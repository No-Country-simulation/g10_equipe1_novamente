# Publique a demonstração do NovaMente na OCI

Siga este guia depois do merge da Parte 1 do [T36](docs/tickets/completed/T36-deploy-na-vm-da-oci.md). Use uma conta exclusiva e dados descartáveis. A demonstração serve HTTP na porta 80, com HTTPS e backup fora do escopo do hackathon.

## 1. Confira a VM e a rede

Confirme no console da OCI que a VM existente é `VM.Standard.A2.Flex`. Por SSH, confirme `aarch64` e confira se a porta 80 está livre.

```bash
uname -m
ss -ltn
```

Confira o efeito conjunto das security lists, dos NSGs e do firewall da VM. Para a demonstração por HTTP, permita TCP 80 para o público. Restrinja TCP 22 à origem do SSH. Para acesso direto, use o IP autorizado da pessoa que faz o deploy. Para acesso pelo Cloud Shell, selecione uma rede privada com rota até o IP privado da VM. Confira a saída TCP 22 da sessão e a entrada na VM a partir do NSG da sessão ou do CIDR privado autorizado. Preserve as regras dos outros hosts em subnets compartilhadas. Confirme que a VM alcança o DNS, o Gemini, os registros de imagens e a OCI. [Regras de rede da OCI](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm#if-you-use-both-security-lists-and-network-security-groups), [Cloud Shell Private Networking](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cloudshellintro_topic-Cloud_Shell_Networking.htm).

## 2. Configure o bucket e a identidade

Crie um bucket privado exclusivo na região da VM. No domínio de identidade padrão, crie um dynamic group com a regra `instance.id = '<ocid-da-vm>'`. Conceda a policy abaixo e configure `OCI_NAMESPACE` no `.env` da VM. [Identidade da instância](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/callingservicesfrominstances.htm), [permissões do Object Storage](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/objectstoragepolicyreference.htm).

```text
Allow dynamic-group <grupo> to manage objects in compartment <compartimento> where target.bucket.name = '<bucket>'
```

## 3. Escolha o endereço da demonstração

Use o IPv4 público da VM. Se quiser usar um domínio, aponte o registro A para esse IP e confira de fora da OCI com `dig +short A novamente.example.com`, substituindo o domínio de exemplo. Publique AAAA só se a VM receber tráfego por IPv6.

## 4. Prepare o Docker e a imagem

Crie ou reutilize o repositório privado `novamente/backend` no OCIR. Na máquina de build, abra a raiz do clone na versão que vai publicar. Entre com uma conta que possa publicar nesse repositório e informe o auth token quando o Docker pedir a senha. Se a conta usa um domínio de identidade no login, use `<namespace>/<dominio-de-identidade>/<usuario>`. [Login no OCIR](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm).

```bash
docker login '<regiao>.ocir.io' --username '<namespace>/<usuario-publicador>'
docker buildx build --platform linux/arm64 -f backend/Dockerfile \
  --tag '<regiao>.ocir.io/<namespace>/novamente/backend:<tag>' --push .
```

Use uma tag própria para a versão. Confira a versão com `docker buildx version` e o suporte do builder a `linux/arm64`. [Docker Buildx](https://docs.docker.com/build/building/multi-platform/).

Na VM, confira `docker version` e `docker compose version`. O plugin precisa interpretar `build: !reset null` e aceitar `up --wait --pull never`. Registre as versões verificadas. Instale o Engine e o plugin se faltarem e habilite o Docker no boot com `sudo systemctl enable --now docker`. [Instalação do Docker](https://docs.docker.com/engine/install/).

A equipe configurou e validou anteriormente na VM o pull do OCIR via Instance Principal com `docker-credential-ocir`. O dynamic group da VM precisa de leitura (`read repos`) no repositório. No contexto do usuário que executa o Docker, inclusive sob `sudo`, confira se o helper está no `PATH` e se `credHelpers` associa o host de `BACKEND_IMAGE` a `ocir`. A variável `OCI_AUTH` do backend configura o acesso ao bucket. [Helper do OCIR](https://docs.oracle.com/en/learn/cred-helper/index.html), [políticas de acesso ao OCIR](https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm).

Se usar autenticação por token na VM, entre com uma conta que tenha só permissão de leitura no repositório.

```bash
docker login '<regiao>.ocir.io' --username '<namespace>/<usuario-leitor>'
```

Na primeira publicação, copie os dois arquivos Compose do commit usado no build. O exemplo de acesso direto usa `~/novamente` na VM. Para atualizar a instalação existente em `/opt/novamente`, siga o passo 7.

```bash
ssh '<usuario-ssh>@<ipv4-publico>' 'mkdir -p ~/novamente'
scp compose.yml compose.deploy.yml '<usuario-ssh>@<ipv4-publico>:novamente/'
```

Se houver um runner de deploy do NovaMente na VM, remova o registro no GitHub e desative o serviço na VM. [Remoção do runner](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/remove-runners).

## 5. Configure o ambiente e publique

Na VM, entre no diretório que contém os dois arquivos Compose. Se o `.env` ainda não existir, crie com `install -m 600 /dev/null .env`. Troque os valores entre `< >` pelos valores da equipe. Rode `openssl rand -hex 32` uma vez por segredo novo. Preserve a senha do PostgreSQL se o volume já existir. O Compose monta `DATABASE_URL` com essa senha e o host `db`.

```dotenv
COMPOSE_FILE=compose.yml:compose.deploy.yml
PROJECT_NAME=NovaMente
BACKEND_IMAGE=<regiao>.ocir.io/<namespace>/novamente/backend:<tag>
SECRET_KEY=<segredo-gerado>
POSTGRES_PASSWORD=<senha-do-postgres>
GEMINI_API_KEY=<chave-do-projeto-de-demonstracao>
GEMINI_GENERATION_MODEL=gemini-3.5-flash-lite
OCI_AUTH=instance_principal
OCI_BUCKET=<bucket-privado>
OCI_NAMESPACE=<namespace>
```

Guarde esse `.env` somente na VM, com permissão `600`. `COMPOSE_FILE` seleciona os arquivos de deploy. `BACKEND_IMAGE` recebe o caminho completo com a tag publicada no passo 4.

Use um projeto Gemini exclusivo da demonstração, no plano gratuito e sem faturamento ativado. Com uma conta com acesso ao Docker, rode os comandos abaixo na ordem. Se um comando falhar, pare e corrija a causa.

```bash
docker compose pull backend
docker compose up -d --wait db
docker compose run --rm --no-deps backend bash scripts/prestart.sh
docker compose up -d --wait --remove-orphans
docker compose ps
docker compose exec -T backend python scripts/verify_storage.py
```

Confirme que envio, leitura, listagem e exclusão passam. Confira que a imagem usada pelo contêiner é `linux/arm64` com `docker image inspect "$(docker compose images -q backend)" --format '{{.Os}}/{{.Architecture}}'`. Confira um servidor com `docker compose top backend`.

De fora da VM, abra `http://192.0.2.10/` no navegador, substituindo o IP de exemplo. O comando abaixo deve retornar `true`.

```bash
curl -fsS http://192.0.2.10/api/v1/utils/health-check/
```

Com `nc -vz -w 5 192.0.2.10 <porta>`, confirme que 80 responde e que 5432, 8000, 8080 e 8090 estão fechadas. Confirme que a porta 22 só responde a partir da origem autorizada no passo 1. Repita por IPv6 se a VM tiver esse acesso.

## 6. Valide a demonstração

Crie a conta pela tela "Criar conta". O cadastro é aberto. Siga o [quiz da LAI](development.md#4-crie-leia-e-exclua-um-curso) até "Pronto" e responda a uma pergunta. Confira o documento e o JSON sob `courses/<course_id>/` no bucket. Exclua o curso pela tela e confira se o prefixo ficou vazio.

## 7. Atualize

Escolha uma janela sem geração ativa. Para futuras publicações, registre o commit usado no build, a tag e o digest retornado pelo OCIR. Preserve o registro da versão anterior. No `.env` de `/opt/novamente`, atualize `BACKEND_IMAGE=<registry>/<namespace>/novamente/backend:<tag>`.

O pull baixa a imagem. A entrega dos YAMLs é separada. Compare os dois arquivos instalados com os do commit do build. Se forem iguais, reutilize o par. Se algum mudou, envie os dois arquivos da raiz do clone Windows ao Cloud Shell. Na sessão com rede privada, use a mesma chave do SSH para copiá-los à pasta pessoal de `opc`.

```bash
scp -i '<caminho-da-chave>' compose.yml compose.deploy.yml 'opc@<ip-privado>:'
```

Na VM, instale o par com backup numerado dos YAMLs existentes. Preserve o `.env` da VM.

```bash
sudo cp --backup=numbered ~/compose.yml ~/compose.deploy.yml /opt/novamente/
```

Entre no diretório do projeto. Carregue a base antes do arquivo de deploy. Confira se as imagens resolvidas são a tag pretendida do backend e a imagem esperada do PostgreSQL. Confirme que o projeto reconhece o backend existente e o banco saudável. Se a imagem nova ainda não estiver disponível na VM, baixe-a com `pull backend` usando os mesmos arquivos e opções.

```bash
cd /opt/novamente
sudo docker compose --env-file .env -f compose.yml -f compose.deploy.yml config --images
sudo docker compose --env-file .env -f compose.yml -f compose.deploy.yml ps db backend
```

Execute a migração com a imagem nova. Prossiga apenas se o comando terminar com sucesso.

```bash
sudo docker compose --env-file .env -f compose.yml -f compose.deploy.yml run --rm --no-deps backend bash scripts/prestart.sh
```

Com o banco saudável e a imagem já baixada, recrie apenas o backend.

```bash
sudo docker compose --env-file .env -f compose.yml -f compose.deploy.yml up -d --no-deps --pull never --wait backend
```

Confira a tag em execução, o estado `healthy` dos dois serviços e a continuidade do banco. A rota de saúde local deve retornar `true`.

```bash
sudo docker compose --env-file .env -f compose.yml -f compose.deploy.yml ps db backend
curl -fsS http://localhost/api/v1/utils/health-check/
```

Na atualização de `0.1.1-arm64` para `0.1.2-arm64`, a equipe observou a nova tag saudável, o banco `pgvector/pgvector:0.8.7-pg18` saudável com o mesmo tempo de atividade e a resposta local `true`. A revisão exata dos YAMLs e o teste funcional pelo endereço público continuam pendentes. O Compose publica HTTP em `80:8000`. Para registrar HTTPS público, confirme o ponto de terminação TLS, o certificado e o comportamento da porta 80 no endereço externo.

**Rollback.** O script executa `alembic upgrade head` antes da troca do backend. A compatibilidade de `0.1.1-arm64` com o esquema após essa atualização continua pendente. Antes de voltar, confira a revisão aplicada e as migrações entre as versões. Após confirmar a compatibilidade do esquema, mantenha o par Compose atual se ele também for compatível com a imagem anterior. Nesse caso, aponte `BACKEND_IMAGE` para a referência completa dessa imagem. Se precisar restaurar YAMLs antigos, confira quais variáveis eles exigem. Um `compose.deploy.yml` legado pode exigir `BACKEND_IMAGE_TAG`. Em ambos os casos, rode `config --images` com o `.env` da VM e o par escolhido, na ordem `compose.yml` e `compose.deploy.yml`. Confirme que a referência resolvida é a da imagem anterior, confira o digest registrado quando disponível e recrie apenas o backend. Valide a saúde e a leitura de um curso. Se a compatibilidade estiver em aberto ou houver quebra, avalie uma correção na versão atual ou a restauração de um backup de banco validado, caso exista. A cópia numerada guarda somente os YAMLs.

## 8. Registre o aceite

Em uma janela combinada com a equipe, reinicie a VM. Confirme de fora que a rota de saúde responde novamente. Na VM, confira que `stat -c %a .env` retorna `600`.

Registre os resultados, o teste de reinício e a estimativa de custo no [aceite do T36](docs/tickets/completed/T36-deploy-na-vm-da-oci.md#verificação-do-aceite). Mantenha [Decisões](docs/ARCHITECTURE.md#decisões) e [Implantação](docs/ARCHITECTURE.md#implantação) coerentes com o que verificou na VM. Atualize este guia se algum passo mudar.

## Diagnostique uma falha

| Falha | Ação |
| --- | --- |
| Compose exige `BACKEND_IMAGE_TAG` mesmo após o pull | Na atualização para `0.1.2-arm64`, uma cópia antiga de `compose.deploy.yml` ainda exigia essa variável. Confira o diretório e a ordem dos YAMLs, entregue o par correspondente à imagem e repita `config --images`. Mantenha a referência completa em `BACKEND_IMAGE` no `.env`. |
| Site não abre | Confira o IPv4 ou o DNS, a porta 80 em `docker compose -f compose.yml -f compose.deploy.yml ps`, a interface de rede na OCI e o firewall local. |
| Migração ou inicialização | Confira a saída de `prestart.sh` e rode `docker compose -f compose.yml -f compose.deploy.yml logs db backend`. O backend recusa `changethis` no deploy. Preserve a senha do volume existente. |
| Criação de curso retorna HTTP 503 | Rode `verify_storage.py` como no passo 5. Confira região, bucket, acesso do contêiner ao IMDSv2 e propagação da policy. |
| Geração falha | Confira a mensagem do conteúdo e os logs de `backend`. Revise `GEMINI_API_KEY` e `GEMINI_GENERATION_MODEL` na VM. |
