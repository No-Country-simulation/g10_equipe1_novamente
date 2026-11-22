# Fidelidade e qualidade

O produto só publica um conteúdo depois de conferir cada afirmação técnica contra o documento. Um conteúdo reprovado não aparece para a pessoa.

Estado: a construir.

## O que a pessoa vê em um conteúdo publicado

| Informação | Significado | No esquema |
| --- | --- | --- |
| Fidelidade ao documento | Porcentagem das afirmações técnicas com apoio no documento. Cada versão publicada pela regra nova tem 100%. | `course_content.grounding_score` |
| Clareza | Baixa, média ou alta, conforme o texto serve ao nível de público do curso | `course_content.clarity` |
| Observações da revisão | Um texto curto sobre a adequação ao público | `course_content.review_notes` |
| Trechos citados | Os trechos do documento que sustentam o conteúdo | `content_citation` |

Cada trecho citado existe no documento que a pessoa enviou.

## Como o produto decide publicar

1. O revisor confere o material de estudo e verifica se ele trata diretamente do foco com apoio nos trechos recuperados. Para quiz, o material traz o enunciado, a resposta marcada e a justificativa de cada pergunta. Para tutorial e flashcards, o revisor recebe o campo `content`. Os trechos servem de evidência para os fatos do material. Os metadados da raiz do JSON ficam fora da revisão.
2. O revisor lista as afirmações técnicas e aponta o trecho que sustenta cada uma, ou indica que não há apoio.
3. O produto divide o número de afirmações sustentadas pelo total de afirmações. Se a revisão não lista afirmações, a nota é zero.
4. Se o foco não é coberto, a geração falha de imediato com “O documento não trata do assunto pedido.”
5. O produto publica se o material cobre o foco, a revisão lista pelo menos uma afirmação e todas têm apoio em trechos válidos.
6. Se o foco é coberto, mas falta apoio para alguma afirmação ou a revisão não lista afirmações, o produto reescreve uma vez com a lista das afirmações sem apoio.
7. Na segunda revisão, se o foco não é coberto ou a revisão não lista afirmações, a geração falha com “O documento não trata do assunto pedido.” Se o foco é coberto e falta apoio para alguma afirmação, a mensagem começa com “Afirmações sem apoio no documento:” e lista cada afirmação sem apoio em uma linha.

O banco e o JSON da OCI guardam a nota de 0 a 1. A tela mostra a nota em porcentagem, inclusive para versões antigas. O produto só grava a nota ao publicar. Se a geração falha, a nota da versão publicada permanece, se houver.

## Regras

- **Analogias ficam.** Uma analogia ou um exemplo do setor não é uma afirmação técnica. Ela não entra na conta, desde que não traga um fato técnico novo.
- **Erro na revisão não aprova.** Se a revisão falha ou devolve uma resposta inválida, o produto não publica.
- **A nota é calculada, não escrita pelo modelo.** O produto conta as afirmações. O modelo não informa o número.
- **Sem apoio, sem ponto.** Uma afirmação marcada como sustentada, sem um trecho válido, conta como não sustentada.
- **Assunto ausente gera aviso.** Se o material não cobre o foco pedido com base nos trechos recuperados, a geração falha sem reescrita e a pessoa vê o motivo.

## Limite conhecido

O revisor só vê os trechos que a busca encontrou. Uma afirmação correta, baseada em outra parte do documento, pode ser reprovada. A equipe prefere esse erro ao de aprovar algo sem fonte.

## Como a equipe mede a qualidade

[`backend/scripts/evaluate.py`](../../backend/scripts/evaluate.py) mede a busca, registra as decisões do revisor e da geração e mostra pistas para a equipe conferir as reprovações em T41. Veja o [guia de casos de avaliação](../../examples/evals/README.md).

As metas abaixo são o ponto de partida. A equipe ajusta cada meta depois de revisar as medições.

| O que mede | Como | Meta inicial |
| --- | --- | --- |
| A busca acha o trecho certo | 20 perguntas com a resposta esperada. O trecho certo fica entre os 8 trechos que a busca devolve | 80% das perguntas |
| O revisor acha erros | 5 conteúdos com um erro plantado e 5 conteúdos fiéis | 4 de 5 erros achados e no máximo 1 alarme falso |
| A nota de clareza faz sentido | 10 conteúdos com nota do revisor e nota de uma pessoa | Concordância em 8 de 10 |
| A adaptação ao público funciona | Uma pessoa de fora indica o nível de cada conteúdo sem ver o rótulo | Acerta todos |

Pessoas sem experiência em programação podem escrever os casos: a tarefa é ler um documento e criar perguntas ou afirmações erradas.

## Medições

A medição usa a primeira rodada do Pix e do Open Finance no commit `06a945b` e a repetição da LAI após a correção do quiz no commit `09e0a82`.

| O que mede | Resultado da rodada |
| --- | --- |
| Data (UTC) | 2026-11-21 |
| Modelo de texto | `gemini-3.5-flash-lite` |
| Modelo de embeddings | `gemini-embedding-2` |
| Versão dos prompts | `planeja-v1+escreve-v4+revisa-v2` |
| Busca | 20 de 20 trechos esperados entre os 8 (100%). |
| Revisor | 4 de 5 erros plantados identificados na conferência. 0 alarmes falsos em 5 casos fiéis. |
| Clareza | Não medida. A equipe não tem quem julgue o assunto dos documentos. |
| Geração | 4 de 4 conteúdos aprovados para publicação. 0 reprovações, 0 falsas reprovações e 0 casos sem causa confirmada. |
| Erros de execução | 2 de 6 gerações receberam HTTP 503 do Gemini. A primeira tentativa de indexar o Open Finance falhou antes dos casos. A repetição mediu o arquivo completo. |

No quiz da LAI com erro plantado, a resposta marcada e a justificativa davam 30 dias como prazo inicial. O revisor reprovou o quiz ao marcar como sem apoio a alternativa de 20 dias, que o art. 11, § 1º, sustenta. O erro de 30 dias ficou sem marcação.

### Rodada com `revisa-v3`

A rodada usou o código do commit `8c6f019` e ocorreu antes de um rebase que manteve o código e os casos de avaliação.

| O que mede | Resultado da rodada |
| --- | --- |
| Data (UTC) | 2026-11-21 |
| Modelo de texto | `gemini-3.5-flash-lite` |
| Modelo de embeddings | `gemini-embedding-2` |
| Versão dos prompts | `planeja-v1+escreve-v4+revisa-v3` |
| Busca | 20 de 20 trechos esperados entre os 8 (100%). |
| Revisor | 5 de 5 erros plantados detectados. 0 alarmes falsos em 5 casos fiéis. |
| Clareza | Não medida. |
| Geração | 6 de 6 conteúdos aprovados para publicação. 1 de 6 precisou de uma segunda tentativa (flashcards de Pix Agendado, causa não confirmada). |
| Erros de execução | Nenhum. |

Em `lai-pedido-erro`, o revisor marcou como sem apoio o prazo inicial de 30 dias da resposta e da justificativa. Nos dois casos da LAI, a lista de afirmações sem apoio trouxe apenas fatos do material. Os quatro erros plantados do Pix e do Open Finance também apareceram nessa lista nos respectivos casos.

## O que fica fora

- Revisão por uma pessoa antes de publicar.
- Edição manual de um conteúdo publicado.
- Histórico das versões reprovadas.
