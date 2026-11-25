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
  - .github/workflows/test-docker-compose.yml
  - .github/workflows/deploy-docker-compose.yml
  - deployment.md
  - deployment-docker-compose.md
  - README.md
  - AGENTS.md
  - docs/ARCHITECTURE.md
  - docs/tickets/README.md
  - docs/tickets/completed/T36-deploy-na-vm-da-oci.md
executor: [agente, pessoa]
size: 3
---

# T36 - Publique a demonstração do NovaMente na VM da OCI por HTTP

Publique o NovaMente na VM `VM.Standard.A2.Flex` (arm64) que a equipe já tem em execução. Use Docker Compose e sirva a demonstração por HTTP na porta 80. A [decisão de custo](../../product-specs/escopo-do-mvp.md#restrições) registra a exceção ao Always Free.

A **Parte 1** entrega Compose, CI e guia em um PR. Depois do merge, uma pessoa com acesso à OCI e à VM executa a **Parte 2** e registra o aceite. Chaves SSH, OCIDs, fingerprints, namespace e valores reais do `.env` ficam com essa pessoa. Use só exemplos e resultados sem identificadores no repositório, no PR e nas sessões de agente.

## Decisões

| Ponto | Decisão | Motivo |
| --- | --- | --- |
| VM | Use a A2.Flex existente. | A equipe já tem a VM. A alternativa Always Free está registrada na especificação. |
| HTTP | Publique a porta 80 da VM no backend. Use o IPv4 público ou um domínio opcional. | O backend serve o frontend e a API na mesma origem. O acesso por IP dispensa DNS. |
| HTTPS e backup | Deixe fora do escopo. Use credenciais exclusivas da demonstração e dados descartáveis. | A entrega é uma demonstração de hackathon por HTTP. A equipe aceita tráfego sem criptografia e a perda do banco da demonstração. |
| Deploy | Entre por SSH e use Docker Compose com uma imagem ARM64 versionada no OCIR. Apague o workflow manual com runner `self-hosted`. | A VM não clona o repositório nem compila a imagem. O repositório é público e não deve guardar segredos de deploy. [Orientação do GitHub](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners). |
| Imagem | Use a imagem versionada `<regiao>.ocir.io/<namespace>/novamente/backend:<tag>` e configure `BACKEND_IMAGE`. | O Compose de deploy consome a imagem do OCIR; a VM ARM64 não faz o build. |
| Backend | Use `fastapi run --workers 1` na VM. | Os limitadores em `backend/app/core/llm.py` compartilham estado e lock no mesmo processo. |
| Object Storage | Use um bucket privado da demonstração na região da VM, com `OCI_AUTH=instance_principal`. | A identidade da VM dispensa uma chave de API da OCI. |

## Parte 1 - agente

### Compose e CI

1. Mova `adminer` para `compose.override.yml`. Mantenha imagem, dependência `db`, `ADMINER_DESIGN` e porta `8080:8080`. Retire os rótulos de roteamento do Adminer.
2. Mantenha o Traefik e os rótulos do backend só em desenvolvimento. O Compose de deploy deve ter `backend` e `db`. Publique `80:8000` no backend e preserve o volume do PostgreSQL. Confira que o acesso por IP funciona e que o frontend e a API funcionam na mesma origem sobre HTTP.
3. Troque `--workers 4` por `--workers 1` em `backend/Dockerfile`. Exclua `.env*` em qualquer diretório do contexto de build.
4. Apague `.github/workflows/deploy-docker-compose.yml`. No CI de Compose, valide com `docker compose -f compose.yml -f compose.deploy.yml config --services` que o deploy tem só `backend` e `db`. Mantenha `docker compose up -d --wait backend adminer`. Use `curl -fsS` na rota completa `/api/v1/utils/health-check/` e compare o corpo com `true`. Exija sucesso HTTP em `/`.

### Fluxo de deploy na VM

O deploy usa `compose.yml` e `compose.deploy.yml` no diretório dedicado da VM. Mantenha o mesmo caminho para preservar o nome do projeto Compose e o volume `app-db-data`. A VM baixa do OCIR a imagem ARM64 indicada em `BACKEND_IMAGE`. O guia mostra como publicar a imagem, copiar os arquivos Compose e autenticar o pull com acesso de leitura.

Com `COMPOSE_FILE=compose.yml:compose.deploy.yml` no `.env`, rode, em ordem, `docker compose pull backend`, `docker compose up -d --wait db`, `docker compose run --rm --no-deps backend bash scripts/prestart.sh` e `docker compose up -d --wait --remove-orphans`. O `prestart.sh` executa `alembic upgrade head`. Confira `docker compose ps` e a rota pública de saúde.

### Guia

Reescreva [o guia de deploy](../../../deployment-docker-compose.md) em português, na ordem da Parte 2. Inclua comandos, campos do `.env`, atualização e diagnóstico de rede, migração, acesso ao armazenamento e geração. Use valores fictícios ou marcados como `<valor>`. Siga o [guia de escrita](../../WRITING.md).

Em [`deployment.md`](../../../deployment.md), linke o guia e preserve a seção de automação do repositório. Adicione o link ao [README](../../../README.md) e ao [`AGENTS.md`](../../../AGENTS.md). Atualize [Implantação](../../ARCHITECTURE.md#implantação) e o mapa do código conforme o fluxo efetivamente implantado. A arquitetura registra o deploy e as verificações da demonstração como validados; o reinício da VM continua pendente.

### Aceite da Parte 1

- [x] Com um `.env` de teste e sem `DOMAIN`, o Compose de deploy resolve `backend` e `db`. Confira no JSON que só o backend publica porta, TCP 80. Registre serviços e porta no PR sem imprimir a configuração interpolada.
- [x] O frontend e a rota de saúde respondem por HTTP com um IP no endereço. Confira autenticação, CORS e a URL da API no código.
- [x] O Compose de desenvolvimento mantém Adminer em `http://localhost:8080`. O CI de Compose e o CI Playwright passam.
- [x] A imagem tem um worker. O workflow com runner `self-hosted` saiu. `uv run zizmor .` e os [hooks](../README.md#verificações-antes-do-pr) passam.
- [x] O guia cobre a Parte 2. Mantenha o diff perto de 400 linhas e revise arquivos e logs para evitar valores reais de infraestrutura ou credenciais.

## Parte 2 - pessoa

1. **VM e rede.** Confirme o shape `VM.Standard.A2.Flex` no console e `aarch64` com `uname -m` por SSH. Confira serviços que já usam portas. Verifique o efeito conjunto das security lists, dos NSGs e do firewall. Deixe abertas só TCP 80 para o público e TCP 22 para o IP da pessoa que faz o deploy. Preserve as regras de outros hosts em subnets compartilhadas. Confirme que a VM alcança o DNS, o Gemini, os registros de imagens e a OCI. [Regras de rede da OCI](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm#if-you-use-both-security-lists-and-network-security-groups).
2. **Bucket e identidade.** Use um bucket privado exclusivo na região da VM. No domínio de identidade padrão, crie um dynamic group com a regra `instance.id = '<ocid-da-vm>'`. Conceda `Allow dynamic-group <grupo> to manage objects in compartment <compartimento> where target.bucket.name = '<bucket>'`. Configure `OCI_NAMESPACE` no `.env` da VM. [Identidade da instância](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/callingservicesfrominstances.htm), [permissões do Object Storage](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/objectstoragepolicyreference.htm).
3. **Endereço.** Use o IPv4 público. Se usar domínio, aponte o registro A para esse IPv4 e confirme a resolução de fora da OCI. Publique AAAA só se a VM também receber tráfego por IPv6.
4. **Docker e imagem.** Na máquina de build, entre no OCIR com acesso de publicação, compile e envie a imagem ARM64. Na VM, instale o Docker Engine e o plugin Compose e habilite o Docker no boot. Entre no OCIR com um token de uma conta com acesso só de leitura ao repositório. Copie os dois arquivos Compose para um diretório dedicado e preserve o caminho nas atualizações. Se houver um runner de deploy do NovaMente na VM, remova o registro no GitHub e desative o serviço. [Guia de deploy](../../../deployment-docker-compose.md#4-prepare-o-docker-e-a-imagem).
5. **Configuração e deploy.** Crie o `.env` privado com permissão `600`, incluindo `BACKEND_IMAGE` com o caminho completo e a tag de uma imagem ARM64 publicada no OCIR. Rode os comandos de pull, migração e subida descritos em "Fluxo de deploy na VM". Depois rode `docker compose exec -T backend python scripts/verify_storage.py` e confira envio, leitura, listagem e exclusão.
6. **Demonstração.** Crie uma conta exclusiva pela tela "Criar conta". Acesse pelo IPv4 público, rode o quiz da LAI e verifique a leitura e a exclusão do curso.
7. **Atualização.** Escolha uma janela sem geração ativa. Atualize `BACKEND_IMAGE` para a imagem publicada antes de copiar os arquivos Compose e repita o fluxo de pull, migração e subida. Confira a rota pública de saúde. A migração altera o banco antes de subir o backend novo. Preserve o volume `app-db-data`.
8. **Conclusão.** Execute a verificação manual e registre o aceite, incluindo o teste de reinício que ainda está pendente. Mantenha [Decisões](../../ARCHITECTURE.md#decisões) e [Implantação](../../ARCHITECTURE.md#implantação) coerentes com os resultados observados na VM e atualize este guia se algum passo mudar.

### Campos do .env da VM

| Variável | Valor |
| --- | --- |
| `COMPOSE_FILE` | `compose.yml:compose.deploy.yml` |
| `PROJECT_NAME` | `NovaMente` |
| `BACKEND_IMAGE` | Caminho e tag da imagem ARM64 publicada, no formato `<regiao>.ocir.io/<namespace>/novamente/backend:<tag>` |
| `SECRET_KEY` | Valor gerado com `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | Outro valor gerado com `openssl rand -hex 32` para volume novo. Preserve a senha de um volume existente. |
| `GEMINI_API_KEY` | Chave exclusiva da demonstração, de um projeto no plano gratuito sem faturamento ativado |
| `GEMINI_GENERATION_MODEL` | `gemini-3.5-flash-lite`, conforme `.env.example` |
| `OCI_AUTH` | `instance_principal` |
| `OCI_BUCKET` | Nome do bucket privado da demonstração |
| `OCI_NAMESPACE` | Namespace lido no console da OCI |

O Compose monta `DATABASE_URL` com a senha do banco e o host `db`. O cadastro é aberto.

### Verificação manual

- [ ] Na VM, `uname -m` mostra `aarch64`. `docker image inspect "$(docker compose images -q backend)" --format '{{.Os}}/{{.Architecture}}'` mostra `linux/arm64`. O Compose mostra o backend saudável e `docker compose top backend` mostra um servidor.
- [ ] De fora da VM, abra `http://<ipv4-publico>/` e confira que `curl -fsS "http://<ipv4-publico>/api/v1/utils/health-check/"` retorna `true`. Confira que 80 responde e que 5432, 8000, 8080 e 8090 estão fechadas. Verifique a porta 22 de um IP autorizado e de outro fora da lista. Confira IPv6 se houver.
- [ ] No navegador, siga o [quiz da LAI](../../../development.md#4-crie-leia-e-exclua-um-curso) até "Pronto" e responda a uma pergunta. Veja o documento e o JSON sob `courses/<course_id>/` no console da OCI. Exclua o curso pela tela e confira que a limpeza esvazia o prefixo.
- [ ] Em uma janela combinada pela equipe, reinicie a VM. Confirme de fora que a rota de saúde voltou a responder `true`. Na VM, `stat -c %a .env` mostra `600`.

## Verificação do aceite

- Parte 1: PR [#55](https://github.com/No-Country-simulation/g10_equipe1_novamente/pull/55), integrado por squash no commit `2a80789`. Os checks do CI passaram.
- Revisões automáticas: três achados na primeira rodada e cinco na segunda, todos corrigidos antes do merge. O caminho da imagem saiu do repositório e passou para `BACKEND_IMAGE` no `.env` da VM. O guia ganhou a publicação da imagem ARM64, o login no OCIR e a cópia dos arquivos Compose. `scripts/deploy.sh` saiu.
- Teste local da Parte 1: em um projeto Compose separado, com `.env` fictício, a imagem ARM64 subiu, a migração rodou e a rota de saúde, `/`, o cadastro e o login responderam por HTTP.
- Parte 2: em 25/11/2026, a equipe informou que a aplicação está publicada na VM. Os resultados da verificação manual, o teste de reinício e a estimativa de custo não foram registrados neste ticket. As caixas da verificação manual ficam abertas até esse registro.

## Fora do escopo

HTTPS, backup, deploy automático, automação de publicação da imagem no OCIR, nova VM, alta disponibilidade e monitoramento externo. O deploy já consome uma imagem versionada do OCIR.
