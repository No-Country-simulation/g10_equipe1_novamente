---
id: T15
title: Crie o módulo de acesso ao Gemini para embeddings e texto estruturado
blocked_by: []
touches:
  - backend/pyproject.toml
  - uv.lock
  - .env.example
  - backend/app/core/config.py
  - backend/app/core/llm.py
  - backend/tests/core/__init__.py
  - backend/tests/core/test_llm.py
executor: agente
size: 3
---

# T15 - Crie o módulo de acesso ao Gemini para embeddings e texto estruturado

## Contexto

A indexação precisa de embeddings, e os agentes `escreve` e `revisa` precisam de texto em JSON validado. Nenhum código fala com o Gemini hoje.

`docs/ARCHITECTURE.md` define que só `backend/app/core/llm.py` chama a API Gemini, que a chave é opcional e que nenhum teste automático chama a API. A indexação (T19), os agentes (T20, T21, T25, T26) e a tarefa de fundo (T28) usam este módulo.

Este ticket está no caminho mais longo do projeto. Revise e faça o merge dele primeiro.

Leia antes: `docs/ARCHITECTURE.md`, seção "Modelos de IA".

## Escopo

- Duas funções: embeddings em lote e geração de texto com schema.
- Configurações e dependência `google-genai`.
- Nova tentativa em erro temporário.

## Fora do escopo

- Prompts (T20, T21).
- Escolher o modelo de texto e medir limites (T12).
- Contagem de tokens e controle de custo.

## Contrato

Em `backend/app/core/llm.py`:

```python
EMBEDDING_DIMENSIONS = 768


class LLMError(Exception): ...


class LLMNotConfiguredError(LLMError): ...


class LLMInvalidResponseError(LLMError): ...


def embed_texts(
    texts: Sequence[str],
    *,
    task: Literal["document", "query"],
) -> list[list[float]]: ...


def generate_structured[T: BaseModel](
    *,
    system_instruction: str,
    prompt: str,
    response_model: type[T],
    temperature: float = 0.2,
) -> T: ...
```

Regras de `embed_texts`:

- Devolve um vetor de 768 valores por texto, na mesma ordem.
- Uma lista vazia devolve lista vazia, sem chamar a API.
- Divide a lista em lotes de `EMBED_BATCH_SIZE` textos. Comece com 20. T12 mede o limite real.
- `task` escolhe o tipo de tarefa da API: documento para os chunks, consulta para o `focus`.
- Um vetor com tamanho diferente de 768 levanta `LLMInvalidResponseError`.

Regras de `generate_structured`:

- Pede JSON com o schema de `response_model` e devolve a instância validada.
- Uma resposta vazia, que não é JSON ou que não passa na validação levanta `LLMInvalidResponseError`. O módulo não tenta de novo nesse caso. Quem decide a reescrita é o grafo de geração (T24).

Regras comuns:

- Sem `GEMINI_API_KEY`, as duas funções levantam `LLMNotConfiguredError`. `generate_structured` também levanta esse erro sem `GEMINI_GENERATION_MODEL`.
- Em erro temporário da API (limite de pedidos ou serviço indisponível), o módulo tenta de novo até 3 vezes, com espera crescente. Depois disso, levanta `LLMError`.
- Qualquer outra falha da API vira `LLMError`.
- O texto do documento e a resposta do modelo nunca entram em mensagem de erro nem em log. O log traz o modelo, o número de textos e o tempo.

Os testes de outros tickets trocam `app.core.llm.embed_texts` e `app.core.llm.generate_structured` por funções determinísticas. Nenhum código fora deste módulo importa o SDK do Gemini.

### Configurações

| Variável | Tipo | Padrão |
| --- | --- | --- |
| `GEMINI_API_KEY` | `str \| None` | `None` |
| `GEMINI_EMBEDDING_MODEL` | `str` | `"gemini-embedding-2"` |
| `GEMINI_GENERATION_MODEL` | `str \| None` | `None` |

O padrão de `GEMINI_EMBEDDING_MODEL` é igual ao padrão da coluna `source_document.embedding_model`.

## Detalhes técnicos

T14 altera os mesmos três arquivos na mesma onda. Insira as linhas nestes pontos, para os dois PRs se juntarem sem conflito:

- `backend/pyproject.toml`: acrescente `google-genai` logo depois da linha de `pydantic-settings`.
- `backend/app/core/config.py`: acrescente o bloco de variáveis logo depois de `EMAIL_TEST_USER`.
- `.env.example`: acrescente um bloco `# Gemini` logo depois da linha `SECRET_KEY=changethis`, com as variáveis comentadas.

`uv.lock` é gerado. Se o PR conflitar nele, faça `rebase` e rode `uv lock`.

Outros pontos:

- Use o SDK `google-genai`. Confira os nomes das chamadas e dos parâmetros na documentação da versão instalada. Não confie na memória: o SDK muda com frequência.
- O projeto usa Python 3.14. Se o SDK não instalar nessa versão, pare e relate.
- Crie o cliente na primeira chamada, não na importação. O backend precisa subir sem chave.
- Receba a função de espera como parâmetro interno, ou troque-a no teste. Nenhum teste dorme de verdade.
- Teste com um cliente falso. Nenhum teste chama a API.
- Alguns limites de schema, como número mínimo de itens, podem não ser aceitos pela API. Se a API recusar o schema de um modelo, envie o schema sem esses limites e valide a resposta com o modelo completo. Relate no PR.

## Critérios de aceite

- [ ] As duas funções cumprem o contrato.
- [ ] O backend sobe e os testes passam sem nenhuma variável `GEMINI_*`.
- [ ] Só `backend/app/core/llm.py` importa o SDK.
- [ ] `.env.example` documenta as variáveis sem nenhum valor secreto.
- [ ] Os hooks e os testes passam, com cobertura de 90% ou mais.
- [ ] Se você tiver uma chave, rode uma chamada real de cada função e relate o resultado no PR. Sem chave, diga que não rodou.

## Cenários de teste

1. `embed_texts` com 45 textos faz 3 chamadas ao cliente falso e devolve 45 vetores na ordem.
2. `embed_texts` com lista vazia não chama o cliente.
3. Um vetor de 767 valores levanta `LLMInvalidResponseError`.
4. `task="document"` e `task="query"` chegam ao cliente como tipos de tarefa diferentes.
5. `generate_structured` devolve a instância de `response_model` para um JSON válido.
6. Resposta vazia, texto que não é JSON e JSON fora do schema levantam `LLMInvalidResponseError`, com uma só chamada ao cliente.
7. Dois erros temporários seguidos de sucesso devolvem o resultado, com 3 chamadas.
8. Quatro erros temporários levantam `LLMError`.
9. Sem chave, as duas funções levantam `LLMNotConfiguredError`. Sem modelo de texto, `generate_structured` também.
10. A mensagem de erro e o log não trazem o texto enviado.
