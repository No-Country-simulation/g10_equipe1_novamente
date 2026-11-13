---
id: T14
title: Crie o módulo de armazenamento de objetos na OCI
blocked_by: []
touches:
  - backend/pyproject.toml
  - uv.lock
  - .env.example
  - backend/app/core/config.py
  - backend/app/core/storage.py
  - backend/scripts/verify_storage.py
  - backend/tests/core/__init__.py
  - backend/tests/core/test_storage.py
executor: agente
size: 3
---

# T14 - Crie o módulo de armazenamento de objetos na OCI

## Contexto

O briefing exige que os documentos originais e os JSON gerados fiquem no OCI Object Storage. Nenhum código fala com a OCI hoje.

`docs/ARCHITECTURE.md` define que só `backend/app/core/storage.py` chama o OCI Python SDK, e que os testes e o CI usam uma versão em memória, sem credenciais. A criação de curso (T23), a indexação (T19), a publicação (T22) e a exclusão (T33) usam este módulo.

Leia antes: `docs/ARCHITECTURE.md`, seções "Armazenamento de objetos" e "O banco e o armazenamento de objetos dividem os dados".

## Escopo

- Interface de armazenamento com quatro operações.
- Implementação na OCI e implementação em memória.
- Funções que montam as chaves dos objetos.
- Configurações e dependência `oci`.
- Script de verificação contra o bucket real.

## Fora do escopo

- Usar o módulo em rotas ou na tarefa de fundo (T19, T22, T23).
- Criar o bucket e as chaves (T12).
- Link temporário de download. O bucket é privado e a API lê do banco.

## Contrato

Em `backend/app/core/storage.py`:

```python
class StorageError(Exception): ...


class StorageNotConfiguredError(StorageError): ...


class ObjectNotFoundError(StorageError): ...


class Storage(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> None: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...
    def list(self, prefix: str) -> list[str]: ...


class OCIStorage:  # implementa Storage com o OCI Python SDK
    ...


class InMemoryStorage:  # implementa Storage com um dicionário
    ...


def get_storage() -> Storage: ...


StorageDep = Annotated[Storage, Depends(get_storage)]


def document_key(
    course_id: uuid.UUID, document_id: uuid.UUID, extension: str
) -> str: ...
def content_key(course_id: uuid.UUID, content_id: uuid.UUID) -> str: ...
def course_prefix(course_id: uuid.UUID) -> str: ...
```

Regras:

- `put` substitui um objeto que já existe.
- `get` de uma chave inexistente levanta `ObjectNotFoundError`.
- `delete` de uma chave inexistente não levanta erro. A limpeza pode rodar duas vezes.
- `list` devolve todas as chaves com o prefixo, em ordem alfabética. Na OCI, ela lê todas as páginas do resultado.
- Qualquer outra falha do SDK vira `StorageError`, com a operação e a chave na mensagem. O conteúdo do objeto nunca entra na mensagem nem no log.
- `get_storage` devolve um `OCIStorage` montado com as configurações, e reusa a mesma instância. Sem `OCI_BUCKET` ou `OCI_NAMESPACE`, levanta `StorageNotConfiguredError`.
- As chaves seguem `docs/ARCHITECTURE.md`:
    - `document_key`: `courses/{course_id}/documents/{document_id}.{extension}`, com a extensão sem ponto.
    - `content_key`: `courses/{course_id}/contents/{content_id}/{uuid}.json`, com um UUID novo a cada chamada.
    - `course_prefix`: `courses/{course_id}/`.

Os testes de outros tickets trocam o armazenamento com `app.dependency_overrides[get_storage]` e um `InMemoryStorage`. A tarefa de fundo recebe a instância de quem a agenda. Nenhum código fora deste módulo importa `oci`.

### Configurações

Em `Settings`, todas opcionais, para o backend subir sem OCI:

| Variável | Tipo | Padrão |
| --- | --- | --- |
| `OCI_BUCKET` | `str \| None` | `None` |
| `OCI_NAMESPACE` | `str \| None` | `None` |
| `OCI_AUTH` | `"api_key"` ou `"instance_principal"` | `"api_key"` |
| `OCI_CONFIG_FILE` | `str` | `"~/.oci/config"` |
| `OCI_CONFIG_PROFILE` | `str` | `"DEFAULT"` |

Com `api_key`, o cliente lê o arquivo de configuração da OCI, que fica fora do repositório. Com `instance_principal`, o cliente usa a identidade da VM e nenhuma chave.

## Detalhes técnicos

T15 altera os mesmos três arquivos na mesma onda. Insira as linhas nestes pontos, para os dois PRs se juntarem sem conflito:

- `backend/pyproject.toml`: acrescente `oci` como última linha da lista `dependencies`, depois de `pgvector`.
- `backend/app/core/config.py`: acrescente o bloco de variáveis logo depois da linha `FASTAPI_ENV`, antes de `PROJECT_NAME`.
- `.env.example`: acrescente um bloco `# OCI Object Storage` no fim do arquivo, com as variáveis comentadas.

`uv.lock` é gerado. Se o PR conflitar nele, faça `rebase` e rode `uv lock`.

Outros pontos:

- O projeto usa Python 3.14. Se `oci` não instalar nessa versão, pare e relate.
- O `mypy` roda em modo estrito e o `oci` não traz tipos. Se for preciso, acrescente um bloco `[[tool.mypy.overrides]]` para `oci.*` logo depois do bloco `[tool.mypy]`. O `ty` também precisa passar.
- Teste `OCIStorage` com um cliente falso no lugar de `ObjectStorageClient`. O CI não tem credenciais da OCI.
- `backend/scripts/verify_storage.py` envia, lê, lista e apaga um objeto com prefixo `verify/` no bucket configurado, e imprime o resultado de cada passo. O script fica fora de `backend/app`, então pode usar `print` e não entra na cobertura. Rode-o se você tiver credenciais. Sem credenciais, diga no PR que o script não foi executado.

## Critérios de aceite

- [ ] `OCIStorage` e `InMemoryStorage` cumprem as mesmas regras do contrato.
- [ ] O backend sobe e os testes passam sem nenhuma variável `OCI_*`.
- [ ] Só `backend/app/core/storage.py` importa `oci`.
- [ ] `.env.example` documenta as variáveis sem nenhum valor secreto.
- [ ] Os hooks e os testes passam, com cobertura de 90% ou mais.

## Cenários de teste

Rode os cenários 1 a 4 contra as duas implementações.

1. `put` seguido de `get` devolve os mesmos bytes. Um segundo `put` na mesma chave substitui o conteúdo.
2. `get` de chave inexistente levanta `ObjectNotFoundError`.
3. `delete` apaga o objeto, e um segundo `delete` não levanta erro.
4. `list` devolve só as chaves do prefixo, em ordem.
5. `OCIStorage.list` junta duas páginas do cliente falso.
6. Um erro 404 do SDK vira `ObjectNotFoundError`, e um erro 500 vira `StorageError`.
7. `get_storage` sem configuração levanta `StorageNotConfiguredError`.
8. As três funções de chave devolvem o formato do contrato, e duas chamadas de `content_key` devolvem chaves diferentes.
