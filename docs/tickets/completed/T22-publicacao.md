---
id: T22
title: Publique um conteúdo aprovado na OCI e no banco
blocked_by: [T03, T04, T05, T14]
touches:
  - backend/app/services/publishing.py
  - backend/tests/services/test_publishing.py
executor: agente
size: 3
---

# T22 - Publique um conteúdo aprovado na OCI e no banco

## Contexto

`docs/ARCHITECTURE.md` define os passos 10 e 11 de uma geração: o backend grava o JSON aprovado na OCI, com uma chave nova, e depois grava em uma transação o conteúdo, as notas, as citações e `status = succeeded`. O primeiro conteúdo publicado muda o curso para `ready`. Se a transação falha, o backend apaga o objeto. Nenhum código publica conteúdo hoje.

Este ticket entrega a publicação como uma função. A tarefa de fundo (T28) chama a função quando o grafo de geração (T24) decide publicar.

Leia antes: `docs/product-specs/pacote-json-e-armazenamento.md`, `docs/ARCHITECTURE.md`, seção "A criação de um curso segue doze passos", e `docs/generated/db-schema.md`, tabelas `course_content` e `content_citation` e a seção "O backend garante as regras que o banco não expressa".

## Escopo

- Montar o arquivo JSON de um conteúdo e gravar na OCI.
- Gravar o conteúdo, as notas e as citações em uma transação.
- Mudar o curso para `ready`.
- Apagar o objeto novo se a transação falha, e o objeto antigo depois de uma regeneração.

## Fora do escopo

- Decidir se o conteúdo é publicado (T04, pronto, e T24).
- Marcar um conteúdo como `running` ou `failed` (T28).
- Gravar `llm_model` e `prompt_version`. Essas colunas descrevem a última geração, com sucesso ou não, e T28 as grava ao iniciar a geração.
- Rota de regeneração.

## Contrato

### Módulos que este ticket usa

Copiados do `master`. Não edite esses módulos.

```python
# app.core.storage
class StorageError(Exception): ...


class Storage(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> None: ...
    def delete(self, key: str) -> None: ...


class InMemoryStorage: ...  # para os testes


def content_key(course_id: uuid.UUID, content_id: uuid.UUID) -> str: ...


# app.services.content_schemas
class GeneratedBase(StrictModel):
    title: Title
    estimated_minutes: Minutes
    key_concepts: KeyConcepts
    prerequisites: Prerequisites


# GeneratedTutorial, GeneratedFlashcards e GeneratedQuiz acrescentam `content`.
GENERATED_MODELS: dict[ContentFormat, type[GeneratedBase]]


class ContentPackage(StrictModel):
    format: ContentFormat
    audience_level: AudienceLevel
    niche: Text  # niche.slug
    title: Title
    content: dict[str, Any]
    estimated_minutes: Minutes
    key_concepts: KeyConcepts
    prerequisites: Prerequisites
    grounding_score: float = Field(ge=0, le=1)
    clarity: ClarityLevel
    review_notes: Text


# app.services.grounding
class ReviewResult(BaseModel):
    claims: list[ClaimReview]
    clarity: ClarityLevel
    review_notes: str


@dataclass(frozen=True, slots=True)
class GroundingReport:
    score: Decimal
    passed: bool
    supported: list[ClaimReview]
    unsupported: list[ClaimReview]
    cited_chunk_ids: list[uuid.UUID]


# app.services.retrieval
@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    text: str
    page_number: int | None
    similarity: float


# app.models
Course, CourseContent, ContentCitation, Niche, CourseStatus, GenerationStatus
```

### Módulo que este ticket cria

Em `backend/app/services/publishing.py`:

```python
class ContentNotFoundError(LookupError): ...


class PublishError(Exception):
    """A mensagem é um texto para `course_content.error_message`."""


def publish_content(
    *,
    session: Session,
    storage: Storage,
    content_id: uuid.UUID,
    generated: GeneratedBase,
    review: ReviewResult,
    report: GroundingReport,
    chunks: Sequence[RetrievedChunk],
) -> CourseContent: ...
```

`generated` é a versão aprovada. `review` e `report` são a revisão e o relatório dessa versão. `chunks` são os trechos que a busca devolveu para essa geração.

`publish_content` confere tudo antes de gravar. Nenhuma destas falhas grava na OCI nem no banco:

| Condição | Exceção |
| --- | --- |
| O `course_content` não existe | `ContentNotFoundError` |
| `report.passed` é falso | `ValueError` |
| `generated` não é instância de `GENERATED_MODELS[content.format]` | `ValueError` |
| Um id de `report.cited_chunk_ids` não está em `chunks` | `ValueError` |
| O `ContentPackage` não valida, por exemplo com `review_notes` vazio | `pydantic.ValidationError` |

Depois, nesta ordem:

1. Monta o `ContentPackage`:

    | Campo | Origem |
    | --- | --- |
    | `format` | `content.format` |
    | `audience_level` | `course.audience_level` |
    | `niche` | `niche.slug` do curso |
    | `title`, `estimated_minutes`, `key_concepts`, `prerequisites` | `generated` |
    | `content` | `generated.content.model_dump(mode="json")` |
    | `grounding_score` | `float(report.score)` |
    | `clarity`, `review_notes` | `review` |

2. Grava o arquivo: `storage.put(key, package.model_dump_json().encode(), "application/json")`, com `key = content_key(course.id, content.id)`. Se `put` falha, levanta `PublishError` e não muda o banco.
3. Em uma transação:
    - Grava em `course_content`: `title`, `content` (o mesmo dicionário do pacote), `estimated_minutes`, `key_concepts`, `prerequisites`, `grounding_score = report.score`, `clarity`, `review_notes`, `oci_object_key = key`, `status = succeeded`, `error_message = None` e `updated_at` com a hora atual.
    - Apaga todas as linhas de `content_citation` do conteúdo e grava uma por id de `report.cited_chunk_ids`, com `course_id` do curso e `similarity` igual à do trecho em `chunks`, como `Decimal` com 3 casas.
    - Se `course.status` não é `ready`, grava `ready` e `course.updated_at` com a hora atual.
    - Faz `commit`.
4. Se a transação falha, faz `rollback`, apaga o objeto novo com `storage.delete(key)` e levanta `PublishError`. O conteúdo e as citações anteriores ficam como estavam.
5. Se o conteúdo tinha um `oci_object_key` antes, apaga o objeto antigo. Se a exclusão falha, tenta mais uma vez. Se falha de novo, registra no log o `course_id`, a chave e o tipo do erro, e segue sem levantar exceção.
6. Devolve o `CourseContent` atualizado.

Outras regras:

- Nenhum JSON reprovado vai para a OCI nem para `course_content.content` (regra 11 de `docs/ARCHITECTURE.md`).
- As citações são só os chunks de `report.cited_chunk_ids` (regra 9).
- A função não muda um conteúdo para `failed`. Quem chama trata `PublishError`.
- Mensagens de `PublishError`: "Não foi possível guardar o conteúdo no armazenamento." na falha do passo 2 e "Não foi possível publicar o conteúdo." na falha do passo 3.
- O conteúdo gerado nunca entra em mensagem de erro nem em log.
- A função faz o próprio `commit`. Quem chama entrega uma sessão sem mudanças pendentes.

## Detalhes técnicos

- Use `content_key` para a chave. Cada chamada devolve uma chave nova.
- O CHECK `ck_course_content_published_pair` exige `content` e `oci_object_key` juntos. Grave os dois na mesma transação.
- A chave composta de `content_citation` recusa um chunk de outro curso. Não trate esse caso à parte: ele cai no passo 4.
- Não acrescente dependência. Não edite `backend/app/models.py`, `backend/app/core/storage.py`, `backend/app/services/content_schemas.py` nem `backend/pyproject.toml`.
- O hook gera o cliente do frontend de novo. O OpenAPI não muda, então `frontend/src/client/` não pode aparecer no diff.
- Nos testes, crie o curso com `tests.utils.course.create_course`, com um documento com chunks e um conteúdo `pending` sem `content`. Leia os `DocumentChunk` do banco para montar os `RetrievedChunk`. Use um `InMemoryStorage`.
- Nenhum teste chama a OCI nem o Gemini.

## Critérios de aceite

- [x] `publish_content` cumpre o contrato.
- [x] O arquivo na OCI valida como `ContentPackage`, e `course_content.content` traz só o conteúdo.
- [x] Nenhum caminho de falha deixa um objeto novo na OCI sem a linha publicada, nem uma linha publicada sem objeto.
- [x] Um relatório reprovado nunca é publicado.
- [x] Nenhum teste chama a OCI nem o Gemini.
- [x] Os hooks e os testes passam, com cobertura de 90% ou mais.

## Cenários de teste

Em `backend/tests/services/test_publishing.py`, com `InMemoryStorage`:

1. Publicar um tutorial aprovado em um curso `initializing`: o conteúdo fica `succeeded`, com título, conteúdo, minutos, conceitos, pré-requisitos, nota, clareza, observações e `oci_object_key`. O curso fica `ready`.
2. O objeto gravado na chave do conteúdo valida como `ContentPackage`, com o `format`, o `audience_level` e o `niche` do curso, e a chave segue `courses/{course_id}/contents/{content_id}/{uuid}.json`.
3. Com dois chunks citados entre três, `content_citation` tem duas linhas, com a `similarity` de cada trecho.
4. `GET /api/v1/courses/{course_id}` devolve o conteúdo publicado com as duas citações.
5. `report.passed` falso levanta `ValueError`. O armazenamento fica vazio e o conteúdo continua `pending`.
6. Um `GeneratedTutorial` para um conteúdo de formato `quiz` levanta `ValueError`, sem gravar nada.
7. Um id citado que não está em `chunks` levanta `ValueError`, sem gravar nada.
8. `review_notes` vazio levanta `ValidationError`, sem gravar nada.
9. Um armazenamento cujo `put` levanta `StorageError` gera `PublishError`. O conteúdo continua `pending` e sem citações.
10. Uma falha no `commit` gera `PublishError`. O armazenamento fica vazio e o conteúdo continua `pending`.
11. Publicar de novo um conteúdo já publicado troca o conteúdo e as citações, usa uma chave nova e apaga o objeto antigo. O curso continua `ready`.
12. Na regeneração, se `delete` do objeto antigo falha duas vezes, a função devolve o conteúdo publicado e o log traz o `course_id`.
13. Publicar em um curso `failed` muda o curso para `ready`.
14. Um `content_id` que não existe levanta `ContentNotFoundError`.

## Verificação do aceite

- PR revisado: [#25](https://github.com/No-Country-simulation/g10_equipe1_novamente/pull/25), integrado no commit `1c71ccc`.
- CI do PR: todos os checks obrigatórios passaram.
- Revisão automática: os achados sobre os testes foram corrigidos em `39be1fc`.
