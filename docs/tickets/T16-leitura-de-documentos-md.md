---
id: T16
title: Leia e valide documentos `.md` antes de gravar qualquer dado
blocked_by: []
touches:
  - backend/app/services/__init__.py
  - backend/app/services/documents.py
  - backend/tests/services/__init__.py
  - backend/tests/services/test_documents.py
executor: agente
size: 2
---

# T16 - Leia e valide documentos `.md` antes de gravar qualquer dado

## Contexto

`docs/product-specs/criar-curso.md` define que a validação acontece antes de gravar qualquer arquivo ou linha, e lista a mensagem de cada erro. Nenhum código lê um documento hoje.

O primeiro caminho de ponta a ponta usa um arquivo `.md` (`docs/product-specs/escopo-do-mvp.md`). O texto digitado em um campo chega à API como um arquivo `.md`, criado pelo navegador, e passa pelo mesmo caminho. O PDF entra em T37.

A API de criação de curso (T23) chama este módulo para validar. A indexação (T19) chama para extrair o texto.

Leia antes: `docs/product-specs/criar-curso.md`, seções "O que a pessoa informa" e "Erros que a pessoa pode ver".

## Escopo

Funções puras que recebem o nome e os bytes de um arquivo e devolvem o texto e os metadados, ou um erro com a mensagem para a pessoa.

## Fora do escopo

- PDF (T37).
- Dividir o texto em chunks (T19).
- Rota de API e gravação na OCI (T23).
- Validar título, setor, nível e saídas (T23).

## Contrato

Em `backend/app/services/documents.py`:

```python
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TEXT_CHARS = 150_000
MAX_DOCUMENTS = 3


class DocumentErrorCode(StrEnum):
    unsupported_type = "unsupported_type"
    empty = "empty"
    too_large = "too_large"
    too_long = "too_long"
    not_utf8 = "not_utf8"
    duplicate = "duplicate"
    count = "count"


class DocumentError(ValueError):
    code: DocumentErrorCode
    message: str
    filename: str | None


@dataclass(frozen=True, slots=True)
class ExtractedDocument:
    filename: str
    extension: str  # "md"
    mime_type: str  # "text/markdown"
    size_bytes: int
    sha256: str  # 64 caracteres hexadecimais em minúsculas
    text: str


def read_document(filename: str, data: bytes) -> ExtractedDocument: ...


def read_documents(files: Sequence[tuple[str, bytes]]) -> list[ExtractedDocument]: ...
```

`read_document` confere nesta ordem e levanta `DocumentError` no primeiro problema:

| Ordem | Condição | Código | Mensagem |
| --- | --- | --- | --- |
| 1 | A extensão não é `.md`, sem diferenciar maiúsculas | `unsupported_type` | Envie um arquivo `.md` ou PDF, ou digite o texto. |
| 2 | O arquivo tem mais de 5 MiB | `too_large` | O arquivo passa de 5 MiB. |
| 3 | Os bytes não são UTF-8 | `not_utf8` | Não foi possível ler o arquivo como texto. |
| 4 | O texto é vazio ou só tem espaços | `empty` | O arquivo não tem texto. |
| 5 | O texto tem mais de 150 mil caracteres | `too_long` | O documento é longo demais. Envie um documento menor ou divida o arquivo. |

`read_documents` lê uma lista de arquivos e levanta `DocumentError` nestes casos:

| Condição | Código | Mensagem |
| --- | --- | --- |
| Lista vazia | `count` | Envie pelo menos um documento e escolha pelo menos uma saída. |
| Mais de 3 arquivos | `count` | Envie até 3 documentos e escolha até 3 saídas. |
| Dois arquivos com o mesmo `sha256` | `duplicate` | Este arquivo já está no curso. |

Outras regras:

- `sha256` e `size_bytes` vêm dos bytes originais. O banco tem uma restrição única em `(course_id, sha256)`.
- `text` é o conteúdo decodificado, sem a marca de ordem de bytes do início, com quebras de linha `\n` e sem caracteres nulos. O PostgreSQL recusa caracteres nulos em colunas de texto.
- `filename` guarda só o nome, sem pasta, com até 255 caracteres. A coluna `original_filename` tem esse limite.
- `DocumentError.filename` traz o nome do arquivo com problema, ou `None` nos erros de quantidade.
- As mensagens são as de `criar-curso.md`. Não mude a redação.

## Detalhes técnicos

- O módulo não importa banco, OCI nem Gemini.
- O limite de caracteres conta o texto depois da limpeza.
- T37 acrescenta o PDF neste mesmo módulo. Organize a escolha do leitor por extensão, para o PDF entrar sem reescrever o `.md`.

## Critérios de aceite

- [ ] As duas funções cumprem o contrato, com a ordem das conferências.
- [ ] Cada erro traz o código, a mensagem da especificação e o nome do arquivo.
- [ ] Nenhuma função grava em disco, banco ou rede.
- [ ] Os hooks e os testes passam, com cobertura de 90% ou mais.

## Cenários de teste

1. Um `.md` válido devolve texto, `sha256`, tamanho, extensão `md` e `text/markdown`.
2. `GUIA.MD` é aceito. `guia.txt`, `guia.pdf` e `guia` levantam `unsupported_type`.
3. Um arquivo com 5 MiB exatos passa no tamanho. Com um byte a mais, levanta `too_large`.
4. Bytes em Latin-1 com acento levantam `not_utf8`.
5. Arquivo vazio e arquivo só com espaços e quebras de linha levantam `empty`.
6. Um texto com 150.000 caracteres passa. Com 150.001, levanta `too_long`.
7. Um arquivo com marca de ordem de bytes, quebras `\r\n` e um caractere nulo devolve o texto limpo.
8. Um nome com pasta, como `pasta/guia.md`, devolve `guia.md`.
9. `read_documents` com zero e com quatro arquivos levanta `count`, com a mensagem de cada caso.
10. `read_documents` com dois arquivos de mesmo conteúdo e nomes diferentes levanta `duplicate`, com o nome do segundo arquivo.
11. `texto-digitado.md` segue as mesmas regras de qualquer `.md`.
