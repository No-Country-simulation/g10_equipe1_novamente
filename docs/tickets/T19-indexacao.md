---
id: T19
title: Indexe um documento em chunks com embeddings
blocked_by: [T14, T15, T16]
touches:
  - backend/app/services/indexing.py
  - backend/tests/services/test_indexing.py
executor: agente
size: 3
---

# T19 - Indexe um documento em chunks com embeddings

## Contexto

`docs/ARCHITECTURE.md` define os passos 4 e 5 da criação de um curso: a tarefa de fundo lê cada documento da OCI, divide o texto em chunks de cerca de 1.000 caracteres, pede um embedding por chunk e grava os chunks e o estado `indexed` na mesma transação. Nenhum código faz isso hoje.

Este ticket entrega a indexação de um documento como uma função. A tarefa de fundo (T28) chama a função para cada documento do curso e para no primeiro que falha. A busca vetorial (T03) lê os chunks gravados aqui.

Leia antes: `docs/ARCHITECTURE.md`, seções "A criação de um curso segue doze passos" e "Os estados tornam a tarefa de fundo observável", e `docs/generated/db-schema.md`, tabelas `source_document` e `document_chunk`.

## Escopo

- Função pura que divide um texto em chunks.
- Função que indexa um documento: lê da OCI, extrai o texto, divide, gera os embeddings e grava.
- Estados `processing`, `indexed` e `failed` do documento, com a mensagem de erro.

## Fora do escopo

- Percorrer os documentos de um curso e parar no primeiro erro (T28).
- Busca vetorial (T03, pronta).
- Ler PDF (T37). Este ticket só define como um texto com páginas vira chunks.
- Controle de ritmo dos pedidos ao Gemini. Veja a pendência.

## Contrato

### Módulos que este ticket usa

Copiados do `master`. Não edite esses módulos.

```python
# app.core.storage
class StorageError(Exception): ...


class ObjectNotFoundError(StorageError): ...


class Storage(Protocol):
    def get(self, key: str) -> bytes: ...


class InMemoryStorage: ...  # para os testes


# app.core.llm
EMBEDDING_DIMENSIONS = 768


class LLMError(Exception): ...


class LLMNotConfiguredError(LLMError): ...


def embed_texts(
    texts: Sequence[str],
    *,
    task: Literal["document", "query"],
) -> list[list[float]]: ...


# app.services.documents
class DocumentError(ValueError):
    code: DocumentErrorCode
    message: str
    filename: str | None


@dataclass(frozen=True, slots=True)
class ExtractedDocument:
    filename: str
    extension: str
    mime_type: str
    size_bytes: int
    sha256: str
    text: str


def read_document(filename: str, data: bytes) -> ExtractedDocument: ...


# app.core.config
settings.GEMINI_EMBEDDING_MODEL  # str, padrão "gemini-embedding-2"

# app.models
SourceDocument, DocumentChunk, DocumentStatus
```

### Módulo que este ticket cria

Em `backend/app/services/indexing.py`:

```python
CHUNK_SIZE = 1000
PAGE_BREAK = "\f"


@dataclass(frozen=True, slots=True)
class TextChunk:
    index: int  # a partir de 0
    text: str
    page_number: int | None  # a partir de 1, ou None sem páginas


class DocumentNotFoundError(LookupError): ...


class IndexingError(Exception):
    """A mensagem é o texto gravado em `source_document.error_message`."""


def split_text(
    text: str,
    *,
    paged: bool = False,
    chunk_size: int = CHUNK_SIZE,
) -> list[TextChunk]: ...


def index_document(
    *,
    session: Session,
    storage: Storage,
    document_id: uuid.UUID,
) -> int: ...
```

Regras de `split_text`:

- Cada chunk tem de 1 a `chunk_size` caracteres, sem espaços nas pontas. Nenhum chunk é vazio.
- Os chunks não se sobrepõem. Juntos e em ordem, eles trazem todo o texto que não é espaço.
- O corte acontece no último limite que cabe no chunk, nesta ordem de preferência: parágrafo (`\n\n`), linha (`\n`), fim de frase (`. `, `? `, `! `) e espaço. Sem nenhum limite dentro de `chunk_size`, o corte é no caractere `chunk_size`.
- `index` começa em 0 e cresce de um em um.
- Com `paged=False`, `page_number` é `None` em todos os chunks e `PAGE_BREAK` conta como espaço.
- Com `paged=True`, `PAGE_BREAK` separa as páginas. A primeira página é a 1. Nenhum chunk atravessa duas páginas. Uma página sem texto não gera chunk, mas conta na numeração.
- Um texto vazio ou só com espaços devolve lista vazia.
- A mesma entrada devolve sempre a mesma saída.

T37 define que o texto de um PDF traz `PAGE_BREAK` entre as páginas. Os dois tickets seguem essa regra e nenhum depende do código do outro.

Regras de `index_document`:

1. Carrega o `SourceDocument`. Sem a linha, levanta `DocumentNotFoundError`.
2. Se o documento já está `indexed`, devolve o número de chunks dele e não faz mais nada.
3. Grava `status = processing` e `error_message = None`, com `commit`.
4. Lê o arquivo com `storage.get(document.oci_object_key)`.
5. Extrai o texto com `read_document(document.original_filename, data)`.
6. Divide com `split_text(text, paged=extracted.mime_type == "application/pdf")`.
7. Pede os vetores em uma só chamada: `embed_texts([chunk.text ...], task="document")`. `embed_texts` já divide em lotes.
8. Em uma transação: apaga os chunks antigos do documento, grava um `DocumentChunk` por chunk e grava `status = indexed` e `embedding_model = settings.GEMINI_EMBEDDING_MODEL`. Faz `commit`.
9. Devolve o número de chunks.

Cada `DocumentChunk` leva `document_id`, `course_id` do documento, `chunk_index`, `text`, `page_number` e `embedding`. `token_count` fica nulo.

Em qualquer falha dos passos 4 a 8, a função faz `rollback`, grava `status = failed` e `error_message`, faz `commit` e levanta `IndexingError` com a mesma mensagem. Nenhum chunk do documento fica gravado.

| Falha | Mensagem |
| --- | --- |
| `ObjectNotFoundError` ou outro `StorageError` | Não foi possível ler o documento `{nome}` no armazenamento. |
| `DocumentError` | `{nome}`: seguido de `DocumentError.message`. |
| O texto não gera nenhum chunk | `{nome}`: O arquivo não tem texto. |
| `LLMNotConfiguredError` | Não foi possível indexar o documento `{nome}`: a chave do Gemini não está configurada. |
| Outro `LLMError` | Não foi possível indexar o documento `{nome}`: o modelo de embeddings falhou. |
| Qualquer outra exceção | Não foi possível indexar o documento `{nome}`. |

`{nome}` é `document.original_filename`. O texto do documento nunca entra na mensagem nem no log.

A função faz os próprios `commit`. Quem chama entrega uma sessão sem mudanças pendentes.

## Detalhes técnicos

- Chame o Gemini pelo módulo: `from app.core import llm` e `llm.embed_texts(...)`. Os testes trocam `app.core.llm.embed_texts` com `monkeypatch.setattr`, e um `from app.core.llm import embed_texts` escaparia da troca. Faça o mesmo com `read_document`: importe o módulo `app.services.documents`.
- Não acrescente dependência. O divisor de texto é código próprio, sem biblioteca.
- Este ticket não edita `backend/app/models.py`, `backend/app/services/documents.py` nem `backend/pyproject.toml`. T37 edita `documents.py` na mesma onda.
- O hook gera o cliente do frontend de novo. O OpenAPI não muda, então `frontend/src/client/` não pode aparecer no diff.
- Nos testes, crie o curso com `tests.utils.course.create_course`, com um documento `uploaded` e sem chunks: `documents=[{"original_filename": "guia.md", "status": "uploaded", "chunks": []}]`. Grave os bytes do arquivo em um `InMemoryStorage`, na chave `oci_object_key` do documento.
- Nenhum teste chama o Gemini nem a OCI. A função falsa de embeddings devolve um vetor de 768 valores por texto.

Pendência: T12 não está feito. Os limites do plano gratuito do Gemini não foram medidos. Este ticket não espera entre os pedidos nem limita o número de chunks. Um documento de 150 mil caracteres gera cerca de 150 chunks e 8 pedidos de embeddings. Se T12 mostrar que isso não cabe no plano, o controle de ritmo entra em `app.core.llm`, e o contrato deste ticket não muda. Por isso este ticket não espera T12.

Decisão: `docs/ARCHITECTURE.md` fala em chunks de cerca de 1.000 caracteres e não fala em sobreposição. Este ticket não sobrepõe chunks. O corte cai em fim de parágrafo ou de frase, então poucas ideias ficam divididas. A equipe revê a decisão com a medida da busca (T30).

## Critérios de aceite

- [ ] `split_text` e `index_document` cumprem o contrato.
- [ ] Um documento indexado tem os chunks, o estado `indexed` e o `embedding_model` gravados na mesma transação.
- [ ] Um documento que falha fica `failed`, com a mensagem, e sem nenhum chunk.
- [ ] Nenhum teste chama o Gemini nem a OCI.
- [ ] Os hooks e os testes passam, com cobertura de 90% ou mais.

## Cenários de teste

`split_text`:

1. Um texto de 300 caracteres devolve um chunk, com `index` 0 e `page_number` nulo.
2. Um texto de 2.500 caracteres com parágrafos de 400 devolve chunks de até 1.000 caracteres, cortados em fim de parágrafo.
3. Um texto de 2.500 caracteres sem nenhum espaço devolve chunks de 1.000, 1.000 e 500 caracteres.
4. Um parágrafo de 1.500 caracteres com frases curtas é cortado em fim de frase.
5. Os chunks juntos, sem espaços, são iguais ao texto original sem espaços.
6. Texto vazio e texto só com espaços devolvem lista vazia.
7. Com `paged=True`, `"A\fB"` devolve dois chunks, nas páginas 1 e 2. `"A\f\fC"` devolve dois chunks, nas páginas 1 e 3.
8. Com `paged=False`, `"A\fB"` devolve um chunk, com `page_number` nulo.
9. `chunk_size=50` vale no lugar do padrão.

`index_document`, com `InMemoryStorage` e `embed_texts` trocada:

10. Um documento `uploaded` de 2.500 caracteres fica `indexed`, com `embedding_model` igual à configuração. Os chunks têm `chunk_index` de 0 em diante, o `course_id` do documento e vetores de 768 valores. A função devolve o número de chunks.
11. A função falsa de embeddings recebe todos os chunks em uma chamada, com `task="document"`.
12. Um segundo `index_document` no mesmo documento não chama `embed_texts` e devolve o mesmo número.
13. Sem o objeto no armazenamento, o documento fica `failed`, com a mensagem de armazenamento, e a função levanta `IndexingError`.
14. Com bytes que não são UTF-8, o documento fica `failed`, com o nome do arquivo e "Não foi possível ler o arquivo como texto."
15. Com `embed_texts` levantando `LLMNotConfiguredError`, a mensagem fala da chave. Com `LLMError`, fala do modelo de embeddings. Nos dois casos, o documento não tem chunks.
16. Um documento `failed` com um chunk antigo é indexado de novo: fica `indexed`, sem o chunk antigo e sem `error_message`.
17. Com `read_document` trocada por uma função que devolve `mime_type` `application/pdf` e o texto `"A\fB"`, os chunks têm `page_number` 1 e 2.
18. Um `document_id` que não existe levanta `DocumentNotFoundError`.
19. Uma falha no `commit` do passo 8 deixa o documento `failed` e sem chunks.
