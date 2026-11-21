---
id: T26
title: Ensine o agente `escreve` a gerar quiz
blocked_by: [T25]
touches:
  - backend/app/services/writer.py
  - backend/tests/services/test_writer.py
executor: agente
size: 2
---

# T26 - Ensine o agente `escreve` a gerar quiz

## Contexto

`write_content` aceita tutorial (T20) e passa a aceitar flashcards com T25. Um pedido de quiz levanta `UnsupportedFormatError` até este ticket. T05 entregou `GeneratedQuiz`. A [verificação de 19/11/2026 com o Gemini](../../ARCHITECTURE.md#modelos-de-ia) confirmou que a API aceita o schema.

T40 faz `revisa` conferir só `content`. No quiz, a revisão confere as afirmações técnicas do enunciado, da resposta correta e da justificativa. As opções erradas funcionam como alternativas de resposta.

O JSON conserva `correct_index` para a revisão e para a correção imediata, que segue opcional. O leitor básico de T10 mostra a justificativa após a resposta, sem usar o índice para dar nota.

T25 e T26 editam `PROMPT_VERSION` e `FORMAT_INSTRUCTIONS` em `writer.py`, além do teste de formato sem instrução em `test_writer.py`. Por isso T26 espera T25.

Leia antes a seção [Quiz](../../product-specs/conteudos-e-formatos.md#quiz), [T20](T20-agente-escreve-tutorial.md), [T25](T25-agente-escreve-flashcards.md), [T40](T40-regras-de-fidelidade.md) e `backend/app/services/writer.py`.

## Escopo

- A instrução do formato quiz e a entrada no dicionário de formatos.
- A nova versão do prompt.

## Fora do escopo

- Mudar a revisão (T40), o grafo (T24) ou a regra comum dos metadados (T25).
- Mudar `GeneratedQuiz` ou outro modelo de `content_schemas.py`.
- O leitor de quiz (T10).

## Contrato

### Módulos que este ticket usa

`content_schemas.py` já define estes modelos e já mapeia `ContentFormat.quiz` para `GeneratedQuiz` em `GENERATED_MODELS`. `QuizQuestion.options_are_unique` rejeita opções repetidas.

```python
# app.services.content_schemas
class QuizQuestion(StrictModel):
    prompt: Text
    options: list[Text] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation: Text


class QuizContent(StrictModel):
    questions: list[QuizQuestion] = Field(min_length=5, max_length=5)


class GeneratedQuiz(GeneratedBase):
    content: QuizContent
```

### O que este ticket muda em `backend/app/services/writer.py`

A interface pública de T20 não muda.

- `PROMPT_VERSION` passa a `"escreve-v3"`.
- Crie `QUIZ_INSTRUCTION` logo depois de `FLASHCARDS_INSTRUCTION`.
- `FORMAT_INSTRUCTIONS` ganha a entrada `ContentFormat.quiz: QUIZ_INSTRUCTION`, na última linha do dicionário.

Os três valores atuais de `ContentFormat` passam a ter instrução. Mantenha `UnsupportedFormatError` para qualquer formato ausente de `FORMAT_INSTRUCTIONS`.

### O que o prompt diz

O texto exato é seu. Estas regras valem para qualquer redação.

1. Exatamente 5 perguntas, cada uma sobre um fato ou conceito dos trechos do documento.
2. Exatamente 4 opções por pergunta, sem repetição. Uma só opção é correta, e `correct_index` aponta para ela, de 0 a 3.
3. As opções incorretas são plausíveis para o nível de público. Os trechos permitem distinguir a opção correta das demais.
4. A posição da opção correta varia entre as perguntas.
5. A justificativa explica a resposta correta com fatos dos trechos. Qualquer fato no enunciado ou na justificativa precisa ter apoio nos trechos.
6. Perguntas diferentes não tratam do mesmo fato.

## Detalhes técnicos

- Siga o padrão de T20: chame o Gemini por `llm.generate_structured`, sem ler `settings` e sem citar nome de modelo.
- Mantenha as dependências e o contrato OpenAPI. O hook que gera `frontend/src/client/` deve deixar o cliente igual.

## Testes que mudam

Em `backend/tests/services/test_writer.py`, retire de `test_writer` o caso de quiz sem instrução que T25 deixou. Acrescente o cenário de quiz sem entrada em `FORMAT_INSTRUCTIONS` e os demais cenários de quiz ao fim do arquivo. Mantenha os testes de tutorial e flashcards.

## Verificação com a API real

Com o Gemini configurado, use o foco e os trechos do caso de assunto presente da [verificação de T40](T40-regras-de-fidelidade.md#verificação-com-a-api-real). Rode `write_content` com `ContentFormat.quiz`. Passe o resultado a `review_content`, com o mesmo foco, nível e trechos. Chame `evaluate` e `decide` conforme o contrato de T40, com `attempt=1`.

Registre no PR o `correct_index` de cada pergunta, a decisão, `focus_covered`, as contagens de afirmações com e sem apoio e a lista das que ficaram sem apoio. Indique se a revisão contou alguma afirmação presente só nas opções erradas ou nos metadados. Mantenha o código da verificação fora do PR. Sem acesso ao Gemini, registre que você pulou a verificação.

## Critérios de aceite

- [x] `write_content` com `ContentFormat.quiz` chama o modelo uma vez, com `response_model=GeneratedQuiz`, e devolve a instância.
- [x] A reescrita de quiz traz a versão anterior e as afirmações sem apoio, como no tutorial.
- [x] Os três formatos têm instruções, a conferência de formato sem instrução tem teste e `PROMPT_VERSION` é `"escreve-v3"` neste ticket.
- [x] Nenhum teste chama o Gemini.
- [x] Os hooks e os testes passam, com cobertura de 90% ou mais.
- [x] O PR relata a verificação com a API real, ou diz que ela não rodou.

## Cenários de teste

Em `backend/tests/services/test_writer.py`, troque `llm.generate_structured` por uma função falsa que registra as chamadas e devolve uma instância válida do modelo pedido. Use `GeneratedQuiz` com 5 perguntas nos casos de quiz.

1. Uma primeira escrita de quiz chama o modelo uma vez, com `response_model` igual a `GeneratedQuiz`, e devolve a instância da função falsa.
2. `system_instruction` do quiz pede 5 perguntas, 4 opções por pergunta, uma resposta correta com posição variada e justificativas apoiadas nos trechos.
3. `system_instruction` do quiz traz a regra comum dos metadados de T25.
4. A reescrita com um `Rewrite` de quiz traz no `prompt` o JSON da versão anterior e cada afirmação sem apoio. Use um enunciado anterior distinto para identificar a versão.
5. Um `Rewrite` com um `GeneratedFlashcards` para um pedido de quiz levanta `ValueError`, com zero chamadas.
6. Retire a entrada do quiz com `monkeypatch.delitem(writer.FORMAT_INSTRUCTIONS, ContentFormat.quiz)`. O pedido de quiz levanta `UnsupportedFormatError`, com zero chamadas. `monkeypatch` restaura a entrada ao fim do teste.

## Verificação do aceite

- PR revisado: [#41](https://github.com/No-Country-simulation/g10_equipe1_novamente/pull/41), integrado no commit `e55afd5`.
- CI do PR: todos os checks obrigatórios passaram, com escopo dentro de `touches`.
- Revisão automática sobre o commit `7b81e26`: sem achados. Só o prompt pede que a posição da opção correta varie, porque o ticket não permite mudar `GeneratedQuiz`. O schema já garante uma única opção correta.
- Testes: 334 testes passaram, com 98% de cobertura no backend.
- Verificação com a API real: relatada no PR, com `correct_index` `[0, 2, 1, 1, 0]`, decisão `publish`, 5 afirmações com apoio e nenhuma tirada de opções incorretas ou dos metadados.
