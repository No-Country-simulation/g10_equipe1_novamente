---
id: T23
title: Exponha a criação de curso, com validação e gravação dos documentos na OCI
blocked_by: [T02, T14, T16]
touches:
  - backend/app/api/routes/courses.py
  - backend/app/main.py
  - backend/tests/api/routes/test_courses_create.py
  - frontend/src/client/
executor: agente
size: 3
---

# T23 - Exponha a criação de curso, com validação e gravação dos documentos na OCI

## Contexto

`docs/ARCHITECTURE.md` define os passos 1 a 3 da criação de um curso: a pessoa envia título, setor, nível, arquivos e saídas para `POST /api/v1/courses/`. A API valida tudo antes de gravar, grava cada arquivo na OCI e cria, em uma transação, o curso, os documentos e os conteúdos. Hoje só a rota de seed cria cursos.

Este ticket entrega a rota. A tela "Novo curso" (T27) envia o formulário para ela. A tarefa de fundo (T28) passa a ser agendada por ela.

Leia antes: `docs/product-specs/criar-curso.md`, `docs/ARCHITECTURE.md`, seção "A criação de um curso segue doze passos", e `backend/app/api/routes/courses.py`.

## Escopo

- Rota `POST /api/v1/courses/`, com formulário `multipart/form-data`.
- Validação do título, das saídas, dos documentos e do setor, com as mensagens da especificação.
- Gravação dos arquivos na OCI e das linhas no banco.
- Limpeza dos arquivos se a gravação falha.
- Resposta HTTP 503 para falha do armazenamento.

## Fora do escopo

- Agendar a tarefa de fundo (T28). Até T28, um curso criado fica em "Gerando".
- Indexar os documentos (T19) e gerar os conteúdos.
- Ler PDF (T37). A rota aceita o que `read_documents` aceita.
- Tela "Novo curso" (T07 e T27).
- Limite de cursos por usuário. `escopo-do-mvp.md` diz que o código ainda não o impõe.

## Contrato

### Módulos que este ticket usa

Copiados do `master`. Não edite esses módulos.

```python
# app.core.storage
class StorageError(Exception): ...


class StorageNotConfiguredError(StorageError): ...


class Storage(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> None: ...
    def delete(self, key: str) -> None: ...


class InMemoryStorage: ...  # para os testes


def get_storage() -> Storage: ...


StorageDep = Annotated[Storage, Depends(get_storage)]


def document_key(
    course_id: uuid.UUID, document_id: uuid.UUID, extension: str
) -> str: ...


# app.services.documents
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_DOCUMENTS = 3


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


def read_documents(files: Sequence[tuple[str, bytes]]) -> list[ExtractedDocument]: ...


# app.api.routes.courses
def read_course(
    *, session: SessionDep, current_user: CurrentUser, course_id: uuid.UUID
) -> CourseDetail: ...


# app.api.deps
SessionDep, CurrentUser

# app.models
Course, SourceDocument, CourseContent, Niche, CourseDetail
AudienceLevel, ContentFormat, CourseStatus, DocumentStatus, GenerationStatus
```

### Rota que este ticket cria

`POST /api/v1/courses/`, com login. A função da rota se chama `create_course`, para o cliente gerado expor `CoursesService.createCourse`.

Corpo `multipart/form-data`. T27 é escrito contra estes nomes:

| Campo | Tipo | Regra |
| --- | --- | --- |
| `title` | texto | De 1 a 255 caracteres, depois de tirar os espaços das pontas. |
| `niche_id` | inteiro | `id` de um setor de `GET /api/v1/niches/`. |
| `audience_level` | `AudienceLevel` | `non_technical`, `technical_basic` ou `technical_advanced`. |
| `formats` | `ContentFormat`, campo repetido | De 1 a 3 valores, sem repetição. A ordem dos campos é a ordem das saídas. |
| `files` | arquivo, campo repetido | De 1 a 3 arquivos. |

Resposta de sucesso: HTTP 201, com um `CourseDetail`, igual ao de `GET /api/v1/courses/{course_id}`.

Toda resposta de erro desta tabela traz `{"detail": "<mensagem>"}`, com a mensagem em texto. A rota confere nesta ordem e responde no primeiro problema:

| Ordem | Condição | Resposta | Mensagem |
| --- | --- | --- | --- |
| 1 | `title` ausente, vazio ou só com espaços | 422 | Informe um título. |
| 2 | `title` com mais de 255 caracteres | 422 | O título passa de 255 caracteres. |
| 3 | Nenhum arquivo ou nenhuma saída | 422 | Envie pelo menos um documento e escolha pelo menos uma saída. |
| 4 | Mais de 3 arquivos ou mais de 3 saídas | 422 | Envie até 3 documentos e escolha até 3 saídas. |
| 5 | Duas saídas do mesmo formato | 422 | Escolha só uma saída de cada formato. |
| 6 | `read_documents` levanta `DocumentError` | 422 | `DocumentError.message`. Com `DocumentError.filename`, a mensagem vem depois do nome: `guia.txt: Envie um arquivo .md ou PDF, ou digite o texto.` |
| 7 | Nenhum setor com `niche_id` | 404 | Setor não encontrado. |

Um `audience_level`, um `formats` ou um `niche_id` com valor que não é do tipo recebe o HTTP 422 padrão do FastAPI, com `detail` em lista. Sem login, a rota responde como as outras rotas de curso.

A validação termina antes de qualquer gravação. Depois dela:

1. A rota gera o `id` do curso e o `id` de cada documento.
2. Grava cada arquivo: `storage.put(document_key(course_id, document_id, extension), data, mime_type)`, com os bytes originais.
3. Em uma transação, cria:
    - um `Course`, com `owner_id` do usuário, `niche_id`, o título sem espaços nas pontas, `audience_level` e `status = initializing`;
    - um `SourceDocument` por arquivo, na ordem recebida, com `title` e `original_filename` iguais a `ExtractedDocument.filename`, `mime_type`, `size_bytes`, `sha256`, `oci_object_key` igual à chave do passo 2 e `status = uploaded`;
    - um `CourseContent` por saída, com `format`, `position` de 0 em diante na ordem recebida, `focus` igual ao título do curso e `status = pending`.
4. Faz `commit` e responde com `read_course`.

Se um `put` ou o `commit` falha, a rota faz `rollback`, apaga com `storage.delete` cada objeto já gravado e deixa o erro subir. Nenhuma linha e nenhum objeto do curso ficam gravados. Uma falha de `delete` na limpeza vai para o log, com o `course_id`, e não troca o erro original.

### Falha do armazenamento

Em `backend/app/main.py`, registre um tratador de exceção para `StorageError`. Ele responde HTTP 503, com `{"detail": "O armazenamento de arquivos não está disponível. Tente novamente mais tarde."}`, e registra no log o tipo do erro. O tratador cobre também `StorageNotConfiguredError`, que `get_storage` levanta sem `OCI_BUCKET` ou `OCI_NAMESPACE`.

Decisão: `criar-curso.md` traz as mensagens desta rota, incluindo "O título passa de 255 caracteres.", o nome do arquivo antes da mensagem de um documento recusado e a mensagem do HTTP 503 acima.

Decisão: o campo do setor é `niche_id`, o `id` que `GET /api/v1/niches/` devolve. A tela sempre escolhe o setor dessa lista. A rota de seed continua com `niche_slug`.

## Detalhes técnicos

- Acrescente a rota no fim de `backend/app/api/routes/courses.py`, depois de `read_course`. Não mude as rotas de leitura. Nenhum outro ticket da onda edita esse arquivo.
- Em `backend/app/main.py`, acrescente o tratador logo depois do bloco `app.add_middleware(...)` e antes de `app.include_router(...)`. Nenhum outro ticket da onda edita esse arquivo.
- Não edite `backend/app/models.py`, `backend/app/api/main.py`, `backend/app/api/routes/private.py` nem `backend/app/services/documents.py`. A rota não precisa de schema novo: a entrada é um formulário e a saída é `CourseDetail`.
- Declare `title`, `formats` e `files` com valor padrão, para a rota responder com as mensagens da tabela quando o campo falta. Sem o padrão, o FastAPI responde com o HTTP 422 dele.
- Leia de cada arquivo no máximo `MAX_FILE_BYTES + 1` bytes: `file.file.read(MAX_FILE_BYTES + 1)`. `read_documents` recusa o arquivo que passa do limite, e a memória usada fica limitada. Um arquivo sem nome entra como nome vazio e cai em tipo não aceito.
- Use `status_code=201` e `response_model=CourseDetail`. Mantenha a rota síncrona (`def`), como as outras.
- `frontend/src/client/` é gerado. O hook `generate-frontend-sdk` roda `bash scripts/generate-client.sh` e o resultado entra no mesmo PR. Em um conflito, faça `rebase` no `master` e gere de novo. Nunca junte as duas versões à mão. Nenhum outro ticket da onda muda o OpenAPI.
- T37 acrescenta o PDF a `read_documents` na mesma onda. Nos testes de tipo não aceito, use `.txt`. Um teste que espera a recusa de `.pdf` quebra quando T37 entrar.
- Nos testes, troque o armazenamento com `app.dependency_overrides[get_storage]` e um `InMemoryStorage`, e desfaça a troca no fim. Nenhum teste chama a OCI.
- Crie os testes em um arquivo novo, `backend/tests/api/routes/test_courses_create.py`. Não edite `test_courses.py`.

## Critérios de aceite

- [ ] A rota cria o curso, os documentos e os conteúdos, e grava os arquivos na OCI.
- [ ] Cada erro da tabela responde com o código e a mensagem definidos, sem gravar nada.
- [ ] Uma falha no meio da gravação não deixa linha nem objeto.
- [ ] O backend sobe e os testes passam sem nenhuma variável `OCI_*`.
- [ ] O cliente gerado traz `CoursesService.createCourse`.
- [ ] Os hooks e os testes passam, com cobertura de 90% ou mais.

## Cenários de teste

Em `backend/tests/api/routes/test_courses_create.py`, com `InMemoryStorage`:

1. Um `guia.md` e `formats=tutorial`: HTTP 201. O curso está `initializing`, com o setor e o nível enviados. O documento está `uploaded`, com `text/markdown`, o tamanho e o nome. O conteúdo está `pending`, na posição 0.
2. No banco, `focus` do conteúdo é igual ao título, e `sha256` e `oci_object_key` do documento conferem com os bytes e com `document_key`. O objeto no armazenamento tem os bytes enviados.
3. Três arquivos e `formats` na ordem `quiz`, `tutorial`, `flashcards`: os conteúdos saem nas posições 0, 1 e 2, nessa ordem, e os três objetos estão no armazenamento.
4. `title` com espaços nas pontas é gravado sem eles. `GET /api/v1/courses/{id}` devolve o mesmo curso, e `GET /api/v1/courses/` o lista.
5. `title` ausente e `title` só com espaços: 422, "Informe um título." `title` com 256 caracteres: 422, com a mensagem do limite. Com 255, a rota aceita.
6. Sem `files` e sem `formats`: 422, "Envie pelo menos um documento e escolha pelo menos uma saída."
7. Quatro arquivos: 422, "Envie até 3 documentos e escolha até 3 saídas."
8. `formats=tutorial` duas vezes: 422, "Escolha só uma saída de cada formato."
9. `notas.txt`: 422, com o nome do arquivo e a mensagem de tipo. Arquivo vazio, arquivo com 5 MiB mais 1 byte e dois arquivos de mesmo conteúdo: 422, com a mensagem de cada caso.
10. `niche_id` que não existe: 404, "Setor não encontrado."
11. Em cada erro dos cenários 5 a 10, o armazenamento fica vazio e o usuário continua sem cursos.
12. `audience_level` inválido: 422.
13. Sem token, a rota responde com o mesmo código de `GET /api/v1/courses/` sem token.
14. Com um armazenamento cujo segundo `put` levanta `StorageError`: 503, com a mensagem do armazenamento. O primeiro objeto foi apagado e o usuário continua sem cursos.
15. Com uma falha no `commit`: o armazenamento fica vazio e o usuário continua sem cursos.
16. Sem a troca do armazenamento e sem variáveis `OCI_*`: 503, com a mensagem do armazenamento.
17. O curso criado por um usuário responde 404 para outro usuário.
