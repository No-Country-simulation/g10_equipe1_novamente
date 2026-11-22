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

Crie um bucket privado exclusivo na região da VM. No domínio de identidade padrão, crie um dynamic group com a regra `instance.id = '<ocid-da-vm>'`. Conceda a policy abaixo e guarde o namespace só na VM. [Identidade da instância](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/callingservicesfrominstances.htm), [permissões do Object Storage](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/objectstoragepolicyreference.htm).

```text
Allow dynamic-group <grupo> to manage objects in compartment <compartimento> where target.bucket.name = '<bucket>'
```

## 3. Escolha o endereço da demonstração

Use o IPv4 público da VM. Se quiser usar um domínio, aponte o registro A para esse IP e confira de fora da OCI com `dig +short A novamente.example.com`, substituindo o domínio de exemplo. Publique AAAA só se a VM receber tráfego por IPv6.

## 4. Prepare o Docker e o clone

Instale o Docker Engine e o plugin Compose se faltarem. Habilite o Docker no boot com `sudo systemctl enable --now docker`. Se houver um runner de deploy do NovaMente, remova o registro no GitHub e desative o serviço na VM. [Instalação do Docker](https://docs.docker.com/engine/install/), [remoção do runner](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/remove-runners).

```bash
git clone --branch master https://github.com/No-Country-simulation/g10_equipe1_novamente.git novamente
cd novamente
```

Use um diretório dedicado e mantenha seu caminho nas atualizações para preservar o projeto Compose e seus volumes.

## 5. Configure o ambiente e publique

Se o `.env` ainda não existir, crie com `install -m 600 /dev/null .env`. Troque os valores entre `< >` pelos valores da equipe. Rode `openssl rand -hex 32` uma vez por segredo novo. Preserve a senha do PostgreSQL se o volume já existir. O Compose monta `DATABASE_URL` com essa senha e o host `db`.

```dotenv
COMPOSE_FILE=compose.yml:compose.deploy.yml
PROJECT_NAME=NovaMente
SECRET_KEY=<segredo-gerado>
POSTGRES_PASSWORD=<senha-do-postgres>
GEMINI_API_KEY=<chave-do-projeto-de-demonstracao>
GEMINI_GENERATION_MODEL=gemini-3.5-flash-lite
OCI_AUTH=instance_principal
OCI_BUCKET=<bucket-privado>
OCI_NAMESPACE=<namespace>
```

Na VM, `COMPOSE_FILE` faz os comandos `docker compose` sem `-f` usarem só os arquivos de deploy.

Use um projeto Gemini exclusivo da demonstração, no plano gratuito e sem faturamento ativado. Com uma conta com acesso ao Docker, rode os comandos abaixo na ordem. Se um comando falhar, pare e corrija a causa.

```bash
bash scripts/deploy.sh
docker compose -f compose.yml -f compose.deploy.yml exec -T backend python scripts/verify_storage.py
```

Confirme que envio, leitura, listagem e exclusão passam. Confira `linux/arm64` com `docker image inspect backend:latest --format '{{.Os}}/{{.Architecture}}'`. Confira um servidor com `docker compose -f compose.yml -f compose.deploy.yml top backend`.

De fora da VM, abra `http://192.0.2.10/` no navegador, substituindo o IP de exemplo. O comando abaixo deve retornar `true`.

```bash
curl -fsS http://192.0.2.10/api/v1/utils/health-check/
```

Com `nc -vz -w 5 192.0.2.10 <porta>`, confirme que 80 responde e que 5432, 8000, 8080 e 8090 estão fechadas. Confirme que a porta 22 só responde do IP autorizado. Repita por IPv6 se a VM tiver esse acesso.

## 6. Valide a demonstração

Crie a conta pela tela "Criar conta". O cadastro é aberto. Siga o [quiz da LAI](development.md#4-crie-leia-e-exclua-um-curso) até "Pronto" e responda a uma pergunta. Confira o documento e o JSON sob `courses/<course_id>/` no bucket. Exclua o curso pela tela e confira se o prefixo ficou vazio.

## 7. Atualize

Escolha uma janela sem geração ativa. Rode `bash scripts/deploy.sh` e confira a rota pública de saúde. A migração altera o banco antes de subir o backend novo. Preserve o volume `app-db-data`.

## 8. Registre o aceite

Em uma janela combinada com a equipe, reinicie a VM. Confirme de fora que a rota de saúde responde novamente. Na VM, confira que `stat -c %a .env` retorna `600`.

Registre os resultados e a estimativa de custo no [aceite do T36](docs/tickets/T36-deploy-na-vm-da-oci.md#verificação-do-aceite). No PR de conclusão, troque `A construir` por `Existe` na linha "Deploy em VM `VM.Standard.A2.Flex` (ARM) com Docker Compose" de [Decisões](docs/ARCHITECTURE.md#decisões). Em [Implantação](docs/ARCHITECTURE.md#implantação), atualize o parágrafo "A Parte 2 do T36 prevê" com o que você fez e verificou na VM.

## Diagnostique uma falha

| Falha | Ação |
| --- | --- |
| Site não abre | Confira o IPv4 ou o DNS, a porta 80 em `docker compose -f compose.yml -f compose.deploy.yml ps`, a interface de rede na OCI e o firewall local. |
| Migração ou inicialização | Confira a saída de `prestart.sh` e rode `docker compose -f compose.yml -f compose.deploy.yml logs db backend`. O backend recusa `changethis` no deploy. Preserve a senha do volume existente. |
| Criação de curso retorna HTTP 503 | Rode `verify_storage.py` como no passo 5. Confira região, bucket, acesso do contêiner ao IMDSv2 e propagação da policy. |
| Geração falha | Confira a mensagem do conteúdo e os logs de `backend`. Revise `GEMINI_API_KEY` e `GEMINI_GENERATION_MODEL` na VM. |
