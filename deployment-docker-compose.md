# Publique a demonstração do NovaMente na OCI

Siga este guia depois do merge da Parte 1 do [T36](docs/tickets/T36-deploy-na-vm-da-oci.md). Use uma conta exclusiva e dados descartáveis. A demonstração serve HTTP na porta 80, com HTTPS e backup fora do escopo do hackathon.

## 1. Confira a VM e a rede

Confirme no console da OCI que a VM existente é `VM.Standard.A2.Flex`. Por SSH, confirme `aarch64` e confira se a porta 80 está livre.

```bash
uname -m
ss -ltn
```

Confira o efeito conjunto das security lists, dos NSGs e do firewall da VM. Abra só TCP 80 para o público e TCP 22 para o IP da pessoa que faz o deploy. Preserve as regras dos outros hosts em subnets compartilhadas. Confirme que a VM alcança o DNS, o Gemini, os registros de imagens e a OCI. [Regras de rede da OCI](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm#if-you-use-both-security-lists-and-network-security-groups).

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

Use uma tag própria para a versão. O builder precisa executar builds para `linux/arm64`. [Docker Buildx](https://docs.docker.com/build/building/multi-platform/).

Na VM, instale o Docker Engine e o plugin Compose se faltarem. Habilite o Docker no boot com `sudo systemctl enable --now docker`. Com a conta do sistema que roda o Compose, entre no OCIR com o token de uma conta que tenha só permissão de leitura no repositório. [Instalação do Docker](https://docs.docker.com/engine/install/), [políticas de acesso ao OCIR](https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm).

```bash
docker login '<regiao>.ocir.io' --username '<namespace>/<usuario-leitor>'
```

Da máquina de build, copie os dois arquivos Compose da mesma versão da imagem. O exemplo usa `~/novamente` na VM. Se o deploy já existe, mantenha o diretório em uso para preservar o volume `app-db-data` e atualize `BACKEND_IMAGE` no `.env` antes de copiar o novo `compose.deploy.yml`.

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

Com `nc -vz -w 5 192.0.2.10 <porta>`, confirme que 80 responde e que 5432, 8000, 8080 e 8090 estão fechadas. Confirme que a porta 22 só responde do IP autorizado. Repita por IPv6 se a VM tiver esse acesso.

## 6. Valide a demonstração

Crie a conta pela tela "Criar conta". O cadastro é aberto. Siga o [quiz da LAI](development.md#4-crie-leia-e-exclua-um-curso) até "Pronto" e responda a uma pergunta. Confira o documento e o JSON sob `courses/<course_id>/` no bucket. Exclua o curso pela tela e confira se o prefixo ficou vazio.

## 7. Atualize

Escolha uma janela sem geração ativa. Atualize `BACKEND_IMAGE` para a versão publicada antes de copiar os arquivos Compose da mesma versão. Repita a sequência de pull, espera do banco, migração e subida do passo 5. Confira a rota pública de saúde. A migração altera o banco antes de subir o backend novo. Preserve o volume `app-db-data`.

## 8. Registre o aceite

Em uma janela combinada com a equipe, reinicie a VM. Confirme de fora que a rota de saúde responde novamente. Na VM, confira que `stat -c %a .env` retorna `600`.

Registre os resultados, o teste de reinício e a estimativa de custo no [aceite do T36](docs/tickets/T36-deploy-na-vm-da-oci.md#verificação-do-aceite). Mantenha [Decisões](docs/ARCHITECTURE.md#decisões) e [Implantação](docs/ARCHITECTURE.md#implantação) coerentes com o que verificou na VM. Atualize este guia se algum passo mudar.

## Diagnostique uma falha

| Falha | Ação |
| --- | --- |
| Site não abre | Confira o IPv4 ou o DNS, a porta 80 em `docker compose -f compose.yml -f compose.deploy.yml ps`, a interface de rede na OCI e o firewall local. |
| Migração ou inicialização | Confira a saída de `prestart.sh` e rode `docker compose -f compose.yml -f compose.deploy.yml logs db backend`. O backend recusa `changethis` no deploy. Preserve a senha do volume existente. |
| Criação de curso retorna HTTP 503 | Rode `verify_storage.py` como no passo 5. Confira região, bucket, acesso do contêiner ao IMDSv2 e propagação da policy. |
| Geração falha | Confira a mensagem do conteúdo e os logs de `backend`. Revise `GEMINI_API_KEY` e `GEMINI_GENERATION_MODEL` na VM. |
