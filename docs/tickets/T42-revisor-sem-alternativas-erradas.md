---
id: T42
title: Tire as alternativas erradas do quiz que o revisor recebe
blocked_by: [T41]
touches:
  - backend/app/services/reviewer.py
  - backend/tests/services/test_reviewer.py
  - backend/tests/services/test_generation_graph.py
  - docs/ARCHITECTURE.md
  - docs/product-specs/fidelidade-e-qualidade.md
executor: agente
size: 2
---

# T42 - Tire as alternativas erradas do quiz que o revisor recebe

## Contexto

A primeira medição de T41 achou um defeito em `revisa`. No caso `lai-pedido-erro` de [`examples/evals/lei-de-acesso-a-informacao.json`](../../examples/evals/lei-de-acesso-a-informacao.json), a quarta pergunta marca "30 dias" como resposta, e a justificativa repete esse prazo. O art. 11, § 1º, da LAI fixa o prazo inicial em até 20 dias quando o acesso imediato não é possível.

O revisor reprovou o quiz por marcar os 20 dias como sem apoio, embora o trecho 14 sustente esse prazo. Deixou passar os 30 dias da resposta marcada e da justificativa. Veja o [relatório da LAI no PR de T41](https://github.com/No-Country-simulation/g10_equipe1_novamente/pull/49) e a seção "Medições" de [`fidelidade-e-qualidade.md`](../product-specs/fidelidade-e-qualidade.md).

### O que o revisor recebe hoje

T40 manda excluir alternativas erradas da lista de afirmações. A instrução está no prompt, mas `review_content` serializa o quiz com `generated.model_dump_json(include={"content"})`. Cada pergunta chega com as quatro `options` e um `correct_index` de 0 a 3.

No caso da LAI, o modelo vê os 20 dias na alternativa de índice 3 e também no trecho de índice 14 do documento. O relatório não permite saber qual foi a origem da afirmação. O prompt já pede as afirmações do material. T42 torna explícito que os trechos servem de evidência e retira as opções não marcadas do material.

Leia antes: [T40](completed/T40-regras-de-fidelidade.md), seção "O que o prompt de `revisa` diz", [T21](completed/T21-agente-revisa.md), seção "O que o prompt diz", e [`examples/evals/README.md`](../../examples/evals/README.md).

## Escopo

- A serialização do quiz em `review_content`, com o enunciado, a resposta marcada e a justificativa de cada pergunta.
- As regras de quiz e de origem das afirmações no prompt de `revisa`.
- `PROMPT_VERSION` passa a `revisa-v3`.
- Os testes com o modelo trocado.
- Uma nova rodada da avaliação com o Gemini real e o registro em "Medições".

## Fora do escopo

- Mudar o tutorial e os flashcards que o revisor recebe. Eles continuam com `generated.model_dump_json(include={"content"})`.
- Conferir se as opções tornam a pergunta ambígua. O quiz publicado continua com as quatro alternativas.
- Mudar `escreve`, `grounding.py`, `content_schemas.py`, o script de avaliação ou os casos de `examples/evals/`.
- Mudar as metas de `fidelidade-e-qualidade.md`.

## Contrato

### `backend/app/services/reviewer.py`

```python
PROMPT_VERSION = "revisa-v3"


def review_content(
    *,
    generated: GeneratedBase,
    audience_level: AudienceLevel,
    focus: str,
    chunks: Sequence[RetrievedChunk],
) -> ReviewResult: ...  # assinatura sem mudança
```

O contrato de `review_content` muda o material enviado para quiz.

- Quando `generated` é um `GeneratedQuiz`, use este JSON e preserve a ordem das perguntas.

    ```json
    {"content": {"questions": [
      {"prompt": "...", "correct_answer": "...", "explanation": "..."}
    ]}}
    ```

    `correct_answer` é `options[correct_index]`, inclusive num caso de avaliação em que a opção marcada é falsa. Monte essa projeção com `json.dumps`, sem alterar o objeto gerado. Os trechos podem conter o mesmo texto que uma alternativa errada.
- Para os outros formatos, o material continua `generated.model_dump_json(include={"content"})`.
- Mantenha uma chamada com `temperature=0.0`, o foco e o público no prompt e a validação atual de foco e trechos. Deixe `LLMError` subir para o chamador.
- Numere os mesmos trechos a partir de 1, sem UUIDs no prompt. Converta `chunk_number` no UUID do trecho pela posição. Número nulo ou fora da lista vira `None`. `grounding.evaluate` continua contando apoio e gerando citações apenas para IDs válidos dos trechos usados.

### O que o prompt de `revisa` diz

1. Liste uma afirmação técnica por item. Use fatos expressos no material, inclusive quando precisar juntar o enunciado à resposta marcada para formular uma afirmação. Em quiz, inclua também fatos do próprio enunciado e da justificativa. Retire a instrução para excluir alternativas erradas.
2. Use os trechos para verificar as afirmações. Um fato que aparece só nos trechos fica fora da lista. Se o material contradiz o trecho, liste o fato do material como sem apoio.
3. Preserve as regras de T40 para cobertura do foco, revisão do tutorial e revisão da introdução, das frentes, dos versos e das dicas dos flashcards. Mantenha a exclusão de instruções de estudo, analogias e exemplos que não trazem fatos técnicos novos.

## Detalhes técnicos

- Em `backend/tests/services/test_generation_graph.py`, `test_prompt_version_includes_all_agents` passa a esperar `"planeja-v1+escreve-v4+revisa-v3"`. Os registros existentes mantêm suas versões em `course_content.prompt_version`.
- `scripts/evaluate.py` já monta um `GeneratedQuiz` para casos de quiz e chama `reviewer.review_content`. O script passa pela nova projeção com os mesmos casos, a mesma assinatura e a versão composta do grafo.
- Use `monkeypatch.setattr` em `app.core.llm.generate_structured` nos testes. Comece rodando o cenário da LAI antes da mudança. A asserção do material deve falhar com `options` e `correct_index` ainda presentes.

## Documentos que este ticket atualiza

Em `docs/ARCHITECTURE.md`, no passo 8 de "A criação de um curso segue doze passos", diga que um quiz chega a `revisa` com o enunciado, a resposta marcada e a justificativa de cada pergunta.

Em `docs/product-specs/fidelidade-e-qualidade.md`, atualize o contrato e registre a rodada.

- No passo 1 de "Como o produto decide publicar", descreva a projeção usada no quiz e o papel dos trechos como evidência.
- Na seção "Medições", preserve a primeira medição e o achado da LAI. Acrescente a rodada de `revisa-v3` com data, commit, modelos, versão, métricas e erros de execução. Registre se o revisor marcou o prazo inicial de 30 dias e se o relatório voltou a atribuir ao material um fato que só aparecia nas alternativas erradas ou nos trechos. A clareza continua não medida. Retire da linha "Clareza" a menção ao T34, que a equipe descartou.

Não edite os tickets em `docs/tickets/completed/`.

## Verificação com a API real

1. Na raiz, prepare o banco com `bash scripts/worktree-setup.sh T42`. Configure as variáveis `GEMINI_*` no `.env` deste worktree conforme o [guia da avaliação](../../examples/evals/README.md), com os mesmos modelos de T41. Mantenha as chaves fora do PR.
2. Em `backend/`, depois dos testes verdes, rode a LAI primeiro.

    ```bash
    uv run python scripts/evaluate.py ../examples/evals/lei-de-acesso-a-informacao.json
    ```

3. Confira se a linha de `lai-pedido-erro` lista o prazo **inicial** de 30 dias como afirmação sem apoio. Confira as linhas dos dois casos da LAI. Uma alternativa errada pode estar correta em outro contexto, como os 20 dias que a resposta marcada da quarta pergunta substituiu. Julgue a afirmação no contexto da pergunta. O relatório lista apenas afirmações sem apoio. O teste da projeção verifica o material enviado.
4. Se o erro plantado passar, ajuste a redação sobre o quiz e a origem das afirmações e repita a LAI. Faça no máximo dois ajustes. Se o caso ainda falhar, registre o resultado e peça à equipe que decida o próximo passo
5. Com a versão final do prompt, rode Pix e Open Finance em sequência. Aguarde uma janela de um minuto entre arquivos, pois cada processo inicia seu próprio limitador.

    ```bash
    uv run python scripts/evaluate.py ../examples/evals/regulamento-do-pix.json
    ```

    ```bash
    uv run python scripts/evaluate.py ../examples/evals/open-finance.json
    ```

6. Se a indexação falhar ou algum caso de busca ou revisão ficar sem resultado por erro temporário, repita o arquivo uma vez, quando houver cota. Registre as duas execuções. Conte erros de geração à parte dos casos com decisão de publicação. Se ainda faltar um caso de busca ou revisão, registre a lacuna antes de considerar a medição completa.
7. Confira os erros plantados caso a caso. Uma reprovação só conta como detecção quando a afirmação correspondente aparece sem apoio. Registre os alarmes falsos e confira as pistas no documento para distinguir falha de busca, falha de revisão e falta de apoio. Use "causa não confirmada" se faltar evidência.

Uma rodada usa 219 embeddings de indexação, 36 de busca e até 40 chamadas de texto, mais pistas e novas tentativas. Cabe nos limites diários medidos de 1.000 embeddings e 500 chamadas de texto quando há saldo para a rodada. Confira o consumo do projeto antes de repetir arquivos. Guarde os relatórios no PR.

## Critérios de aceite

- [ ] O JSON após `Material:\n` usa a projeção do contrato, com os cinco itens em ordem. O teste confirma que os trechos continuam disponíveis, inclusive se contêm o texto de uma alternativa errada.
- [ ] O tutorial e os flashcards chegam ao revisor como antes.
- [ ] `PROMPT_VERSION` vale `revisa-v3`, e `generation_graph.PROMPT_VERSION` vale `planeja-v1+escreve-v4+revisa-v3`.
- [ ] Na rodada real, `lai-pedido-erro` tem o prazo inicial de 30 dias entre as afirmações sem apoio. Em ambos os casos da LAI, essa coluna não lista fatos que aparecem só nas alternativas erradas ou nos trechos.
- [ ] Os cinco casos fiéis seguem sem alarme falso e os outros quatro erros plantados seguem marcados. Se houver regressão, registre o caso e a evidência no PR e em "Medições" para decisão da equipe.
- [ ] "Medições" registra a nova rodada com `planeja-v1+escreve-v4+revisa-v3`, a data, os modelos e os erros de execução.
- [ ] Nenhum teste chama o Gemini.
- [ ] Os hooks e os testes passam, com cobertura de 90% ou mais.

## Cenários de teste

Use `generate_structured` trocada em `backend/tests/services/test_reviewer.py`.

1. Um `GeneratedQuiz` válido com cinco perguntas e índices marcados 0, 1, 2, 3 e 0. Analise o JSON após `"\nMaterial:\n"` e compare os cinco itens com o contrato. Confira que o objeto original ainda contém as quatro opções de cada pergunta.
2. Na pergunta da LAI com opções "5 dias", "10 dias", "30 dias" e "20 dias", o índice 2 põe "30 dias" e sua justificativa no material. Inclua um trecho que diga "20 dias". O trecho permanece no prompt e a opção fica fora do JSON da pergunta.
3. Um `GeneratedFlashcards` válido e o tutorial existente continuam serializados com `model_dump_json(include={"content"})`.
4. Atualize a asserção antiga de `test_review` sobre excluir as alternativas. Confira que `system_instruction` usa `correct_answer`, delimita a origem das afirmações e mantém as regras de foco e de analogias de T40.
5. Preserve os testes de T21 e T40 para a resolução de `chunk_number`, os IDs inválidos, as precondições e a decisão de publicar.

Em `backend/tests/services/test_generation_graph.py`, confira a versão composta.
