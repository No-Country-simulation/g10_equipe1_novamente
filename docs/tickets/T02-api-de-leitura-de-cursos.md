---
id: T02
title: Exponha a leitura de setores e cursos e o seed de desenvolvimento
blocked_by: []
touches:
  - backend/app/models.py
  - backend/app/api/main.py
  - backend/app/api/routes/niches.py
  - backend/app/api/routes/courses.py
  - backend/app/api/routes/private.py
  - backend/tests/api/routes/test_niches.py
  - backend/tests/api/routes/test_courses.py
  - backend/tests/api/routes/test_private.py
  - backend/tests/utils/course.py
  - frontend/src/client/
executor: agente
size: 5
---

# T02 - Exponha a leitura de setores e cursos e o seed de desenvolvimento

## Contexto

O esquema do banco existe, mas a API só tem rotas de conta. As telas "Cursos" (T17) e "Curso" (T18) precisam ler cursos antes de a geração existir.

O CI não tem chave do Gemini, então nenhum teste de navegador consegue gerar um curso de verdade. Uma rota de desenvolvimento que grava um curso pronto resolve isso. O frontend já usa uma rota assim para criar usuários (`POST /api/v1/private/users/`).

Leia antes: `docs/product-specs/pacote-json-e-armazenamento.md`, `docs/generated/db-schema.md` e `backend/app/api/routes/users.py`, que mostra o padrão das rotas.

## Escopo

Três rotas de leitura, uma rota de seed só para desenvolvimento, e os schemas de resposta.

## Fora do escopo

- Criar curso pela API pública (T23).
- Nova tentativa e a regra dos 10 minutos (T32).
- Excluir curso (T33).
- Validar o formato de `content` (T05 define os modelos).
- Paginação. Um usuário tem até 5 cursos.

## Contrato

### Rotas

| Rota | Resposta | Regras |
| --- | --- | --- |
| `GET /api/v1/niches/` | `list[NichePublic]` | Exige login. Ordena por `id`. |
| `GET /api/v1/courses/` | `CoursesPublic` | Exige login. Só os cursos do usuário. Ordena por `created_at`, do mais novo ao mais velho. |
| `GET /api/v1/courses/{course_id}` | `CourseDetail` | Exige login. Curso inexistente ou de outro usuário responde HTTP 404 com `detail` "Curso não encontrado." |
| `POST /api/v1/private/courses/` | `CourseDetail` | Sem login. Existe só com `FASTAPI_ENV=development`, como o resto de `private.py`. |

### Schemas de resposta

Acrescente no fim de `backend/app/models.py`, depois de `ContentCitation`. Não altere as classes de tabela.

```python
class NichePublic(SQLModel):
    id: int
    slug: str
    name: str
    description: str | None


class ContentSummary(SQLModel):
    id: uuid.UUID
    format: ContentFormat
    status: GenerationStatus
    position: int
    title: str | None


class CourseSummary(SQLModel):
    id: uuid.UUID
    title: str
    audience_level: AudienceLevel
    status: CourseStatus
    niche: NichePublic
    created_at: datetime
    updated_at: datetime
    contents: list[ContentSummary]


class CoursesPublic(SQLModel):
    data: list[CourseSummary]
    count: int


class DocumentPublic(SQLModel):
    id: uuid.UUID
    title: str
    original_filename: str
    mime_type: str
    size_bytes: int
    status: DocumentStatus
    error_message: str | None


class CitationPublic(SQLModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    text: str
    page_number: int | None
    similarity: float | None


class ContentPublic(ContentSummary):
    content: dict[str, Any] | None
    estimated_minutes: int | None
    key_concepts: list[str] | None
    prerequisites: list[str] | None
    grounding_score: float | None
    clarity: ClarityLevel | None
    review_notes: str | None
    oci_object_key: str | None
    error_message: str | None
    updated_at: datetime
    citations: list[CitationPublic]
```

`CourseDetail` tem os campos de `CourseSummary`, com `contents: list[ContentPublic]`, e mais `documents: list[DocumentPublic]`.

`contents` vem em ordem de `position`. `citations` vem em ordem de `similarity`, da maior à menor. `grounding_score` e `similarity` saem como número, não como texto.

### Corpo do seed

Defina estes modelos em `private.py`, como `PrivateUserCreate`.

```python
class PrivateDocumentCreate(BaseModel):
    original_filename: str = "documento.md"
    status: DocumentStatus = DocumentStatus.indexed
    chunks: list[str] = []


class PrivateContentCreate(BaseModel):
    format: ContentFormat
    status: GenerationStatus = GenerationStatus.succeeded
    title: str | None = None
    content: dict[str, Any] | None = None
    estimated_minutes: int | None = None
    key_concepts: list[str] | None = None
    prerequisites: list[str] | None = None
    grounding_score: float | None = None
    clarity: ClarityLevel | None = None
    review_notes: str | None = None
    error_message: str | None = None
    cited_chunks: list[int] = []


class PrivateCourseCreate(BaseModel):
    owner_email: str
    title: str
    niche_slug: str = "geral"
    audience_level: AudienceLevel
    status: CourseStatus = CourseStatus.ready
    documents: list[PrivateDocumentCreate]
    contents: list[PrivateContentCreate]
```

## Detalhes técnicos

- Registre os routers novos em `backend/app/api/main.py`.
- Toda consulta de curso filtra por `owner_id` do usuário autenticado (regra 8 de `db-schema.md`).
- O seed grava as linhas direto, sem OCI e sem Gemini:
    - `source_document`: `title` igual ao nome do arquivo, `mime_type` `text/markdown`, `sha256` calculado do texto dos chunks (ou de um UUID, se não há chunks), `size_bytes` maior que zero, `oci_object_key` `courses/{course_id}/documents/{document_id}.md`.
    - `document_chunk`: um por texto, com `chunk_index` na ordem e `embedding` `[1.0] + [0.0] * 767`.
    - `course_content`: `position` na ordem da lista e `focus` igual ao título do curso. Um conteúdo com `content` recebe `oci_object_key` `courses/{course_id}/contents/{content_id}/{uuid}.json`.
    - `content_citation`: `cited_chunks` traz índices na lista de todos os chunks do curso, na ordem dos documentos. Use `similarity` 0.9.
- O seed responde HTTP 404 se `owner_email` ou `niche_slug` não existe, e HTTP 422 se `documents` ou `contents` está vazio, se um conteúdo `succeeded` não tem `content`, ou se um índice de `cited_chunks` não existe.
- `backend/tests/utils/course.py` traz uma função que cria um curso pelo seed. Os testes das rotas de leitura usam essa função.
- O hook `generate-frontend-sdk` gera `frontend/src/client/` de novo. Inclua o resultado no commit.

## Critérios de aceite

- [ ] As quatro rotas respondem conforme o contrato.
- [ ] Um usuário nunca recebe um curso de outro usuário, na lista ou no detalhe.
- [ ] As rotas de leitura respondem HTTP 401 ou 403 sem token.
- [ ] `POST /api/v1/private/courses/` não existe sem `FASTAPI_ENV=development`.
- [ ] `frontend/src/client/` tem `NichesService`, `CoursesService` e o método de seed em `PrivateService`.
- [ ] Os hooks e os testes passam, com cobertura de 90% ou mais.

## Cenários de teste

1. `GET /niches/` devolve os quatro setores do seed da migration, em ordem de `id`.
2. `GET /courses/` devolve lista vazia e `count` 0 para um usuário novo.
3. `GET /courses/` devolve só os cursos do usuário, do mais novo ao mais velho, com `niche` e `contents` resumidos.
4. `GET /courses/{id}` devolve documentos, conteúdos em ordem de `position` e citações com o texto do chunk e o título do documento.
5. `GET /courses/{id}` de outro usuário e de um `id` inexistente respondem HTTP 404.
6. O seed cria um curso `initializing` com um conteúdo `pending`, e um curso `ready` com um conteúdo `succeeded` e citações.
7. O seed recusa cada caso de erro listado em "Detalhes técnicos".
