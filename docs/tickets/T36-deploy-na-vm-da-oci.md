---
id: T36
title: Publique a demonstração do NovaMente na VM da OCI por HTTP
blocked_by: [T35]
touches:
  - .dockerignore
  - compose.yml
  - compose.override.yml
  - compose.deploy.yml
  - backend/Dockerfile
  - scripts/deploy.sh
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

# T36 - Publique a demonstração do NovaMente na VM da OCI por HTTP

Publique o NovaMente na VM `VM.Standard.A2.Flex` (arm64) que a equipe já tem em execução. Use Docker Compose e sirva a demonstração por HTTP na porta 80. A [decisão de custo](../product-specs/escopo-do-mvp.md#restrições) registra a exceção ao Always Free.

A **Parte 1** entrega Compose, script e guia em um PR. Depois do merge, uma pessoa com acesso à OCI e à VM executa a **Parte 2** e registra o aceite. Chaves SSH, OCIDs, fingerprints, namespace e valores reais do `.env` ficam com essa pessoa. Use só exemplos e resultados sem identificadores no repositório, no PR e nas sessões de agente.

## Decisões

| Ponto | Decisão | Motivo |
| --- | --- | --- |
| VM | Use a A2.Flex existente. | A equipe já tem a VM. A alternativa Always Free está registrada na especificação. |
| HTTP | Publique a porta 80 da VM no backend. Use o IPv4 público ou um domínio opcional. | O backend serve o frontend e a API na mesma origem. O acesso por IP dispensa DNS. |
| HTTPS e backup | Deixe fora do escopo. Use credenciais exclusivas da demonstração e dados descartáveis. | A entrega é uma demonstração de hackathon por HTTP. A equipe aceita tráfego sem criptografia e a perda do banco da demonstração. |
| Deploy | Entre por SSH e rode o script. Apague o workflow manual com runner `self-hosted`. | O repositório é público. O script elimina o runner de deploy na VM e os segredos de deploy no GitHub. [Orientação do GitHub](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners). |
| Build | Compile a imagem do backend na VM. Mantenha o CI em `ubuntu-latest`. | O build nativo valida arm64 na VM existente. |
| Backend | Use `fastapi run --workers 1` na VM. | Os limitadores em `backend/app/core/llm.py` compartilham estado e lock no mesmo processo. |
| Object Storage | Use um bucket privado da demonstração na região da VM, com `OCI_AUTH=instance_principal`. | A identidade da VM dispensa uma chave de API da OCI. |

## Parte 1 - agente

### Compose e CI

1. Mova `adminer` para `compose.override.yml`. Mantenha imagem, dependência `db`, `ADMINER_DESIGN` e porta `8080:8080`. Retire os rótulos de roteamento do Adminer.
2. Mantenha o Traefik e os rótulos do backend só em desenvolvimento. O Compose de deploy deve ter `backend` e `db`. Publique `80:8000` no backend e preserve o volume do PostgreSQL. Confira que o acesso por IP funciona e que o frontend e a API funcionam na mesma origem sobre HTTP.
3. Troque `--workers 4` por `--workers 1` em `backend/Dockerfile`. Exclua `.env*` em qualquer diretório do contexto de build.
4. Apague `.github/workflows/deploy-docker-compose.yml`. No CI de Compose, valide com `docker compose -f compose.yml -f compose.deploy.yml config --services` que o deploy tem só `backend` e `db`. Mantenha `docker compose up -d --wait backend adminer`. Use `curl -fsS` na rota completa `/api/v1/utils/health-check/` e compare o corpo com `true`. Exija sucesso HTTP em `/`.

### Script de deploy

Em `scripts/deploy.sh`, use `set -euo pipefail`, entre na raiz do clone a partir do caminho do script e use `-f compose.yml -f compose.deploy.yml` em todo comando Compose. O Compose lê o `.env`.

Exija um checkout limpo no branch `master`. Rode `git pull --ff-only origin master` e confira que `HEAD` e `FETCH_HEAD` coincidem. Rode, em ordem, `build backend`, `up -d --wait db`, `run --rm --no-deps backend bash scripts/prestart.sh` e `up -d --wait --remove-orphans`. O `prestart.sh` executa `alembic upgrade head`. Pare no primeiro erro. Mostre `ps` e o commit publicado. Use o script só no projeto Compose dedicado ao NovaMente.

### Guia

Reescreva [o guia de deploy](../../deployment-docker-compose.md) em português, na ordem da Parte 2. Inclua comandos, campos do `.env`, atualização e diagnóstico de rede, migração, acesso ao armazenamento e geração. Use valores fictícios ou marcados como `<valor>`. Siga o [guia de escrita](../WRITING.md).

Em [`deployment.md`](../../deployment.md), linke o guia e preserve a seção de automação do repositório. Adicione o link ao [README](../../README.md) e ao [`AGENTS.md`](../../AGENTS.md). Atualize [Implantação](../ARCHITECTURE.md#implantação) e o mapa do código. Mantenha a publicação e a verificação na VM como planejadas até a Parte 2.

### Aceite da Parte 1

- [ ] Com um `.env` de teste e sem `DOMAIN`, o Compose de deploy resolve `backend` e `db`. Confira no JSON que só o backend publica porta, TCP 80. Registre serviços e porta no PR sem imprimir a configuração interpolada.
- [ ] O frontend e a rota de saúde respondem por HTTP com um IP no endereço. Confira autenticação, CORS e a URL da API no código.
- [ ] O Compose de desenvolvimento mantém Adminer em `http://localhost:8080`. O CI de Compose e o CI Playwright passam.
- [ ] A imagem tem um worker. O workflow com runner `self-hosted` saiu. `bash -n scripts/deploy.sh`, `uv run zizmor .` e os [hooks](README.md#verificações-antes-do-pr) passam.
- [ ] O guia cobre a Parte 2. Mantenha o diff perto de 400 linhas e revise arquivos e logs para evitar valores reais de infraestrutura ou credenciais.

## Parte 2 - pessoa

1. **VM e rede.** Confirme o shape `VM.Standard.A2.Flex` no console e `aarch64` com `uname -m` por SSH. Confira serviços que já usam portas. Verifique o efeito conjunto das security lists, dos NSGs e do firewall. Deixe abertas só TCP 80 para o público e TCP 22 para o IP da pessoa que faz o deploy. Preserve as regras de outros hosts em subnets compartilhadas. Confirme que a VM alcança o DNS, o Gemini, os registros de imagens e a OCI. [Regras de rede da OCI](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm#if-you-use-both-security-lists-and-network-security-groups).
2. **Bucket e identidade.** Use um bucket privado exclusivo na região da VM. No domínio de identidade padrão, crie um dynamic group com a regra `instance.id = '<ocid-da-vm>'`. Conceda `Allow dynamic-group <grupo> to manage objects in compartment <compartimento> where target.bucket.name = '<bucket>'`. Configure o namespace só na VM. [Identidade da instância](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/callingservicesfrominstances.htm), [permissões do Object Storage](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/objectstoragepolicyreference.htm).
3. **Endereço.** Use o IPv4 público. Se usar domínio, aponte o registro A para esse IPv4 e confirme a resolução de fora da OCI. Publique AAAA só se a VM também receber tráfego por IPv6.
4. **Docker e código.** Use o Docker Engine e o plugin Compose. Habilite o Docker no boot. Se houver um runner de deploy do NovaMente nessa VM, remova o registro no GitHub e desative o serviço. Clone o `master` por HTTPS em um diretório dedicado e mantenha o caminho nas atualizações para preservar o projeto e seus volumes. [Instalação do Docker](https://docs.docker.com/engine/install/).
5. **Configuração e deploy.** Crie o `.env` com permissão `600`. Rode `bash scripts/deploy.sh` e `docker compose -f compose.yml -f compose.deploy.yml exec -T backend python scripts/verify_storage.py`. Confira o envio, a leitura, a listagem e a exclusão.
6. **Demonstração.** Crie uma conta exclusiva pela tela "Criar conta". Acesse pelo IPv4 público, rode o quiz da LAI e verifique a leitura e a exclusão do curso.
7. **Atualização.** Escolha uma janela sem geração ativa. Rode `bash scripts/deploy.sh` e confira a rota pública de saúde. A migração altera o banco antes de subir o backend novo. Preserve o volume `app-db-data`.
8. **Conclusão.** Execute a verificação manual, registre o aceite e abra o PR de conclusão com os estados comprovados em [Implantação](../ARCHITECTURE.md#implantação). Corrija o guia se algum passo mudou.

### Campos do .env da VM

| Variável | Valor |
| --- | --- |
| `PROJECT_NAME` | `NovaMente` |
| `SECRET_KEY` | Valor gerado com `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | Outro valor gerado com `openssl rand -hex 32` para volume novo. Preserve a senha de um volume existente. |
| `GEMINI_API_KEY` | Chave exclusiva da demonstração, de um projeto no plano gratuito sem faturamento ativado |
| `GEMINI_GENERATION_MODEL` | `gemini-3.5-flash-lite`, conforme `.env.example` |
| `OCI_AUTH` | `instance_principal` |
| `OCI_BUCKET` | Nome do bucket privado da demonstração |
| `OCI_NAMESPACE` | Namespace lido no console da OCI |

O Compose monta `DATABASE_URL` com a senha do banco e o host `db`. O cadastro é aberto.

### Verificação manual

- [ ] Na VM, `uname -m` mostra `aarch64`. O build passa e `docker image inspect backend:latest --format '{{.Os}}/{{.Architecture}}'` mostra `linux/arm64`. O Compose mostra o backend saudável e `docker compose -f compose.yml -f compose.deploy.yml top backend` mostra um servidor.
- [ ] De fora da VM, abra `http://<ipv4-publico>/` e confira que `curl -fsS "http://<ipv4-publico>/api/v1/utils/health-check/"` retorna `true`. Confira que 80 responde e que 5432, 8000, 8080 e 8090 estão fechadas. Verifique a porta 22 de um IP autorizado e de outro fora da lista. Confira IPv6 se houver.
- [ ] No navegador, siga o [quiz da LAI](../../development.md#4-crie-leia-e-exclua-um-curso) até "Pronto" e responda a uma pergunta. Veja o documento e o JSON sob `courses/<course_id>/` no console da OCI. Exclua o curso pela tela e confira que a limpeza esvazia o prefixo.
- [ ] Em uma janela combinada pela equipe, reinicie a VM. Confirme de fora que a rota de saúde voltou a responder `true`. Na VM, `stat -c %a .env` mostra `600`.

## Verificação do aceite

Registre a data, o commit, o shape, a região e os resultados do build, do acesso HTTP, do quiz, da exclusão e do reinício. Registre o custo mensal estimado da VM com base no uso e no preço aplicável no console. Compartilhe o endereço da demonstração com a equipe e a banca pelo canal escolhido.

## Fora do escopo

HTTPS, backup, deploy automático, registry de imagens, nova VM, alta disponibilidade e monitoramento externo.
