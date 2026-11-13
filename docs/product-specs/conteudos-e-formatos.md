# Conteúdos e formatos

Um curso tem um ou mais conteúdos. Cada conteúdo tem um formato, um foco e um resultado gerado a partir dos documentos do curso.

Estado: a construir.

## Um curso é uma lista ordenada de conteúdos

| Conceito | Significado | No esquema |
| --- | --- | --- |
| Curso | Um documento, ou mais, adaptado a um nível de público e a um setor | `course` |
| Conteúdo | Uma peça de estudo do curso | `course_content` |
| Formato | Tutorial, flashcards ou quiz | `course_content.format` |
| Foco | O assunto da peça. O produto usa o foco para buscar os trechos do documento | `course_content.focus` |
| Ordem | A posição do conteúdo na lista do curso | `course_content.position` |

A pessoa escolhe as saídas na criação do curso: de uma a três, uma de cada formato. O produto não propõe uma trilha.

O foco de cada conteúdo começa igual ao título do curso. Todo conteúdo usa todos os documentos do curso.

## Todo conteúdo traz três informações de estudo

1. **Conceitos-chave**: os termos que a pessoa precisa dominar. Cada conceito aparece no documento.
2. **Pré-requisitos**: o que a pessoa precisa saber antes.
3. **Tempo estimado**: os minutos de estudo.

O briefing exige as três. O esquema guarda em `key_concepts`, `prerequisites` e `estimated_minutes`.

## Tutorial

Um guia passo a passo.

- Título.
- Resumo de abertura, no layout "Resumo" dos documentos de design.
- Seções, cada uma com um título e um texto em Markdown.

O texto das seções pode ter listas, tabelas e blocos de código.

## Flashcards

Cartões para memorização.

- Título do conjunto.
- Introdução curta, com o contexto do assunto.
- Cartões, cada um com frente, verso e uma dica opcional.

Cada conjunto tem de 8 a 12 cartões.

## Quiz

Perguntas de múltipla escolha com justificativa.

- Título.
- Perguntas, cada uma com enunciado, opções, a opção correta e a justificativa.

Cada quiz tem 5 perguntas, com 4 opções cada. A justificativa explica a resposta com base no documento.

Responder ao quiz na tela, com correção imediata, é um diferencial opcional do briefing. O produto não guarda as respostas.

## O nível de público muda a linguagem e a profundidade

| Nível | Como o conteúdo deve soar |
| --- | --- |
| Não técnico (iniciante ou gestor) | Sem jargão. Usa analogias do dia a dia. Explica para que serve antes de como funciona. |
| Técnico básico (dev júnior ou pleno) | Usa os termos corretos e os explica. Traz passos práticos e exemplos de comando ou código. |
| Técnico avançado (líder técnico ou arquiteto) | Vai direto ao ponto. Trata de limites, alternativas e custos de cada escolha. |

Uma pessoa de fora deve acertar o nível de cada conteúdo sem ver o rótulo.

## O setor muda os exemplos

O produto usa exemplos do setor escolhido. Um curso de Fintech usa exemplos de bancos e pagamentos. Um curso do setor Geral usa exemplos neutros.

O setor não muda os fatos técnicos. Um exemplo do setor não pode trazer um fato que o documento não traz.

## O que fica fora

- Resumo executivo e roteiro de aula.
- Trilha de conteúdos proposta pelo modelo.
- Um conteúdo com vários formatos ao mesmo tempo. Cada conteúdo tem um formato.
- Nível de público por conteúdo. O nível vale para o curso inteiro.
- Escolher quais documentos do curso um conteúdo usa. Todo conteúdo usa todos os documentos indexados.
- Versões anteriores de um conteúdo.
