---
id: T25
title: Ensine o agente `escreve` a gerar flashcards
blocked_by: [T20, T40]
touches:
  - backend/app/services/writer.py
  - backend/tests/services/test_writer.py
executor: agente
size: 2
---

# T25 - Ensine o agente `escreve` a gerar flashcards

## Contexto

T20 entregou `write_content` para tutorial. No `master`, um pedido de flashcards levanta `UnsupportedFormatError`. T05 entregou `GeneratedFlashcards`. A [verificação de 19/11/2026 com o Gemini](../ARCHITECTURE.md#modelos-de-ia) confirmou que a API aceita o schema.

T40 faz `revisa` conferir só `content`. Uma afirmação sem apoio impede a publicação da versão revisada. Os fatos técnicos ficam no conteúdo de estudo, que inclui a introdução e os cartões.

Leia antes a seção [Flashcards](../product-specs/conteudos-e-formatos.md#flashcards), [T20](completed/T20-agente-escreve-tutorial.md), [T40](completed/T40-regras-de-fidelidade.md) e `backend/app/services/writer.py`.

## Escopo

- A instrução do formato flashcards e a entrada no dicionário de formatos.
- A instrução sobre metadados passa do tutorial para a parte comum de `system_instruction`.
- A nova versão do prompt.

## Fora do escopo

- Quiz (T26).
- Mudar a revisão (T40) ou o grafo (T24).
- Mudar `GeneratedFlashcards` ou outro modelo de `content_schemas.py`.
- Validação automática dos conceitos-chave contra o documento.
- O leitor de flashcards (T09).

## Contrato

### Módulos que este ticket usa

`content_schemas.py` já define estes modelos e já mapeia `ContentFormat.flashcards` para `GeneratedFlashcards` em `GENERATED_MODELS`.

```python
# app.services.content_schemas
class Flashcard(StrictModel):
    front: Text
    back: Text
    hint: Text | None = None


class FlashcardsContent(StrictModel):
    introduction: Text
    cards: list[Flashcard] = Field(min_length=8, max_length=12)


class GeneratedFlashcards(GeneratedBase):
    content: FlashcardsContent
```

### O que este ticket muda em `backend/app/services/writer.py`

A interface pública de T20 não muda: `WriteRequest`, `Rewrite`, `write_content` e `UnsupportedFormatError`.

- `PROMPT_VERSION` passa a `"escreve-v2"`.
- Crie `FLASHCARDS_INSTRUCTION` logo depois de `TUTORIAL_INSTRUCTION`.
- `FORMAT_INSTRUCTIONS` ganha a entrada `ContentFormat.flashcards: FLASHCARDS_INSTRUCTION`. Escreva o dicionário com uma entrada por linha, para T26 acrescentar a do quiz sem mexer nas outras.
- Mova as instruções de metadados de `TUTORIAL_INSTRUCTION` para `system_instruction`, antes da instrução do formato. Mantenha as instruções sobre a estrutura do tutorial.

`ContentFormat.quiz` continua a levantar `UnsupportedFormatError` até T26.

### O que o prompt diz

O texto exato é seu. Estas regras valem para qualquer redação.

A regra comum, para todos os formatos:

- Use um título que descreva o material. Coloque os fatos técnicos em `content`.
- Escolha conceitos-chave que aparecem nos trechos do documento e que o conteúdo ensina. Essa é uma instrução de `escreve`. T40 mantém os metadados fora da revisão.
- Indique o que a pessoa precisa saber antes de estudar. Informe o tempo estimado em minutos.

A instrução dos flashcards:

1. Uma introdução curta que situa o assunto com base nos trechos.
2. De 8 a 12 cartões. Cada cartão trata de um só fato ou conceito.
3. A frente é uma pergunta ou um termo. O verso responde à frente com um fato dos trechos do documento.
4. A dica é opcional. Ela ajuda a lembrar a resposta e não traz um fato técnico que o verso e os trechos não trazem.
5. Cartões diferentes não repetem a mesma pergunta.

## Detalhes técnicos

- Siga o padrão de T20: chame o Gemini por `llm.generate_structured`, sem ler `settings` e sem citar nome de modelo.
- Mantenha as dependências e o contrato OpenAPI. O hook que gera `frontend/src/client/` deve deixar o cliente igual.
- T26 acrescenta o quiz aos mesmos arquivos depois deste ticket. T24 usa a mesma interface de `write_content` para todos os formatos.

## Testes que mudam

Em `backend/tests/services/test_writer.py`, troque o laço de formatos sem instrução de `test_writer` por uma chamada com `ContentFormat.quiz` dentro de `pytest.raises(UnsupportedFormatError)`. Mantenha os demais casos de T20 e acrescente os cenários de flashcards ao fim do arquivo.

## Verificação com a API real

Com o Gemini configurado, use o foco e os trechos do caso de assunto presente da [verificação de T40](completed/T40-regras-de-fidelidade.md#verificação-com-a-api-real). Rode `write_content` com `ContentFormat.flashcards`. Passe o resultado a `review_content`, com o mesmo foco, nível e trechos. Chame `evaluate` e `decide` conforme o contrato de T40, com `attempt=1`.

Registre no PR quantos cartões saíram, a decisão, `focus_covered`, as contagens de afirmações com e sem apoio e a lista das que ficaram sem apoio. Indique se a revisão contou alguma afirmação presente só nos metadados. Mantenha o código da verificação fora do PR. Sem acesso ao Gemini, registre que você pulou a verificação.

## Critérios de aceite

- [ ] `write_content` com `ContentFormat.flashcards` chama o modelo uma vez, com `response_model=GeneratedFlashcards`, e devolve a instância.
- [ ] A reescrita de flashcards traz a versão anterior e as afirmações sem apoio, como no tutorial.
- [ ] `system_instruction` traz a regra comum dos metadados nos dois formatos. `PROMPT_VERSION` é `"escreve-v2"` neste ticket.
- [ ] `ContentFormat.quiz` levanta `UnsupportedFormatError`, sem chamar o modelo.
- [ ] Nenhum teste chama o Gemini.
- [ ] Os hooks e os testes passam, com cobertura de 90% ou mais.
- [ ] O PR relata a verificação com a API real, ou diz que ela não rodou.

## Cenários de teste

Em `backend/tests/services/test_writer.py`, troque `llm.generate_structured` por uma função falsa que registra as chamadas e devolve uma instância válida do modelo pedido. Use `GeneratedFlashcards` com 8 cartões nos casos de flashcards.

1. Uma primeira escrita de flashcards chama o modelo uma vez, com `response_model` igual a `GeneratedFlashcards`, e devolve a instância da função falsa.
2. `system_instruction` dos flashcards é diferente da do tutorial e fala em 8 a 12 cartões e na dica sem fato novo.
3. `system_instruction` dos flashcards e a do tutorial trazem a regra comum dos metadados.
4. A reescrita com um `Rewrite` de flashcards traz no `prompt` o JSON da versão anterior e cada afirmação sem apoio. Use uma introdução anterior distinta para identificar a versão.
5. Um `Rewrite` com um `GeneratedTutorial` para um pedido de flashcards levanta `ValueError`, com zero chamadas.
