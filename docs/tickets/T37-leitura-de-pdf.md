---
id: T37
title: Leia documentos PDF com texto
blocked_by: [T16]
touches:
  - backend/pyproject.toml
  - uv.lock
  - backend/app/services/documents.py
  - backend/tests/services/test_documents.py
executor: agente
size: 2
---

# T37 - Leia documentos PDF com texto

## Contexto

`docs/product-specs/criar-curso.md` aceita arquivos `.md`, arquivos PDF com texto e texto digitado. T16 entregou a leitura de `.md` em `backend/app/services/documents.py`, com um leitor por extensão em `_READERS`. Um `.pdf` hoje é recusado como tipo não aceito.

Este ticket acrescenta o leitor de PDF. A API de criação de curso (T23) e a indexação (T19) chamam `read_documents` e `read_document` e passam a aceitar PDF sem mudança no código delas.

Leia antes: `docs/product-specs/criar-curso.md`, seções "O que a pessoa informa" e "Erros que a pessoa pode ver", e `backend/app/services/documents.py`.

## Escopo

- Leitor de PDF em `documents.py`, com o texto de cada página.
- Erros de PDF sem texto e de PDF que não abre.
- Dependência `pypdf`.

## Fora do escopo

- Reconhecer texto em imagem (OCR) e ler diagramas. `docs/ARCHITECTURE.md` deixa fora.
- Dividir o texto em chunks e gravar o número da página (T19).
- Aceitar PDF na tela "Novo curso" (T07).

## Contrato

As assinaturas de `read_document` e `read_documents` e os campos de `ExtractedDocument` não mudam. Copiados do `master`:

```python
@dataclass(frozen=True, slots=True)
class ExtractedDocument:
    filename: str
    extension: str
    mime_type: str
    size_bytes: int
    sha256: str
    text: str


def read_document(filename: str, data: bytes) -> ExtractedDocument: ...


def read_documents(files: Sequence[tuple[str, bytes]]) -> list[ExtractedDocument]: ...
```

Este ticket muda três pontos de `backend/app/services/documents.py`:

```python
PAGE_BREAK = "\f"


class DocumentErrorCode(StrEnum):
    ...
    unreadable = "unreadable"  # novo valor, depois de `count`


_READERS = {
    "md": _Reader("text/markdown", _read_markdown),
    "pdf": _Reader("application/pdf", _read_pdf),
}
```

Regras para um arquivo `.pdf`, sem diferenciar maiúsculas na extensão:

- `extension` é `"pdf"` e `mime_type` é `"application/pdf"`. `sha256` e `size_bytes` vêm dos bytes originais.
- `text` traz o texto de todas as páginas, em ordem, com `PAGE_BREAK` entre uma página e a seguinte. Um PDF de 3 páginas tem 2 `PAGE_BREAK`. Uma página sem texto entra como texto vazio, para a numeração das páginas se manter.
- Um `PAGE_BREAK` dentro do texto de uma página vira `\n`.
- O limite de 5 MiB vale antes de abrir o PDF, como no `.md`. O limite de 150 mil caracteres vale para o texto extraído.

T19 define que, em um texto de PDF, `PAGE_BREAK` separa as páginas e a primeira é a página 1. Os dois tickets seguem essa regra e nenhum depende do código do outro.

Erros novos de `read_document`, com `DocumentError.filename` preenchido:

| Condição | Código | Mensagem |
| --- | --- | --- |
| O PDF abre e nenhuma página tem texto | `empty` | Este PDF não tem texto. Envie um PDF com texto. |
| O arquivo não abre como PDF, está corrompido ou pede senha | `unreadable` | Não foi possível ler o arquivo como texto. |

O erro de PDF sem texto sai do leitor de PDF, antes da conferência geral de arquivo vazio, para a pessoa receber a mensagem do PDF e não "O arquivo não tem texto."

A mensagem de tipo não aceito não muda: "Envie um arquivo .md ou PDF, ou digite o texto."

Pendência: `criar-curso.md` não traz mensagem para um PDF corrompido ou com senha. Este ticket usa a mensagem do Markdown que não é UTF-8, "Não foi possível ler o arquivo como texto.", com o código novo `unreadable`. A equipe decide se quer uma mensagem própria.

## Detalhes técnicos

- Use `pypdf`. Em `backend/pyproject.toml`, acrescente `pypdf` como última linha da lista `dependencies`, depois de `oci`, com a versão estável mais recente como mínimo e a próxima versão maior como teto. Nenhum outro ticket da onda edita esse arquivo.
- `uv.lock` é gerado. Rode `uv lock`. Em um conflito, faça `rebase` no `master` e rode `uv lock` de novo. Nunca junte as duas versões à mão.
- O projeto usa Python 3.14. Se `pypdf` não instalar nessa versão, pare e relate.
- Confira os nomes das chamadas na documentação da versão instalada.
- Capture qualquer exceção do `pypdf` ao abrir o arquivo e ao extrair o texto, e levante `DocumentError` sem causa encadeada. O texto do documento nunca entra na mensagem nem no log.
- Não mude `_read_markdown`, `_clean_text` nem a ordem das conferências de `read_document`. `_clean_text` mantém o `PAGE_BREAK`.
- Só `documents.py` importa `pypdf`. O módulo continua sem importar banco, OCI e Gemini.
- T19 e T23 usam `documents.py` na mesma onda e não o editam.
- Monte os PDFs de teste em bytes, dentro do teste. Não guarde arquivo binário no repositório e não acrescente dependência para criar PDF. Um PDF mínimo escrito à mão, com um fluxo de texto por página, basta para as páginas com texto. `pypdf.PdfWriter` cria páginas em branco e PDF com senha.
- Em `backend/tests/services/test_documents.py`, o cenário 2 de T16 espera que `guia.pdf` levante `unsupported_type`. Tire `guia.pdf` desse teste e mantenha `guia.txt` e `guia`.
- O hook gera o cliente do frontend de novo. O OpenAPI não muda, então `frontend/src/client/` não pode aparecer no diff.

## Critérios de aceite

- [ ] Um PDF com texto devolve o texto das páginas, separado por `PAGE_BREAK`.
- [ ] Um PDF sem texto e um PDF que não abre recebem o código e a mensagem do contrato.
- [ ] Os testes de `.md` de T16 passam, com o ajuste do cenário 2.
- [ ] Só `documents.py` importa `pypdf`.
- [ ] Os hooks e os testes passam, com cobertura de 90% ou mais.

## Cenários de teste

Em `backend/tests/services/test_documents.py`:

1. Um PDF de uma página com texto devolve o texto, extensão `pdf`, `application/pdf`, o `sha256` e o tamanho dos bytes, e nenhum `PAGE_BREAK`.
2. Um PDF de 3 páginas com texto devolve os três textos em ordem, com 2 `PAGE_BREAK`.
3. Um PDF de 3 páginas com a segunda em branco devolve `"A\f\fC"`, sem contar espaços e quebras de linha das pontas de cada página.
4. `GUIA.PDF` é aceito.
5. Um PDF só com páginas em branco levanta `empty`, com "Este PDF não tem texto. Envie um PDF com texto." e o nome do arquivo.
6. Bytes que não são um PDF, com o nome `guia.pdf`, levantam `unreadable`, com "Não foi possível ler o arquivo como texto."
7. Um PDF com senha levanta `unreadable`.
8. Um arquivo `.pdf` com 5 MiB mais 1 byte levanta `too_large`, sem abrir o PDF.
9. Um PDF cujo texto passa de 150 mil caracteres levanta `too_long`. Troque o leitor por uma função que devolve o texto longo.
10. `read_documents` com um `.md` e um `.pdf` devolve os dois, e com o mesmo PDF duas vezes levanta `duplicate`.
11. `guia.txt` e `guia` continuam levantando `unsupported_type`.
