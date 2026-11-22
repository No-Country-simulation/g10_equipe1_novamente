# Rode o NovaMente localmente

## 1. Instale as dependências

Você precisa de Python 3.14, conforme [`.python-version`](.python-version), Bun 1.3.12, conforme o [workflow Playwright](.github/workflows/playwright.yml), `uv` e Docker com o plugin Compose. Confira com `python3 --version`, `bun --version`, `uv --version` e `docker compose version`. O `uv` pode instalar o Python 3.14 automaticamente.

```bash
git clone https://github.com/No-Country-simulation/g10_equipe1_novamente.git
```

```bash
cd g10_equipe1_novamente
```

```bash
(cd backend && uv sync --locked)
```

```bash
bun ci
```

## 2. Configure o ambiente

Na raiz do clone, crie os arquivos usados pelo backend e pelo frontend.

```bash
cp .env.example .env
```

```bash
cp frontend/.env.example frontend/.env
```

| Variáveis | Configure assim |
| --- | --- |
| `FASTAPI_ENV`, `PROJECT_NAME` | Mantenha `development`. Use `NovaMente` como nome da API. |
| `SECRET_KEY`, `POSTGRES_PASSWORD`, `DATABASE_URL` | Gere uma chave local para assinar os tokens com `openssl rand -hex 32`. Escolha a senha do banco antes do primeiro start do Compose. A URL de exemplo usa essa senha. Guarde esses valores no `.env` local. |
| `VITE_API_URL`, `FRONTEND_HOST` | O frontend aponta para `http://localhost:8000`. Se mudar a origem padrão do frontend, `http://localhost:5173`, ajuste `FRONTEND_HOST` no `.env` da raiz. |
| `GEMINI_API_KEY`, `GEMINI_GENERATION_MODEL` | Para a geração real, informe a chave e retire o comentário da linha do modelo de texto. O modelo de embeddings já tem valor padrão. Ajuste as três variáveis de limite se a cota da sua conta exigir. [Modelos de IA](docs/ARCHITECTURE.md#modelos-de-ia). |
| `OCI_BUCKET`, `OCI_NAMESPACE`, `OCI_AUTH`, `OCI_CONFIG_FILE`, `OCI_CONFIG_PROFILE` | Para a geração real, informe o nome do bucket privado de desenvolvimento e o namespace. Use `api_key` e aponte para o arquivo de configuração e o perfil da OCI. O padrão é `~/.oci/config`, perfil `DEFAULT`. Guarde a API signing key fora do repositório. |

Use apenas documentos públicos ou fictícios com o Gemini. Sem as credenciais, o backend padrão sobe e você pode criar uma conta. A geração real precisa do Gemini e do OCI.

O [Compose](compose.yml) repassa as variáveis `GEMINI_*` e `OCI_*` ao backend. No desenvolvimento, o [`compose.override.yml`](compose.override.yml) monta `~/.oci` do host em `/root/.oci` no contêiner, em modo somente leitura. Com `OCI_AUTH=api_key`, guarde a chave em `~/.oci/` e use `key_file=~/.oci/minha-chave.pem` em `~/.oci/config`. Um caminho específico do host, como `/Users/...`, fica fora dessa montagem. O passo 3 usa o backend local.

Para conferir o acesso ao bucket, execute em `backend/`. As operações `put`, `get`, `list` e `delete` devem retornar `ok`.

```bash
uv run python scripts/verify_storage.py
```

## 3. Suba o banco, a API e o frontend

Da raiz, suba o PostgreSQL com pgvector e espere o healthcheck.

```bash
docker compose up -d --wait db
```

Se a porta 5432 já atende um PostgreSQL de desenvolvimento com pgvector, crie um banco separado nesse servidor. Se o servidor é o Compose de outro checkout do NovaMente, rode no checkout que subiu o serviço:

```bash
docker compose exec db createdb -U postgres novamente_dev
```

Aponte `DATABASE_URL` no clone novo para `postgresql://postgres:SENHA_DO_SERVIDOR@localhost:5432/novamente_dev`. Adapte usuário, host e porta ao servidor escolhido. Rode as migrations e inicie a API em `backend/`.

```bash
uv run bash scripts/prestart.sh
```

```bash
uv run fastapi dev
```

Em outro terminal, inicie o frontend na raiz.

```bash
bun run dev
```

Abra o [frontend](http://localhost:5173), a [API em `/api/v1`](http://localhost:8000/api/v1/utils/health-check/) ou o [Swagger](http://localhost:8000/docs).

## 4. Crie, leia e exclua um curso

1. Abra o frontend, clique em "Criar conta" e entre com a conta nova.
2. Em "Novo curso", anexe [`lei-de-acesso-a-informacao.md`](examples/sources/lei-de-acesso-a-informacao.md). Escolha o título "Receber pedidos de informação e encaminhar recursos", o setor "Geral", o nível "Técnico básico" e o formato "Quiz". Clique em "Criar curso".
3. Na lista "Cursos", acompanhe o estado até "Pronto" e abra o curso. Com uma única saída, o leitor aparece na página do curso. Responda a uma pergunta para ver a justificativa e copie o UUID da URL.
4. Em "Resumo do curso", clique em "Excluir curso" e confirme. O curso sai da lista. No console do Object Storage, abra o bucket de desenvolvimento e busque pelo prefixo `courses/{course_id}/`, com o UUID que você copiou. A limpeza roda em segundo plano a cada 30 segundos. Atualize a lista até o prefixo ficar vazio.

## 5. Rode os testes

Da raiz, rode os hooks para os commits do branch. Em um ticket de backend, teste contra o banco de desenvolvimento. Em um ticket de frontend, rode lint e build. Veja o [fluxo de tickets](docs/tickets/README.md#verificações-antes-do-pr).

```bash
uv run prek run --from-ref origin/master --to-ref HEAD
```

```bash
(cd backend && uv run bash scripts/tests-start.sh && uv run coverage report --fail-under=90)
```

```bash
(cd frontend && bun run lint && bun run build)
```

Para validar a geração sem credenciais, use um clone de teste com os dois `.env` copiados dos exemplos. Reserve as portas do Compose. O ponto de entrada montado por `compose.playwright.yml` fornece as respostas controladas do Gemini e o armazenamento em memória. O restante usa o código do produto. Rode os comandos no mesmo shell, da raiz do clone.

```bash
export COMPOSE_FILE=compose.yml:compose.override.yml:compose.playwright.yml
```

```bash
export COMPOSE_PROJECT_NAME=novamente-e2e
```

```bash
docker compose build backend playwright
```

```bash
docker compose run --rm backend bash scripts/prestart.sh
```

```bash
docker compose up -d --wait backend
```

```bash
docker compose run --rm playwright bunx playwright test tests/generation.spec.ts
```

O teste abre os três leitores de um curso aprovado e confere a mensagem de um curso reprovado. Ao terminar, remova os contêineres desse projeto com `docker compose down`.

## Se a instalação parar

| Mensagem observada | Como prosseguir |
| --- | --- |
| `Bind for 0.0.0.0:5432 failed: port is already allocated` | Para a aplicação local, use o banco separado do passo 3. No Playwright, os contêineres se comunicam pela rede do Compose. Use a sobreposição abaixo se a porta 5432 ou 8000 estiver ocupada. |
| `E-mail ou senha incorretos` | Se houver dois backends na porta 8000, o navegador pode chamar o do Compose em vez do local. Aponte `VITE_API_URL` em `frontend/.env` para `http://127.0.0.1:8000` e reinicie o Vite. |
| `Frontend directory '.../backend/app/frontend' does not exist` | No clone novo, o FastAPI avisa que ainda não há um build estático. Abra o frontend pelo Vite em `http://localhost:5173`. |

Para deixar as portas 5432 e 8000 livres no host durante o Playwright, salve este arquivo como `/tmp/novamente-e2e-ports.yml` com o Docker Compose que suporta [`!reset`](https://docs.docker.com/reference/compose-file/merge/#reset-value).

```yaml
services:
  db:
    ports: !reset []
  backend:
    ports: !reset []
```

Depois de definir `COMPOSE_FILE` no passo 5, acrescente o arquivo antes de rodar os comandos de Docker.

```bash
export COMPOSE_FILE="$COMPOSE_FILE:/tmp/novamente-e2e-ports.yml"
```
