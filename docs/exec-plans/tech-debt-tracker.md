# Débitos técnicos conhecidos

Este arquivo lista o débito técnico que já existe no repositório e que ninguém está pagando agora. Débito técnico aqui é código, configuração ou decisão que a equipe sabe que não é a forma final. Uma funcionalidade que ainda não começou não é débito. Ela fica em uma issue ou em um ExecPlan, descrito em `docs/PLANS.md`.

Cada entrada tem os mesmos campos:

- **Onde**: os caminhos a partir da raiz do repositório.
- **Por que existe**: o motivo para aceitar o débito e o `commit` ou ExecPlan que o aceitou.
- **Custo de manter**: o risco concreto de deixar como está.
- **Quando pagar**: o gatilho para pagar o débito e o resultado que mostra que ele acabou.
- **Estado**: `aberto` ou `planejado`. Um débito `planejado` tem link para o ExecPlan que vai pagá-lo.

Quando um débito é pago, a entrada sai deste arquivo. O histórico do Git guarda a entrada removida.

## A coluna `embedding` não tem índice HNSW

**Onde**: a tabela `document_chunk`, descrita em `docs/generated/db-schema.md`. O model é `DocumentChunk` em `backend/app/models.py`.

**Por que existe**: `docs/generated/db-schema.md` decide começar com busca exata por distância de cosseno. Um índice HNSW (índice aproximado de vizinhos mais próximos do pgvector) só entra depois de um benchmark.

**Custo de manter**: a busca exata lê todos os chunks dos documentos `indexed` do curso. O tempo de cada busca cresce junto com o número de chunks.

**Quando pagar**: quando um benchmark com dados reais mostrar que a busca exata passa do tempo aceito pela tela que a usa. O benchmark ainda não existe e o limite de tempo ainda não foi definido. Acaba quando uma migration cria o índice e o benchmark mostra o tempo antes e depois.

**Estado**: aberto.

## Workflows do GitHub Actions ainda servem o repositório do template

**Onde**: `.github/workflows/`.

**Por que existe**: o `commit` `d1ff5b6` copiou os workflows do template sem adaptar.

**Custo de manter**: `add-to-project.yml`, `bump-pre-commit-hooks.yml` e `issue-manager.yml` só rodam quando o dono do repositório é `fastapi`. Este repositório pertence a `No-Country-simulation`, então esses três workflows nunca rodam. `zizmor.yml` roda, mas escolhe entre `advanced-security` e `annotations` com a mesma condição. `smokeshow.yml` envia a cobertura de testes do backend para o serviço externo smokeshow. `deploy-docker-compose.yml` roda em um runner `self-hosted` e precisa dos secrets `SECRET_KEY` e `POSTGRES_PASSWORD`. Não verifiquei se esse runner e esses secrets existem.

**Quando pagar**: antes de a equipe depender do CI para revisar ou publicar. Acaba quando cada arquivo em `.github/workflows/` roda neste repositório ou é apagado, e o `deploy-docker-compose.yml` tem um destino real ou sai.

**Estado**: aberto.

## Os documentos em `docs/needs-validation/` não foram validados

**Onde**: `docs/needs-validation/`.

**Por que existe**: o `commit` `dd03a49` moveu para essa pasta os documentos de planejamento que vieram de fora do código, como os arquivos do Drive e o relatório técnico.

**Custo de manter**: esses documentos podem contradizer o código e `docs/generated/db-schema.md`. Por exemplo, `docs/needs-validation/RELATORIO_TECNICO_PROJETO.md` ainda dá "FastAPI / Node.js" como opção de backend, mas o backend é FastAPI. Um agente que lê esses arquivos pode tratar uma ideia antiga como decisão atual.

**Quando pagar**: antes de usar um desses documentos como fonte para um ExecPlan. Acaba quando cada documento sai da pasta, seja para `docs/` depois de validado, seja para fora do repositório.

**Estado**: aberto.
