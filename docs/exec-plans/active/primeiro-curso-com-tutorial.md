# Criar um curso com um tutorial a partir de um documento de texto

Este ExecPlan é um documento vivo. As seções `Progresso`, `Surpresas e Descobertas`, `Registro de Decisões` e `Resultados e Retrospectiva` devem ser mantidas atualizadas conforme o trabalho avança.

Este documento segue `docs/PLANS.md`, na raiz do repositório, e deve ser mantido de acordo com ele.

## Propósito / Visão Geral

Hoje o NovaMente é o template full-stack-fastapi: uma pessoa cria conta, entra e gerencia "items", uma tabela de exemplo que o produto não usa. Nada do produto existe.

Depois deste plano, uma pessoa autenticada abre a tela "Cursos", preenche um formulário com título, setor (nicho), nível de público e formato, anexa um arquivo `.txt` e clica em "Criar curso". O curso aparece na lista com o estado "Gerando". Em menos de um minuto o estado muda para "Pronto", e a pessoa abre o curso e lê um tutorial gerado a partir do texto dela, com a lista dos trechos do documento que o tutorial usou.

Esta é a primeira camada do produto. Ela usa o esquema definitivo do banco (ERD versão 5, descrito em `docs/generated/db-schema.md`) e só aceita o que o protótipo precisa: texto puro, um documento por curso e um único conteúdo do formato `tutorial`. Flashcards, quiz, PDF, regeneração e vários documentos ficam para planos seguintes, que crescem sobre esta camada sem trocar o esquema.

## Progresso

- [x] (2026-11-02 00:00Z) Plano escrito.
- [ ] Marco 1: models do ERD, migration única de base, remoção de `Item` no backend e no frontend, banco local migrado, testes e build passando.
- [ ] Marco 2: armazenamento de objetos (MinIO local, OCI em produção) e `endpoint` que cria curso, documento e conteúdo pendente.
- [ ] Marco 3: indexação do texto (chunks e embeddings) e geração do tutorial com Gemini, em tarefa de fundo.
- [ ] Marco 4: telas "Cursos", "Novo curso" e "Curso" no frontend, com teste Playwright.
- [ ] Marco 5: validação de ponta a ponta com chave Gemini real e atualização da documentação.

## Surpresas e Descobertas

Nenhuma ainda.

## Registro de Decisões

- Decisão: usar Gemini, pelo SDK oficial `google-genai`, para embeddings e para a geração do tutorial.
  Justificativa: `docs/generated/db-schema.md` fixa `embedding_model = gemini-embedding-2` e `vector(768)`. A página oficial do modelo (https://ai.google.dev/gemini-api/docs/models/gemini-embedding-2) lista 768 como dimensão recomendada. Usar o mesmo fornecedor na geração exige uma só chave (`GEMINI_API_KEY`) e um só cliente.
  Data/Autor: 2026-11-02, Flavio Murata com agente.

- Decisão: guardar arquivos pela API compatível com S3, com `boto3`. Em desenvolvimento e nos testes, o serviço `minio` do Docker Compose atende essa API. Em produção, o OCI Object Storage atende a mesma API pelo seu `endpoint` de compatibilidade com S3.
  Justificativa: o esquema guarda `oci_object_key` e o produto vai rodar no OCI. Um único caminho de código serve aos dois ambientes. Um armazenamento em disco local seria um paliativo a substituir depois.
  Data/Autor: 2026-11-02, Flavio Murata com agente.

- Decisão: rodar a indexação e a geração em `BackgroundTasks` do FastAPI, no mesmo processo da API.
  Justificativa: a escala planejada é de 10 usuários e cerca de 15.000 chunks. O esquema já tem estados (`initializing`, `pending`, `running`, `failed`) que tornam a tarefa observável. Uma fila externa (Celery, RQ) é uma peça a mais sem necessidade nesta escala. Limite aceito: se o processo cair no meio de uma geração, o curso fica em `initializing` até a rota de nova tentativa existir (plano seguinte).
  Data/Autor: 2026-11-02, Flavio Murata com agente.

- Decisão: apagar as seis migrations do template e criar uma única migration de base com o ERD inteiro, sem a tabela `item`.
  Justificativa: o repositório ainda não tem banco em produção. Uma migration de base limpa paga o débito "A tabela `item` do template continua no banco e na interface" de `docs/exec-plans/tech-debt-tracker.md` e evita uma cadeia de migrations que cria e depois apaga `item`. O custo é que um banco local antigo precisa ser recriado (ver `Idempotência e Recuperação`).
  Data/Autor: 2026-11-02, Flavio Murata com agente.

- Decisão: remover `Item` agora, antes de `course` ter rota e tela.
  Justificativa: o débito no rastreador sugeria esperar `course` servir de exemplo. A pessoa responsável pediu para pagar o débito no Marco 1. O Marco 2 e o Marco 4 entregam a rota e a tela de `course` logo depois.
  Data/Autor: 2026-11-02, Flavio Murata.

- Decisão: o `focus` do primeiro tutorial é o título do curso.
  Justificativa: `course_content.focus` é obrigatório e não vazio. O formulário do protótipo não precisa de um campo a mais. Um plano seguinte pode expor `focus` quando o curso tiver mais de uma peça.
  Data/Autor: 2026-11-02, Flavio Murata com agente.

- Decisão: as citações do tutorial são todos os chunks recuperados pela busca vetorial e enviados ao modelo, com a similaridade de cosseno de cada um.
  Justificativa: é o vínculo verificável entre o texto gerado e o documento. Pedir ao modelo que aponte quais trechos usou fica para quando houver avaliação de qualidade (`grounding_score`, `clarity`).
  Data/Autor: 2026-11-02, Flavio Murata com agente.

- Decisão: referenciar `docs/generated/db-schema.md` em vez de copiar as tabelas de colunas para o plano, e provar a conformidade com `test_schema_matches_erd`.
  Justificativa: o ERD é um arquivo versionado no repositório e é a fonte única do esquema. Uma cópia no plano pode divergir dele. O teste no catálogo do Postgres pega omissões que `alembic check` não detecta.
  Data/Autor: 2026-11-02, Flavio Murata com agente.

- Decisão: `GEMINI_API_KEY` é opcional nas configurações; sem ela, a geração falha com mensagem clara.
  Justificativa: o CI, os testes e o Playwright precisam subir o backend sem chave. Uma chave obrigatória quebraria esses ambientes, e um provedor falso dentro da aplicação seria código só de teste em produção.
  Data/Autor: 2026-11-02, Flavio Murata com agente.

## Resultados e Retrospectiva

Nada a relatar ainda.

## Contexto e Orientação

O repositório tem duas partes. `backend/` é uma API em Python 3.14 com FastAPI (framework web) e SQLModel (camada que une Pydantic e SQLAlchemy para descrever tabelas como classes Python). `frontend/` é uma aplicação React com TanStack Router, TanStack Query e componentes shadcn/ui, empacotada com Vite e gerenciada com `bun`. O banco é PostgreSQL 18 com a extensão pgvector (tipo `vector` para guardar embeddings, que são listas de números que representam o sentido de um texto). O serviço `db` de `compose.yml` usa a imagem `pgvector/pgvector:0.8.7-pg18`.

Arquivos que importam:

- `backend/app/models.py`: todas as classes SQLModel. Hoje tem `User`, `Item` e os schemas de entrada e saída da API.
- `backend/app/crud.py`: funções de acesso ao banco (`create_user`, `authenticate`, `create_item`).
- `backend/app/api/main.py`: registra os routers. `backend/app/api/routes/` tem `login.py`, `users.py`, `utils.py`, `private.py` e `items.py`.
- `backend/app/api/deps.py`: `SessionDep` (sessão do banco) e `CurrentUser` (usuário autenticado pelo token JWT).
- `backend/app/core/config.py`: classe `Settings`, lida do arquivo `.env` na raiz.
- `backend/app/alembic/`: Alembic, a ferramenta de migrations (scripts versionados que mudam o esquema do banco). `env.py` usa `SQLModel.metadata` como alvo. `versions/` tem seis migrations do template. `script.py.mako` é o molde de uma migration nova.
- `backend/scripts/prestart.sh`: roda `alembic upgrade head`.
- `backend/scripts/test.sh` e `lint.sh`: testes com cobertura e verificação de tipos e estilo.
- `backend/tests/`: testes `pytest`. `conftest.py` abre uma sessão no banco real e, ao final, apaga `Item` e `User`.
- `frontend/src/routes/`: rotas do TanStack Router. `_layout/items.tsx` é a tela de items. `frontend/src/components/Items/` tem os componentes dela. `frontend/src/components/Sidebar/AppSidebar.tsx` tem o link "Items".
- `frontend/src/client/`: cliente HTTP gerado a partir do OpenAPI do backend por `scripts/generate-client.sh`. Nunca edite à mão.
- `frontend/tests/`: testes Playwright (navegador real). `items.spec.ts` testa a tela de items.
- `docs/generated/db-schema.md`: a referência do esquema. Este plano implementa esse documento. Em caso de conflito entre este plano e aquele documento, o documento vence e o conflito vai para `Surpresas e Descobertas`.

O esquema tem sete tabelas. `user` é a conta de acesso. `niche` é o setor usado nos exemplos (Fintech, Saúde, E-commerce, Geral). `course` é o curso de um usuário, com um `audience_level` e um `status`. `source_document` guarda os metadados de um arquivo enviado. `document_chunk` guarda cada trecho do documento com o embedding de 768 dimensões. `course_content` guarda uma peça gerada, como um tutorial, com o JSON publicado em `content`. `content_citation` liga um conteúdo aos chunks que ele cita. Chaves estrangeiras compostas, como `document_chunk.(document_id, course_id)` apontando para `source_document.(id, course_id)`, impedem que um registro aponte para dados de outro curso.

Termos usados no plano:

- Chunk: um trecho contínuo do documento, pequeno o bastante para caber com outros no prompt do modelo.
- Busca vetorial: ordenar chunks pela distância de cosseno entre o embedding do chunk e o embedding da pergunta. No pgvector, o operador `<=>` calcula essa distância.
- Armazenamento de objetos: serviço que guarda arquivos por chave, como `courses/{course_id}/documents/{id}.txt`. O MinIO é um servidor local compatível com a API do Amazon S3. O OCI Object Storage oferece a mesma API.
- Tarefa de fundo: função que o FastAPI roda depois de enviar a resposta HTTP, por meio de `BackgroundTasks`.

## Plano de Trabalho

### Marco 1: o banco usa o ERD e o template não tem mais `Item`

Ao final deste marco, `alembic upgrade head` em um banco vazio cria as sete tabelas do ERD, os seis tipos enum, as chaves compostas, os CHECKs e as quatro linhas de `niche`. Nenhum arquivo fora do histórico do Git cita `Item`. A aplicação continua funcionando: cadastro, login, configurações do usuário e o painel inicial. Nenhuma rota nova existe ainda.

Adicione a dependência `pgvector` ao backend (pacote Python que dá o tipo `Vector` ao SQLAlchemy):

    cd backend
    uv add "pgvector>=0.4,<1.0"

Em `backend/app/models.py`, apague `ItemBase`, `ItemCreate`, `ItemUpdate`, `Item`, `ItemPublic` e `ItemsPublic`, e a relação `User.items`. Em `User`, troque `items` por `courses: list["Course"] = Relationship(back_populates="owner", cascade_delete=True)`. Mantenha as colunas de `User`, com uma correção: o ERD dá a `is_active` o padrão `true` no banco, e o template só tem o padrão em Python. Declare `is_active: bool = Field(default=True, sa_column_kwargs={"server_default": sqlalchemy.true()})` em `UserBase`, para que a migration crie `DEFAULT true`.

No mesmo arquivo, defina os enums como `enum.StrEnum`, com os valores em minúsculas exatamente como no ERD: `AudienceLevel` (`non_technical`, `technical_basic`, `technical_advanced`), `ContentFormat` (`tutorial`, `flashcards`, `quiz`), `DocumentStatus` (`uploaded`, `processing`, `indexed`, `failed`), `GenerationStatus` (`pending`, `running`, `succeeded`, `failed`), `ClarityLevel` (`low`, `medium`, `high`) e `CourseStatus` (`initializing`, `ready`, `failed`). Para cada coluna enum, use `sa_column=Column(sqlalchemy.Enum(<Classe>, name="<nome_do_tipo>", values_callable=lambda e: [m.value for m in e]), nullable=..., server_default=...)`. Sem `values_callable`, o SQLAlchemy grava o nome do membro, e não o valor; o nome do tipo no Postgres deve ser o do ERD, como `audience_level`.

Uma regra do SQLModel 0.0.47 (a versão em `backend/uv.lock`) guia toda a tradução. Quando um `Field` recebe `sa_column=Column(...)`, o SQLModel recusa no mesmo `Field` os argumentos `foreign_key`, `ondelete`, `nullable`, `primary_key`, `unique` e `index` (ver `sqlmodel/main.py`, função `Field`), e ignora `max_length` e `sa_column_kwargs`. Então, numa coluna com `sa_column`, todas as opções de banco vão dentro do `Column`, incluindo `ForeignKey`, e só o padrão Python (`default` ou `default_factory`) fica no `Field`. Exemplo para `course.niche_id`:

    niche_id: int = Field(
        sa_column=Column(
            SmallInteger,
            ForeignKey("niche.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )

E para uma coluna enum com padrão no banco:

    status: CourseStatus = Field(
        default=CourseStatus.initializing,
        sa_column=Column(
            sqlalchemy.Enum(CourseStatus, name="course_status", values_callable=lambda e: [m.value for m in e]),
            nullable=False,
            server_default=CourseStatus.initializing.value,
        ),
    )

Colunas sem `sa_column` continuam usando `Field(foreign_key=..., ondelete=..., index=..., max_length=...)`, como `Item.owner_id` fazia no template.

Defina as classes de tabela `Niche`, `Course`, `SourceDocument`, `DocumentChunk`, `CourseContent` e `ContentCitation`, com nomes de tabela explícitos (`__tablename__ = "niche"`, `"course"`, `"source_document"`, `"document_chunk"`, `"course_content"`, `"content_citation"`). Cada coluna segue a tabela correspondente de `docs/generated/db-schema.md`: tipo, nulidade, padrão e índice. Regras de tradução:

- `uuid` vira `uuid.UUID`. Só as chaves primárias geradas recebem `default_factory=uuid.uuid4`. Colunas `uuid` que são chave estrangeira, como `course.owner_id` e `document_chunk.course_id`, não têm padrão.
- `smallint` com auto incremento (`niche.id`) vira `sa_column=Column(SmallInteger, primary_key=True, autoincrement=True)`. `course.niche_id` também é `SmallInteger`.
- `timestamptz` vira `DateTime(timezone=True)`. Onde o ERD diz padrão `now()`, use `default_factory=get_datetime_utc` no Python e `server_default=sqlalchemy.func.now()` no banco.
- `text` vira `sqlalchemy.Text`. `varchar(n)` vira `max_length=n`. `char(64)` vira `sqlalchemy.CHAR(64)`. `bigint` vira `BigInteger`. `jsonb` vira `sqlalchemy.dialects.postgresql.JSONB`. `numeric(3,2)` e `numeric(4,3)` viram `Numeric(3, 2)` e `Numeric(4, 3)`, com tipo Python `decimal.Decimal`.
- `vector(768)` vira `sa_column=Column(pgvector.sqlalchemy.Vector(768), nullable=False)`, com tipo Python `list[float]`.
- Chaves estrangeiras simples usam `foreign_key=` e `ondelete=` como `Item.owner_id` fazia. `course.niche_id` usa `ondelete="RESTRICT"`.
- Chaves compostas, índices únicos compostos e CHECKs ficam em `__table_args__`, com `sqlalchemy.ForeignKeyConstraint`, `UniqueConstraint`, `Index` e `CheckConstraint`. Use exatamente os nomes de CHECK do ERD, como `ck_source_document_size_positive`. Os CHECKs de JSON usam `jsonb_typeof`, por exemplo `content IS NULL OR jsonb_typeof(content) = 'object'`. `ck_course_content_published_pair` é `(content IS NULL) = (oci_object_key IS NULL)`. `ck_course_content_successful_published` é `status <> 'succeeded' OR (content IS NOT NULL AND oci_object_key IS NOT NULL)`.
- Toda chave estrangeira usa `ON DELETE CASCADE`, exceto `course.niche_id`. A tabela "Chaves estrangeiras compostas impedem dados de outro curso" do ERD lista todas.
- `content_citation` tem chave primária composta `(content_id, chunk_id)` e índice `(chunk_id, course_id)`.

O ERD define 16 CHECKs, todos com nome. Os 16 nomes são: `ck_source_document_size_positive`, `ck_source_document_sha256_hex`, `ck_document_chunk_position`, `ck_document_chunk_text_nonempty`, `ck_document_chunk_page`, `ck_document_chunk_tokens`, `ck_course_content_position`, `ck_course_content_focus_nonempty`, `ck_course_content_minutes`, `ck_course_content_grounding`, `ck_course_content_body_json`, `ck_course_content_key_concepts_array`, `ck_course_content_prerequisites_array`, `ck_course_content_published_pair`, `ck_course_content_successful_published` e `ck_content_citation_cosine_similarity`. As expressões estão na seção de cada tabela de `docs/generated/db-schema.md`. Este plano não copia as tabelas de colunas do ERD para não criar uma segunda fonte que pode divergir; o teste `test_schema_matches_erd`, descrito abaixo, prova a conformidade no banco real.

Adicione relações SQLModel só onde o código dos próximos marcos vai navegar: `User.courses`/`Course.owner`, `Course.documents`, `Course.contents`. Relações a mais não ajudam e geram ciclos de import nos schemas de saída.

Remova o resto de `Item` no backend: `create_item` em `backend/app/crud.py`, o arquivo `backend/app/api/routes/items.py` e o registro dele em `backend/app/api/main.py`, `backend/tests/api/routes/test_items.py`, `backend/tests/utils/item.py` e o `delete(Item)` de `backend/tests/conftest.py`. O `conftest.py` passa a apagar só `User`, e a cascata apaga cursos e o resto.

Substitua as migrations. Apague os seis arquivos de `backend/app/alembic/versions/`. Em `backend/app/alembic/script.py.mako`, acrescente `import pgvector.sqlalchemy` aos imports, para que migrations geradas com coluna `Vector` importem o tipo. Suba o banco vazio e gere a migration de base:

    docker compose up -d --wait db
    cd backend
    uv run alembic revision --autogenerate -m "create erd v5 schema"

Antes do autogenerate, confirme que o banco está vazio: `docker compose exec db psql -U postgres -d app -c '\dt'` deve responder `Did not find any relations.` Se houver tabelas, recrie só o volume do banco como descrito em `Idempotência e Recuperação`. Um autogenerate contra um banco com tabelas antigas gera `drop_table` indesejados.

Revise o arquivo gerado à mão, porque o autogenerate não cobre tudo e `alembic check` não detecta depois um CHECK ou um `server_default` omitido: o Alembic instalado não compara CHECKs, e `backend/app/alembic/env.py` não ativa `compare_server_default`. No início de `upgrade()`, acrescente `op.execute("CREATE EXTENSION IF NOT EXISTS vector")`, antes de qualquer tabela. Confira, item por item contra o ERD, que os 16 CHECKs, as três chaves compostas, os índices únicos, os `server_default` e os seis tipos enum estão presentes. No fim de `upgrade()`, insira o seed de `niche` com SQL idempotente:

    INSERT INTO niche (slug, name, description, prompt_hint) VALUES
      ('fintech', 'Fintech', 'Financial technology and digital finance', '<dica>'),
      ('saude', 'Saúde', 'Healthcare and health technology', '<dica>'),
      ('e-commerce', 'E-commerce', 'Online shops and retail platforms', '<dica>'),
      ('geral', 'Geral', 'General-purpose examples', '<dica>')
    ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, prompt_hint = EXCLUDED.prompt_hint

O ERD não traz o texto de `prompt_hint`. Escreva uma frase em inglês por setor, como "Use examples from banking, payments and personal finance.", e registre os textos em `Surpresas e Descobertas`. `downgrade()` apaga as tabelas na ordem inversa e só depois os seis tipos enum (`sa.Enum(name=...).drop(op.get_bind(), checkfirst=True)` ou `DROP TYPE IF EXISTS`). Não apague a extensão `vector` no downgrade, porque outro esquema do mesmo banco pode usá-la.

Remova `Item` do frontend: apague `frontend/src/routes/_layout/items.tsx`, a pasta `frontend/src/components/Items/` e `frontend/tests/items.spec.ts`, apague `randomItemTitle` e `randomItemDescription` de `frontend/tests/utils/random.ts`, e tire o link "Items" de `frontend/src/components/Sidebar/AppSidebar.tsx` (remova o import do ícone `Briefcase` se ele ficar sem uso). Regenere `frontend/openapi.json` e o cliente com `bash scripts/generate-client.sh` na raiz; o script também roda o lint do frontend. Rode `bun run build` em `frontend/` para regenerar `frontend/src/routeTree.gen.ts` e provar que nada mais importa `Items`. Procure qualquer citação restante com `rg -n "Item|items" frontend/src frontend/tests backend/app backend/tests` e trate cada resultado que se refere ao recurso `Item` (palavras como `SidebarMenuItem`, `items-center` do Tailwind e o tipo `Item` de `frontend/src/components/Sidebar/Main.tsx`, que descreve um item de menu, não contam).

Escreva `backend/tests/test_schema.py` com testes que provam o esquema no banco real. Cada teste cria os próprios dados e usa `session.rollback()` depois de um erro esperado. Os testes mínimos são:

- `test_niche_seed`: a tabela `niche` tem os slugs `fintech`, `saude`, `e-commerce` e `geral`.
- `test_course_graph_round_trip`: cria um usuário, um curso, um documento, um chunk com embedding de 768 números, um `course_content` e uma `content_citation`, e lê tudo de volta.
- `test_chunk_rejects_other_course`: um chunk cujo `course_id` difere do curso do documento levanta `sqlalchemy.exc.IntegrityError`.
- `test_citation_rejects_other_course`: uma citação que liga um conteúdo do curso A a um chunk do curso B levanta `IntegrityError`.
- `test_succeeded_content_requires_published`: um `course_content` com `status = succeeded` e `content` nulo levanta `IntegrityError`.
- `test_delete_user_cascades`: apagar o usuário apaga curso, documento, chunk, conteúdo e citação.
- `test_niche_in_use_cannot_be_deleted`: apagar um nicho usado por um curso levanta `IntegrityError` (`ON DELETE RESTRICT`).
- `test_schema_matches_erd`: consulta o catálogo do Postgres e compara com listas escritas no teste a partir do ERD. `pg_constraint` com `contype = 'c'` tem exatamente os 16 nomes de CHECK; `pg_type` com `typtype = 'e'` tem os seis enums e, por `pg_enum`, os valores de cada um na ordem do ERD; `information_schema.columns` dá o `column_default` de `user.is_active`, `course.status`, `source_document.status`, `source_document.embedding_model`, `course_content.status`, `course_content.position` e das colunas `created_at` e `updated_at` com `now()`; `pg_indexes` tem os índices únicos `(id, course_id)` de `source_document`, `document_chunk` e `course_content`, e `(course_id, sha256)` e `(document_id, chunk_index)`.

Por fim, edite `docs/exec-plans/tech-debt-tracker.md`: apague a seção "A tabela `item` do template continua no banco e na interface". Edite `docs/generated/db-schema.md`: troque a frase "Hoje `backend/app/models.py` define só as tabelas `user` e `item`. As outras seis tabelas deste documento ainda não têm model nem migration. A tabela `item` vem do template e não faz parte do ERD." por uma frase que diga que `backend/app/models.py` define as sete tabelas e que a migration de base fica em `backend/app/alembic/versions/`. No item do HNSW em `tech-debt-tracker.md`, troque "A tabela ainda não tem model nem migration." por uma referência ao model `DocumentChunk`.

### Marco 2: a API cria um curso com documento e conteúdo pendente

Ao final deste marco, `POST /api/v1/courses/` recebe um formulário com arquivo, grava o arquivo no armazenamento de objetos e cria, na mesma transação, o `course` (`initializing`), o `source_document` (`uploaded`) e o `course_content` (`tutorial`, `pending`). `GET /api/v1/niches/`, `GET /api/v1/courses/` e `GET /api/v1/courses/{id}` funcionam. Nada é gerado ainda.

Adicione `boto3` ao backend. Acrescente ao `compose.yml` um serviço `minio` (imagem oficial `minio/minio`, comando `server /data`, volume próprio, `healthcheck`) e, em `compose.override.yml`, as portas 9000 e 9001. O backend precisa de um bucket; crie-o na inicialização do backend se não existir (`head_bucket` e, em erro 404, `create_bucket`), só quando `FASTAPI_ENV == "development"`. Em produção o bucket é criado fora da aplicação.

Em `Settings` (`backend/app/core/config.py`), acrescente `OBJECT_STORAGE_ENDPOINT_URL: HttpUrl`, `OBJECT_STORAGE_REGION: str`, `OBJECT_STORAGE_BUCKET: str`, `OBJECT_STORAGE_ACCESS_KEY: str` e `OBJECT_STORAGE_SECRET_KEY: str`. Acrescente os mesmos nomes em `.env.example`, apontando para o MinIO local, e passe-os ao serviço `backend` em `compose.yml`. Crie `backend/app/core/storage.py` com duas funções que usam um único cliente `boto3`: `put_object(key: str, body: bytes, content_type: str) -> None` e `get_object(key: str) -> bytes`, e uma terceira, `delete_object(key: str) -> None`, para a limpeza quando a transação falha.

Crie `backend/app/api/routes/niches.py` (lista de `NichePublic`: `id`, `slug`, `name`, `description`) e `backend/app/api/routes/courses.py`. A rota de criação recebe `title: Annotated[str, Form(min_length=1, max_length=255)]`, `niche_id: Annotated[int, Form()]`, `audience_level: Annotated[AudienceLevel, Form()]`, `format: Annotated[Literal["tutorial"], Form()]` e `file: UploadFile`. Ela remove espaços nas pontas do título. Ela rejeita com HTTP 422 um título que fica vazio, um arquivo vazio, maior que 1 MiB, que não decodifica como UTF-8 ou que só tem espaços, e com HTTP 404 um `niche_id` inexistente. Essas validações rodam antes de gravar qualquer objeto ou linha, porque o título vira `focus` e o texto vira chunks, e os CHECKs `ck_course_content_focus_nonempty` e `ck_document_chunk_text_nonempty` recusariam valores vazios depois. O tipo MIME gravado é sempre `text/plain`, porque o protótipo só aceita texto. Ela calcula o `sha256`, gera os `id`s antes do `insert`, grava o arquivo em `courses/{course_id}/documents/{document_id}.txt` e só então faz o `commit` das três linhas. Se o `commit` falhar, chame `delete_object` para não deixar arquivo órfão. A resposta é `CoursePublic` com HTTP 201.

As rotas de leitura filtram por `Course.owner_id == current_user.id`. Um curso de outro usuário responde HTTP 404, e não 403, para não revelar que o `id` existe. `CourseDetailPublic` inclui os documentos (`id`, `title`, `status`, `error_message`) e os conteúdos (`id`, `format`, `status`, `title`, `content`, `estimated_minutes`, `key_concepts`, `prerequisites`, `error_message` e `citations`) ordenados por `position`, `created_at` e `id`. Cada citação traz `chunk_id`, `chunk_index`, `text` e `similarity`, ordenadas por `similarity` decrescente. A lista fica vazia até o Marco 3 gerar citações.

Testes em `backend/tests/api/routes/test_courses.py` usam o MinIO real do Compose. Cobrem a criação feliz (as três linhas existem e o objeto está no bucket), os casos de título e arquivo inválidos, o nicho inexistente, a lista que só mostra cursos do próprio usuário e o HTTP 404 para curso de outro usuário.

### Marco 3: o tutorial é gerado em tarefa de fundo

Ao final deste marco, criar um curso dispara uma tarefa de fundo que indexa o documento e gera o tutorial. O curso termina em `ready` com `content` preenchido, ou em `failed` com `error_message`.

Adicione `google-genai` ao backend e, em `Settings`, `GEMINI_API_KEY: str | None = None`, `GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-2"` e `GEMINI_GENERATION_MODEL: str`. Antes de escolher o padrão de `GEMINI_GENERATION_MODEL`, confirme na lista oficial de modelos da API Gemini qual modelo estável de texto está disponível, e registre a escolha em `Registro de Decisões`. A chave é opcional para que o backend, os testes e o Playwright subam sem ela; sem chave, `embed_texts` levanta um erro com a mensagem `GEMINI_API_KEY is not set` e o curso termina em `failed` com essa mensagem.

Crie `backend/app/core/llm.py` com duas funções. `embed_texts(texts: list[str]) -> list[list[float]]` chama `client.models.embed_content` com `config=types.EmbedContentConfig(output_dimensionality=768)` e devolve um vetor por texto. `generate_tutorial(*, title: str, audience_level: AudienceLevel, niche_hint: str, chunks: list[str]) -> TutorialBody` chama `client.models.generate_content` com `response_mime_type="application/json"` e `response_schema=TutorialBody`, e valida a resposta com `TutorialBody.model_validate_json`. `TutorialBody` é um model Pydantic com `title`, `summary`, `sections` (lista de `heading` e `body_markdown`), `key_concepts`, `prerequisites` e `estimated_minutes`. O prompt fica em uma constante com `PROMPT_VERSION = "tutorial-v1"`, gravada em `course_content.prompt_version`.

Crie `backend/app/services/course_generation.py` com `generate_first_tutorial(course_id: uuid.UUID) -> None`. A função abre a própria sessão (a sessão da requisição já fechou) e segue esta ordem: documento `processing`; lê o texto do armazenamento; divide em chunks por parágrafo, juntando parágrafos até cerca de 1.000 caracteres e cortando parágrafos maiores; chama `embed_texts`; grava os chunks; documento `indexed`; conteúdo `running`; gera o embedding do `focus`; busca os 8 chunks mais próximos com a consulta SQL do ERD; chama `generate_tutorial`; grava o JSON em `courses/{course_id}/contents/{content_id}/{uuid4}.json`; numa transação, preenche `content`, `title`, `estimated_minutes`, `key_concepts`, `prerequisites`, `oci_object_key`, `llm_model`, `prompt_version`, `status = succeeded`, as citações com `similarity = 1 - distância` e `course.status = ready`. Cada mudança de estado é um `commit` próprio, para que a tela veja o progresso. Em qualquer exceção, a função faz `rollback` da sessão, abre uma sessão nova, marca como `failed` o documento ou o conteúdo da fase que falhou, grava `error_message` com a mensagem da exceção, marca o curso como `failed` e registra o erro no log. Se a exceção ocorrer depois do envio do JSON ao armazenamento, a função chama `delete_object` para a chave nova antes de registrar a falha. A rota de criação agenda a função com `background_tasks.add_task(generate_first_tutorial, course.id)`.

Os testes substituem `embed_texts` e `generate_tutorial` com `monkeypatch` por funções determinísticas (vetores fixos de 768 números e um `TutorialBody` fixo). O `TestClient` do FastAPI roda a tarefa de fundo antes de devolver a resposta, então o teste lê o curso já `ready`. Um segundo teste faz `generate_tutorial` levantar uma exceção e verifica `failed` e `error_message`. Um teste unitário cobre a divisão em chunks.

### Marco 4: o frontend cria e mostra cursos

Ao final deste marco, a barra lateral tem o link "Cursos". A rota `frontend/src/routes/_layout/courses.tsx` lista os cursos com título, nível e estado ("Gerando", "Pronto", "Falhou") e consulta a API a cada 3 segundos enquanto algum curso estiver `initializing`, usando `refetchInterval` do TanStack Query. O botão "Novo curso" abre um diálogo com `react-hook-form` e `zod`, no mesmo padrão dos formulários existentes em `frontend/src/components/UserSettings/`: título, setor (select com `GET /niches/`), nível (três opções com rótulos em português), formato (select com a única opção "Tutorial") e arquivo (`accept=".txt,text/plain"`). A rota `frontend/src/routes/_layout/courses.$courseId.tsx` mostra o tutorial: título, resumo, seções em Markdown, conceitos-chave, pré-requisitos e tempo estimado. Se o curso falhou, mostra a mensagem de erro.

Para renderizar Markdown, verifique primeiro se `frontend/package.json` já tem uma biblioteca para isso. Se não tiver, adicione `react-markdown` e registre a decisão.

Crie `frontend/tests/courses.spec.ts`. O Playwright roda contra o backend real do Compose, sem chave Gemini válida, então o teste cobre o que não depende do modelo: o formulário cria o curso, o curso aparece na lista com estado "Gerando" ou "Falhou" (sem chave o curso falha em segundos, e o teste aceita os dois), a tela do curso falho mostra `GEMINI_API_KEY is not set`, e um arquivo só com espaços mostra a mensagem de erro da API. O caminho de sucesso com tutorial fica coberto pelos testes do backend com `monkeypatch` e pela validação manual do Marco 5.

### Marco 5: validação real e documentação

Com uma `GEMINI_API_KEY` real no `.env`, siga `Validação e Aceitação` e registre a transcrição em `Artefatos e Notas`. Atualize `development.md` com o serviço MinIO e as variáveis novas. Mova este arquivo para `docs/exec-plans/completed/` e preencha `Resultados e Retrospectiva`.

## Passos Concretos

Todos os comandos partem da raiz do repositório, salvo indicação. O `.env` da raiz precisa existir (`cp .env.example .env` na primeira vez).

Para recriar só o banco local do zero, o que apaga os dados do PostgreSQL local e preserva outros volumes, como o do MinIO:

    docker compose rm -s -f db
    docker volume rm "$(basename "$PWD")_app-db-data"
    docker compose up -d --wait db

O nome do volume é o nome do projeto do Compose (por padrão, a pasta do repositório) seguido de `_app-db-data`; confira com `docker volume ls`.

Para migrar e testar o backend:

    cd backend
    uv sync
    uv run bash scripts/prestart.sh
    uv run bash scripts/lint.sh
    uv run bash scripts/tests-start.sh
    uv run coverage report --fail-under=90

Saída esperada do `prestart.sh` no Marco 1, com um `revision id` diferente:

    INFO  [alembic.runtime.migration] Running upgrade  -> 3f2a..., create erd v5 schema

Para conferir o esquema no banco:

    docker compose exec db psql -U postgres -d app -c '\dt'

Saída esperada no Marco 1: as tabelas `alembic_version`, `content_citation`, `course`, `course_content`, `document_chunk`, `niche`, `source_document` e `user`, e nenhuma tabela `item`.

Para provar que os models e a migration batem:

    cd backend
    uv run alembic check

Saída esperada: `No new upgrade operations detected.`

Para provar que a migration desfaz e refaz:

    cd backend
    uv run alembic downgrade base
    uv run alembic upgrade head

Para o frontend:

    bash scripts/generate-client.sh
    cd frontend
    bun run build

Para o Playwright, com o Compose inteiro:

    docker compose build
    docker compose down -v --remove-orphans
    docker compose run --rm backend bash scripts/prestart.sh
    docker compose up -d --wait backend
    docker compose run --rm playwright bunx playwright test

## Validação e Aceitação

Marco 1 está aceito quando: `prestart.sh` migra um banco vazio; `\dt` mostra as oito tabelas listadas acima; `alembic check` não acusa diferença; `downgrade base` seguido de `upgrade head` funciona; `lint.sh` passa; `tests-start.sh` passa, incluindo os testes de `backend/tests/test_schema.py`; `coverage report --fail-under=90` passa, que é o limite do CI em `.github/workflows/test-backend.yml`; `bun run build` passa; os testes Playwright passam (`login.spec.ts`, `sign-up.spec.ts` e `user-settings.spec.ts`); e `rg -n "\bItem\b|ItemPublic|randomItem|items\.tsx|/items" backend frontend/src frontend/tests frontend/openapi.json` não acha nada que se refira ao recurso `Item` (o tipo de menu em `frontend/src/components/Sidebar/Main.tsx` é a única exceção esperada). Abrir http://localhost:5173 com `bun run dev`, criar conta, entrar e abrir "Configurações" funciona, e a barra lateral não tem "Items".

Marco 2 está aceito quando o roteiro abaixo funciona. Com o backend rodando em http://localhost:8000, crie um arquivo, uma conta e um token:

    printf 'O Pix é o sistema de pagamentos instantâneos do Banco Central.\n\nUma transferência Pix usa uma chave.\n' > /tmp/pix.txt
    curl -s -X POST http://localhost:8000/api/v1/users/signup -H 'Content-Type: application/json' \
      -d '{"email":"demo@example.com","password":"demo-password-1"}'
    TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/login/access-token \
      -d 'username=demo@example.com&password=demo-password-1' | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

Depois:

    curl -s -w '\nHTTP %{http_code}\n' -X POST http://localhost:8000/api/v1/courses/ \
      -H "Authorization: Bearer $TOKEN" \
      -F title="Pix para iniciantes" -F niche_id=1 \
      -F audience_level=non_technical -F format=tutorial \
      -F file=@/tmp/pix.txt

responde HTTP 201 com `"status": "initializing"`, e o console do MinIO em http://localhost:9001 mostra o objeto em `courses/<id>/documents/`.

Marco 3 está aceito quando, com `GEMINI_API_KEY` real, `GET /api/v1/courses/<id>` passa a mostrar `"status": "ready"` em menos de um minuto, com um conteúdo `succeeded` cujo `content.sections` não é vazio, e `SELECT count(*) FROM content_citation` é maior que zero. Os testes com `monkeypatch` passam sem chave real.

Marco 4 está aceito quando o fluxo descrito em `Propósito / Visão Geral` funciona no navegador e `courses.spec.ts` passa.

## Idempotência e Recuperação

A migration de base só roda em banco vazio. Um banco local criado com as migrations antigas do template tem `alembic_version` apontando para uma revisão que não existe mais, e `alembic upgrade head` falha com `Can't locate revision`. Nesse caso, recrie o banco com `docker compose down -v` e `docker compose up -d --wait db`. Os comandos estão em `Passos Concretos`. Eles apagam só o volume do PostgreSQL local; faça antes um `docker compose exec db pg_dump -U postgres app > backup.sql` se os dados locais importam. Não há banco de produção com esse esquema; se passar a haver antes deste plano chegar a ele, pare e registre o problema em `Surpresas e Descobertas`.

`downgrade base` seguido de `upgrade head` é seguro e repetível. O seed de `niche` usa `ON CONFLICT`, então rodar de novo não duplica linhas. `generate-client.sh` e `bun run build` regeneram arquivos e podem rodar quantas vezes for preciso.

Na criação de curso, o arquivo vai ao armazenamento antes do `commit`. Se o `commit` falhar, a rota apaga o objeto. Se a tarefa de fundo falhar, ela faz `rollback`, registra a falha numa sessão nova e apaga o JSON que tiver enviado. Os chunks já gravados de um documento `indexed` continuam válidos. Uma falha ao apagar um objeto deixa um objeto órfão no armazenamento, registrado no log com a chave; o plano aceita esse caso raro até existir a limpeza de objetos descrita no ERD.

## Artefatos e Notas

Nenhum ainda.

## Interfaces e Dependências

Dependências novas do backend: `pgvector` (Marco 1), `boto3` (Marco 2) e `google-genai` (Marco 3). Dependência nova possível do frontend: `react-markdown` (Marco 4), só se nada equivalente já existir.

Ao final do Marco 1, `backend/app/models.py` exporta, além do que já tem para `User`, `Message`, `Token` e `TokenPayload`: `AudienceLevel`, `ContentFormat`, `DocumentStatus`, `GenerationStatus`, `ClarityLevel`, `CourseStatus`, `Niche`, `Course`, `SourceDocument`, `DocumentChunk`, `CourseContent` e `ContentCitation`. Não exporta nada com `Item` no nome.

Ao final do Marco 2:

    # backend/app/core/storage.py
    def put_object(key: str, body: bytes, content_type: str) -> None: ...
    def get_object(key: str) -> bytes: ...
    def delete_object(key: str) -> None: ...

Ao final do Marco 3:

    # backend/app/core/llm.py
    PROMPT_VERSION = "tutorial-v1"
    class TutorialSection(BaseModel): heading: str; body_markdown: str
    class TutorialBody(BaseModel):
        title: str
        summary: str
        sections: list[TutorialSection]
        key_concepts: list[str]
        prerequisites: list[str]
        estimated_minutes: int
    def embed_texts(texts: list[str]) -> list[list[float]]: ...
    def generate_tutorial(*, title: str, audience_level: AudienceLevel, niche_hint: str, chunks: list[str]) -> TutorialBody: ...

    # backend/app/services/course_generation.py
    def split_into_chunks(text: str, max_chars: int = 1000) -> list[str]: ...
    def generate_first_tutorial(course_id: uuid.UUID) -> None: ...

Nota de revisão (2026-11-02): uma revisão do plano por um agente Codex apontou falhas que este texto corrige. O SQLModel recusa `foreign_key` e outras opções junto de `sa_column`. `user.is_active` não tinha padrão no banco. `alembic check` não prova CHECKs nem padrões, então entrou `test_schema_matches_erd`. Ficaram faltando `randomItemTitle`, `randomItemDescription` e `frontend/openapi.json` na remoção de `Item`. `docker compose down -v` apagaria também o volume do MinIO. Título e texto só com espaços violariam CHECKs. As citações não chegavam à API nem à tela. A tarefa de fundo não definia `rollback`. O Playwright dependia de uma chave Gemini.
