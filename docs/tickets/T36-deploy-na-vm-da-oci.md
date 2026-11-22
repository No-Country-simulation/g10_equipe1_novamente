---
id: T36
title: Publique o NovaMente na VM da OCI com HTTPS, backup diário e roteiro de operação
blocked_by: [T35]
touches:
  - .dockerignore
  - compose.yml
  - compose.override.yml
  - compose.deploy.yml
  - backend/Dockerfile
  - backend/scripts/upload_backup.py
  - backend/tests/scripts/test_upload_backup.py
  - scripts/deploy.sh
  - scripts/backup-db.sh
  - .github/workflows/test-docker-compose.yml
  - .github/workflows/deploy-docker-compose.yml
  - deployment.md
  - deployment-docker-compose.md
  - README.md
  - AGENTS.md
  - docs/ARCHITECTURE.md
  - docs/tickets/T36-deploy-na-vm-da-oci.md
executor: [agente, pessoa]
size: 3
---

# T36 - Publique o NovaMente na VM da OCI com HTTPS, backup diário e roteiro de operação

Publique o NovaMente na VM `VM.Standard.A2.Flex` (arm64) que a equipe já tem em execução. Use Docker Compose, HTTPS e um backup diário do banco no OCI Object Storage. A [decisão de custo](../product-specs/escopo-do-mvp.md#restrições) registra a exceção ao Always Free.

A **Parte 1** entrega Compose, scripts, testes e guia em um PR. A **Parte 2** começa depois do merge. Uma pessoa com acesso à OCI e à VM executa o guia e registra o aceite. Chaves SSH, OCIDs, fingerprints, namespace e valores reais do `.env` ficam com a pessoa. Use só exemplos e resultados sem identificadores no repositório, no PR e nas sessões de agente.

## Decisões

| Ponto | Decisão | Motivo |
| --- | --- | --- |
| VM | Use a A2.Flex existente, com a configuração atual. | A equipe já tem a VM. A alternativa Always Free está registrada na especificação. |
| DNS e HTTPS | Use o domínio da equipe ou um subdomínio gratuito do DuckDNS apontado para o IPv4 público da VM. O Traefik pede e renova o certificado do Let's Encrypt pelo desafio HTTP-01. | O DuckDNS só resolve o nome. O desafio usa a porta 80 e dispensa token de DNS no servidor. [DuckDNS](https://www.duckdns.org/why.jsp), [Traefik](https://doc.traefik.io/traefik/v3.7/reference/install-configuration/tls/certificate-resolvers/acme/#httpchallenge). |
| Deploy | Entre por SSH e rode o script. Apague o workflow manual com runner `self-hosted`. | O repositório é público. O script elimina o runner de deploy na VM e os segredos de produção no GitHub. [Orientação do GitHub](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners). |
| Build | Compile a imagem do backend na VM. Mantenha o CI atual em `ubuntu-latest`. | O GitHub oferece `ubuntu-24.04-arm` para repositórios públicos. A compilação nativa na VM já comprova arm64 para este deploy. [Runners do GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners#standard-github-hosted-runners-for-public-repositories). |
| Backend | Use `fastapi run --workers 1` em produção. | O Dockerfile inicia quatro workers hoje. Os limitadores de `backend/app/core/llm.py` guardam o estado e o lock no processo. Um worker compartilha o limite entre os pedidos deste deploy. |
| Object Storage | Use um bucket privado de produção na região da VM, com `OCI_AUTH=instance_principal`. | `backend/app/core/config.py`, `backend/app/core/storage.py` e `compose.yml` já aceitam essa configuração. A identidade da VM dispensa chave de API. |
| Backup | Agende o `pg_dump` com cron. Envie o arquivo ao bucket pelo SDK já instalado na imagem e guarde as sete cópias mais recentes. | Contas, chunks e embeddings precisam do PostgreSQL. O backup cobre o banco. A recuperação de um curso depende também dos objetos ainda presentes no bucket. |

## Parte 1 - agente

### Compose e CI

1. Mova `adminer` inteiro de `compose.yml` para `compose.override.yml`. Mantenha a imagem, a dependência `db`, `ADMINER_DESIGN` e a porta `8080:8080`. Retire os rótulos do Traefik e o bloco `adminer` de `compose.deploy.yml`.
2. Em `compose.deploy.yml`, troque `--certificatesresolvers.le.acme.tlschallenge=true` por `--certificatesresolvers.le.acme.httpchallenge.entrypoint=http`. Mantenha o redirecionamento HTTP para HTTPS, os rótulos `backend-https` com `tls.certresolver=le` e o volume `traefik-certificates`. O Traefik responde ao desafio na porta 80 e serve a aplicação na 443.
3. Em `backend/Dockerfile`, troque `--workers 4` por `--workers 1`. Exclua arquivos `.env*` de qualquer diretório do contexto em `.dockerignore`. O Dockerfile já compila o frontend e o backend o serve na mesma origem.
4. Apague `.github/workflows/deploy-docker-compose.yml`. Em `.github/workflows/test-docker-compose.yml`, mantenha `docker compose up -d --wait backend adminer`. Depois de copiar os arquivos de exemplo, valide com `DOMAIN=example.com` que `docker compose -f compose.yml -f compose.deploy.yml config --services` lista apenas `backend`, `db` e `proxy`. Na checagem do backend, use `curl -fsS` com a rota completa `/api/v1/utils/health-check/` e compare a resposta com `true`. No frontend, exija sucesso HTTP em `/`.

### Scripts novos

Nos dois scripts de shell, use `set -euo pipefail`, entre na raiz do clone a partir do caminho do script e passe `-f compose.yml -f compose.deploy.yml` em todo comando do Compose. Use as variáveis do `.env` pelo Compose.

- **`scripts/deploy.sh`**. Exija um checkout limpo no branch `master`. Faça `git pull --ff-only origin master` e confira que `HEAD` e `FETCH_HEAD` apontam para o mesmo commit. Rode, em ordem, `build backend`, `up -d --wait db`, `run --rm --no-deps backend bash scripts/prestart.sh` e `up -d --wait --remove-orphans`. `prestart.sh` já executa `alembic upgrade head`. Use apenas no projeto Compose dedicado ao NovaMente. Pare no primeiro erro. Ao final, mostre `ps` e o commit publicado.
- **`scripts/backup-db.sh`**. Crie um temporário privado com `mktemp` e remova-o ao sair com `trap`. Grave nele a saída de `exec -T db pg_dump -U postgres -Fc app`. Só depois de o dump terminar com sucesso, passe o arquivo pela entrada padrão de `exec -T backend python scripts/upload_backup.py`.
- **`backend/scripts/upload_backup.py`**. Leia os bytes da entrada padrão e use `get_storage()` de `app.core.storage`. Recuse entrada vazia. Envie a `backups/app-<timestamp-UTC>.dump`, com precisão de microssegundos e data em ordem lexicográfica, e imprima a chave. Só depois de gravar, liste `backups/app-` e apague os `.dump` mais antigos além dos sete mais recentes. Em erro de armazenamento, devolva código diferente de zero e registre só o tipo da falha e a operação, sem incluir o conteúdo ou a configuração. O script entra na imagem pela instrução `COPY ./backend/scripts` que já existe.

### Guia

Reescreva [`deployment-docker-compose.md`](../../deployment-docker-compose.md) como guia prático em português, na ordem da Parte 2. Inclua comandos copiáveis, os campos do `.env`, a atualização, a restauração em um banco separado e os diagnósticos abaixo. Use valores fictícios ou marcados como `<valor>`. Siga o [guia de escrita](../WRITING.md).

| O que falhou | Como conferir e corrigir |
| --- | --- |
| Domínio ou certificado | Confira DNS, portas públicas e os logs de `proxy`. A porta 80 precisa receber o desafio HTTP-01. |
| O serviço não responde fora da VM | Confira as portas publicadas pelo Compose, as regras da interface de rede na OCI e o firewall da VM. |
| Migração ou inicialização | Confira a saída de `prestart.sh` e os logs de `db` e `backend`. O backend recusa `changethis` em produção. Preserve a senha do volume existente. |
| Criação de curso responde HTTP 503 | Rode `verify_storage.py` no contêiner. Confira região, bucket, acesso do contêiner ao IMDSv2 da VM e propagação da policy. |
| Geração falha | Confira a mensagem do conteúdo, os logs de `backend` e a configuração de `GEMINI_API_KEY` e `GEMINI_GENERATION_MODEL` na VM. |
| Backup falha | Confira o log do cron e a chave mais recente no bucket. |

Em [`deployment.md`](../../deployment.md), troque a seção Docker Compose por um link para o guia e preserve a seção de automação do repositório. Ligue o guia no [README](../../README.md) e no [`AGENTS.md`](../../AGENTS.md). Atualize [Implantação](../ARCHITECTURE.md#implantação) e o mapa do código com as mudanças de Compose e scripts. Mantenha como planejadas a publicação na VM, o domínio, a rede e a execução do cron até a Parte 2.

### Aceite da Parte 1

- [ ] Com `DOMAIN=example.com` e o `.env` de teste, o Compose de produção resolve `backend`, `db` e `proxy`. Inspecione o resultado em JSON e confirme que só `proxy` publica portas, 80 e 443, e que usa HTTP-01. Registre os serviços e as portas no PR. Evite imprimir a configuração interpolada.
- [ ] O Compose de desenvolvimento ainda tem `adminer` em `http://localhost:8080`. O CI de Compose passa com esse serviço, a rota de saúde e o frontend. A sobreposição `compose.playwright.yml` continua funcionando no CI Playwright.
- [ ] O comando da imagem tem um worker. O workflow com runner `self-hosted` saiu do repositório. `uv run zizmor .` e os [hooks](README.md#verificações-antes-do-pr) passam.
- [ ] `bash -n scripts/deploy.sh` e `bash -n scripts/backup-db.sh` passam. Em um teste com `pg_dump` simulado que escreve alguns bytes e falha, o script sai com erro e não chama o upload.
- [ ] Em `backend/tests/scripts/test_upload_backup.py` (novo), use `InMemoryStorage` e um instante fixo. Verifique a chave UTC e os bytes gravados, a retenção das sete cópias mais recentes e a preservação de objetos de curso. Verifique que entrada vazia ou falha no envio retorna erro sem apagar cópias. Os testes do backend mantêm a cobertura exigida pelo CI.
- [ ] O guia cobre as ações e as verificações da Parte 2. Mantenha o PR perto de 400 linhas ou menos, contando o diff, e revise os arquivos e logs para evitar valores reais de infraestrutura ou credenciais.

## Parte 2 - pessoa

Use o guia da Parte 1 depois do merge.

1. **VM e rede.** Confirme no console que a VM existente é a `VM.Standard.A2.Flex` e confira `uname -m` por SSH. Verifique os serviços que já usam portas na VM. Na interface de rede da VM, confira o efeito conjunto das security lists, dos NSGs e do firewall local. Libere TCP 80 e 443 para acesso público e limite SSH aos IPs da equipe. Preserve as regras de outros hosts em subnets compartilhadas. Confirme acesso ao DNS, ao Let's Encrypt, ao Gemini, aos registros de imagens e à OCI. [Regras de rede da OCI](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm#if-you-use-both-security-lists-and-network-security-groups).
2. **Bucket e identidade.** Use um bucket privado exclusivo de produção na região da VM, como `novamente-prod`. Crie no domínio de identidade padrão um dynamic group que inclua só a VM pela regra `instance.id = '<ocid-da-vm>'`. Conceda `Allow dynamic-group <grupo> to manage objects in compartment <compartimento> where target.bucket.name = '<bucket>'`. Configure o namespace só na VM. [Identidade da instância](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/callingservicesfrominstances.htm), [permissões do Object Storage](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/objectstoragepolicyreference.htm).
3. **Domínio.** Aponte o registro A para o IPv4 público da VM no domínio da equipe ou no painel do DuckDNS. Confira o resultado de fora da OCI antes do deploy. Só publique um registro AAAA se a VM também receber o tráfego por IPv6.
4. **Docker e código.** Use o Docker Engine e o plugin Compose. Se faltarem, instale seguindo o [guia oficial](https://docs.docker.com/engine/install/) do sistema da VM e habilite o serviço no boot. Se houver um runner de deploy do NovaMente nessa VM, remova o registro no GitHub e desative seu serviço. Use a mesma conta com acesso ao Docker para o deploy e o cron. Clone o `master` por HTTPS em um diretório dedicado e mantenha o caminho nas atualizações para preservar o projeto e seus volumes.
5. **Configuração e deploy.** Crie o `.env` da VM com permissão `600`. Rode `bash scripts/deploy.sh`. Depois, rode `docker compose -f compose.yml -f compose.deploy.yml exec -T backend python scripts/verify_storage.py`. As operações de envio, leitura, listagem e exclusão precisam passar.
6. **Conta e backup.** Crie a conta da demonstração pela tela "Criar conta". Rode `bash scripts/backup-db.sh` e confira a chave no bucket. Habilite o serviço de cron da VM. Agende o script no `crontab` da conta de deploy, com caminho absoluto e saída para um log privado. Escolha e registre o horário no fuso da VM. Confira o primeiro backup criado pelo cron.
7. **Atualização.** Antes de cada atualização, faça um backup, confirme a chave e escolha uma janela sem geração ativa. Rode `bash scripts/deploy.sh` e confira a rota pública de saúde. A migração altera o banco antes de subir o backend novo. Preserve o volume `app-db-data` e a cópia anterior à atualização.
8. **Conclusão.** Preencha a [verificação do aceite](#verificação-do-aceite) e abra o PR de conclusão com os estados comprovados em [Implantação](../ARCHITECTURE.md#implantação). Corrija o guia se algum passo precisou mudar.

### Campos do .env da VM

| Variável | Valor |
| --- | --- |
| `DOMAIN` | Nome DNS, sem protocolo nem porta |
| `PROJECT_NAME` | `NovaMente` |
| `SECRET_KEY` | Valor gerado com `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | Outro valor gerado com `openssl rand -hex 32`, se o volume for novo. Em um volume existente, use a senha atual. |
| `GEMINI_API_KEY` | Chave de um projeto no plano gratuito, sem faturamento ativado |
| `GEMINI_GENERATION_MODEL` | `gemini-3.5-flash-lite`, conforme `.env.example` |
| `OCI_AUTH` | `instance_principal` |
| `OCI_BUCKET` | Nome do bucket privado de produção |
| `OCI_NAMESPACE` | Namespace lido no console da OCI |

O Compose monta `DATABASE_URL` com a senha do banco e o host `db`. O cadastro é aberto. A chave do Gemini é exclusiva do projeto de demonstração para que o uso local tenha sua própria cota.

### Verificação manual

- [ ] Na VM, `uname -m` mostra `aarch64`. O build da imagem passa na VM e `docker image inspect backend:latest --format '{{.Os}}/{{.Architecture}}'` mostra `linux/arm64`. O Compose mostra o backend saudável e `docker compose -f compose.yml -f compose.deploy.yml top backend` mostra um servidor.
- [ ] De fora da VM, `curl -sSI "http://<dominio>/"` retorna 3xx com `Location` no domínio HTTPS. `curl -fsS "https://<dominio>/api/v1/utils/health-check/"` retorna `true` com certificado válido. Com `nc -vz -w 5 <dominio> <porta>`, confirme que 5432, 8000, 8080 e 8090 estão fechadas. Verifique que o SSH funciona de um IP autorizado e que a porta 22 está fechada de uma rede fora da lista. Verifique as duas famílias de IP se publicou IPv6.
- [ ] No navegador, siga o [quiz da LAI](../../development.md#4-crie-leia-e-exclua-um-curso) até o estado "Pronto" e responda a uma pergunta. Veja o documento e o JSON sob `courses/<course_id>/` no console da OCI. Exclua o curso pela tela e confirme que a limpeza em segundo plano esvazia o prefixo.
- [ ] Veja no bucket duas chaves distintas, uma da execução manual e outra do horário agendado. Baixe a cópia agendada, transfira-a por SSH e importe-a em um banco descartável com `createdb -U postgres app_restore` e `pg_restore --exit-on-error -U postgres -d app_restore`. Use `docker compose -f compose.yml -f compose.deploy.yml exec -T db` para os comandos, com o dump na entrada do `pg_restore`. Confirme com `psql -U postgres -d app_restore` que a conta de demonstração está em `"user"`. Use `dropdb -U postgres app_restore` para apagar o banco descartável e remova as cópias locais do dump.
- [ ] Em uma janela combinada pela equipe, reinicie a VM. De fora, confirme que a rota de saúde volta a responder `true` sem rodar o deploy outra vez. Na VM, `stat -c %a .env` mostra `600`.

## Verificação do aceite

A pessoa que publicou registra aqui a data, o commit, o shape e a região, os resultados do build, do HTTPS, do quiz, da exclusão, do cron, da restauração e do reinício. Registre a estimativa de custo mensal da VM com base no uso e no preço aplicável no console. Compartilhe o endereço de demonstração com a equipe e a banca pelo canal escolhido.

## Fora do escopo

Deploy automático, registry de imagens, nova VM, alta disponibilidade e monitoramento externo.
