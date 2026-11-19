---
id: T39
title: Respeite os limites por minuto do Gemini no módulo `llm.py`
blocked_by: [T15]
touches:
  - backend/app/core/config.py
  - backend/app/core/llm.py
  - backend/tests/core/test_llm.py
  - .env.example
executor: agente
size: 2
---

# T39 - Respeite os limites por minuto do Gemini no módulo `llm.py`

## Contexto

T12 leu os limites do plano gratuito no Google AI Studio em 19/11/2026:

| Modelo | Pedidos por minuto | Tokens por minuto | Pedidos por dia |
| --- | ---: | ---: | ---: |
| `gemini-embedding-2` | 100 | 30.000 | 1.000 |
| `gemini-3.5-flash-lite` | 15 | 250.000 | 500 |

A cota de embeddings conta cada texto como um pedido, mesmo dentro de um lote. Uma chamada com 1 texto e outra com um lote de 20 apareceram no painel como 21 pedidos.

Hoje `embed_texts` envia todos os lotes em sequência, sem pausa. Em um HTTP 429, `_call_api` tenta de novo depois de 1, 2 e 4 segundos, 7 segundos no total, e a janela de um minuto não termina nesse tempo. Com `CHUNK_SIZE = 1000`, um documento com mais de cerca de 90 mil caracteres passa de 100 textos ou de 30 mil tokens no mesmo minuto, e a indexação (T19) falha com `LLMError`. O produto aceita até 150 mil caracteres por documento e até 3 documentos por curso.

Na geração, um curso com três saídas faz até 12 chamadas, e o limite é de 15 por minuto. A tarefa de fundo (T28) pode gerar os conteúdos em paralelo e passar desse limite.

Leia antes: `docs/ARCHITECTURE.md`, seção "Modelos de IA", e `docs/tickets/completed/T15-acesso-ao-gemini.md`.

## Escopo

- Um controle de ritmo por minuto antes de cada pedido, nas duas funções públicas.
- Espera longa em HTTP 429, no lugar das três esperas curtas.
- Três configurações com os limites por minuto.

## Fora do escopo

- A cota diária. Quando ela acaba, a função levanta `LLMError` com uma mensagem clara, como define o contrato abaixo.
- Contar tokens com uma chamada à API. A contagem é uma estimativa local.
- Coordenar vários processos do backend. Cada processo controla o próprio ritmo, e a espera em 429 cobre o excesso.
- Mudar `CHUNK_SIZE`, `EMBED_BATCH_SIZE` ou o limite de 150 mil caracteres.
- Mudar as assinaturas de `embed_texts` e `generate_structured`.

## Contrato

### Configurações

Em `backend/app/core/config.py`, ao lado das outras `GEMINI_*`:

```python
GEMINI_EMBEDDING_RPM: int = 100
GEMINI_EMBEDDING_TPM: int = 30_000
GEMINI_GENERATION_RPM: int = 15
```

Em `.env.example`, as três linhas comentadas com esses valores, depois de `GEMINI_GENERATION_MODEL`, e uma linha de comentário que diga que são os limites do plano gratuito lidos em 19/11/2026.

### Ritmo por minuto

Em `backend/app/core/llm.py`:

- Acrescente `_now: Callable[[], float] = time.monotonic` ao lado de `_sleep`. O controle de ritmo lê o tempo só por `_now` e espera só por `_sleep`, para os testes trocarem as duas.
- Crie um controle de ritmo para os embeddings e outro para a geração. Cada um é um objeto do módulo, compartilhado por todas as chamadas do processo e seguro entre threads (`threading.Lock`). Não segure o lock durante a espera.
- Cada controle guarda os pedidos dos últimos 60 segundos. Antes de enviar, ele soma o que está na janela com o pedido novo. Se a soma passa de um limite, ele espera até o pedido mais antigo sair da janela e confere de novo. Um pedido que sozinho passa do limite sai quando a janela estiver vazia, para não esperar para sempre.
- Embeddings: cada lote conta `len(batch)` pedidos e `sum(math.ceil(len(text) / 3) for text in batch)` tokens. Três caracteres por token é uma estimativa de propósito alta. Os limites são `GEMINI_EMBEDDING_RPM` e `GEMINI_EMBEDDING_TPM`.
- Geração: cada chamada conta 1 pedido, com o limite `GEMINI_GENERATION_RPM`. A geração não controla tokens.
- Toda tentativa passa pelo controle, inclusive as novas tentativas de `_call_api`, porque toda tentativa gasta cota.
- Uma espera de 1 segundo ou mais gera um log `INFO` com o tipo de pedido e a duração da espera. O log não traz texto enviado nem resposta.

### HTTP 429 e 503

- HTTP 503: sem mudança. Novas tentativas depois de 1, 2 e 4 segundos.
- HTTP 429: espere o `retryDelay` do detalhe `google.rpc.RetryInfo` do erro, quando ele existir. Sem esse detalhe, espere 60 segundos. Faça no máximo duas esperas dessas por chamada. Confira na versão instalada do `google-genai` onde `errors.APIError` guarda os detalhes.
- Depois da segunda espera, um novo 429 levanta `LLMError("A API Gemini recusou o pedido por limite de uso (429). Tente de novo mais tarde.")`, sem causa encadeada, como os outros erros do módulo.

## Regras

- Só `backend/app/core/llm.py` importa o SDK.
- Nenhum teste chama a API Gemini, e nenhum teste dorme de verdade.
- Os testes que já existem continuam passando. Ajuste só o teste do 429, que muda de comportamento.

## Critérios de aceite

- [x] Com os valores padrão, nenhuma janela de 60 segundos passa de 100 textos ou de 30 mil tokens estimados de embeddings, nem de 15 chamadas de geração.
- [x] Um HTTP 429 espera o `retryDelay` ou 60 segundos, no máximo duas vezes, e depois levanta `LLMError` com a mensagem do contrato.
- [x] O comportamento em HTTP 503 não muda.
- [x] As assinaturas de `embed_texts` e `generate_structured` não mudam.
- [x] Os hooks e os testes passam, com cobertura de 90% ou mais.
- [x] Se você tiver uma chave, rode `embed_texts` com 150 textos de 1.000 caracteres e relate no PR o tempo total e se houve 429. Sem chave, diga que não rodou.

## Cenários de teste

Em `backend/tests/core/test_llm.py`, com um relógio falso: `_now` devolve um valor que só avança quando o `_sleep` falso recebe uma espera. Cada teste começa com os controles de ritmo vazios.

1. `embed_texts` com 150 textos de 1.000 caracteres: 8 chamadas, em ordem. Em nenhuma janela de 60 segundos do relógio falso a soma passa de 100 textos ou de 30 mil tokens estimados, e a espera total é maior que zero.
2. `embed_texts` com 20 textos curtos: uma chamada e nenhuma espera.
3. Duas chamadas seguidas de `embed_texts` dividem a mesma janela: a segunda espera se a soma das duas passa do limite.
4. 16 chamadas de `generate_structured` sem avançar o relógio: as 15 primeiras saem sem espera, e a 16ª espera até a primeira sair da janela.
5. `GEMINI_EMBEDDING_RPM = 10` com 40 textos: cada lote de 20 passa sozinho do limite. O primeiro sai sem espera, o segundo espera a janela esvaziar, e a função termina.
6. HTTP 429 com `retryDelay` de 37 segundos e depois sucesso: uma espera de 37 segundos e o resultado certo.
7. HTTP 429 sem `RetryInfo` e depois sucesso: uma espera de 60 segundos.
8. Três HTTP 429 seguidos: duas esperas longas e depois `LLMError` com a mensagem do contrato, sem o texto enviado.
9. HTTP 503 e depois sucesso: uma espera de 1 segundo, como hoje.
10. A nova tentativa depois de um 429 passa pelo controle e conta na janela.

## Verificação do aceite

- PR revisado: [#31](https://github.com/No-Country-simulation/g10_equipe1_novamente/pull/31), integrado no commit `e4e3613`.
- CI do PR: todos os checks obrigatórios passaram, com escopo dentro de `touches`.
- Revisão automática sobre o commit `a73f90b`: sem achados.
- Chamada real: `embed_texts` com 150 textos de 1.000 caracteres devolveu 150 vetores em 63,84 segundos, sem HTTP 429.
