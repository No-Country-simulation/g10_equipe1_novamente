# Fidelidade e qualidade

O produto só publica um conteúdo depois de conferir cada afirmação técnica contra o documento. Um conteúdo reprovado não aparece para a pessoa.

Estado: a construir.

## O que a pessoa vê em um conteúdo publicado

| Informação | Significado | No esquema |
| --- | --- | --- |
| Fidelidade ao documento | Porcentagem das afirmações técnicas com apoio no documento | `course_content.grounding_score` |
| Clareza | Baixa, média ou alta | `course_content.clarity` |
| Observações da revisão | Um texto curto sobre a adequação ao público | `course_content.review_notes` |
| Trechos citados | Os trechos do documento que sustentam o conteúdo | `content_citation` |

Cada trecho citado existe no documento que a pessoa enviou.

## Como o produto decide publicar

1. Um revisor lista as afirmações técnicas do conteúdo.
2. Para cada afirmação, o revisor aponta o trecho do documento que a sustenta, ou diz que não há trecho.
3. O produto calcula a fidelidade: afirmações sustentadas divididas pelo total de afirmações.
4. Se a fidelidade atinge o mínimo, o produto publica.
5. Se não atinge, o produto reescreve o conteúdo uma vez, com a lista das afirmações reprovadas.
6. Se a segunda versão também não atinge, o produto não publica e mostra as afirmações reprovadas.

O mínimo inicial é 80%. A equipe mede com os primeiros casos, ajusta o valor e registra cada mudança neste documento.

## Regras

- **Analogias ficam.** Uma analogia ou um exemplo do setor não é uma afirmação técnica. Ela não entra na conta, desde que não traga um fato técnico novo.
- **Erro na revisão não aprova.** Se a revisão falha ou devolve uma resposta inválida, o produto não publica.
- **A nota é calculada, não escrita pelo modelo.** O produto conta as afirmações. O modelo não informa o número.
- **Sem apoio, sem ponto.** Uma afirmação marcada como sustentada, sem um trecho válido, conta como não sustentada.
- **Assunto ausente gera aviso.** Se o documento não trata do foco pedido, o conteúdo reprova e a pessoa vê o motivo.

## Limite conhecido

O revisor só vê os trechos que a busca encontrou. Uma afirmação correta, baseada em outra parte do documento, pode ser reprovada. A equipe prefere esse erro ao de aprovar algo sem fonte.

## Como a equipe mede a qualidade

As metas abaixo são o ponto de partida. Nenhuma foi medida ainda. A equipe ajusta cada meta depois da primeira medição.

| O que mede | Como | Meta inicial |
| --- | --- | --- |
| A busca acha o trecho certo | 20 perguntas com a resposta esperada. O trecho certo fica entre os 8 trechos que a busca devolve | 80% das perguntas |
| O revisor acha erros | 5 conteúdos com um erro plantado e 5 conteúdos fiéis | 4 de 5 erros achados e no máximo 1 alarme falso |
| A nota de clareza faz sentido | 10 conteúdos com nota do revisor e nota de uma pessoa | Concordância em 8 de 10 |
| A adaptação ao público funciona | Uma pessoa de fora indica o nível de cada conteúdo sem ver o rótulo | Acerta todos |

Pessoas sem experiência em programação podem escrever os casos: a tarefa é ler um documento e criar perguntas ou afirmações erradas.

## O que fica fora

- Revisão por uma pessoa antes de publicar.
- Edição manual de um conteúdo publicado.
- Histórico das versões reprovadas.
