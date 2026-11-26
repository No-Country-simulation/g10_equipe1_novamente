---
id: T47
title: Tire as bordas azuis das telas de conteúdo
blocked_by: [T09, T18, T38]
touches:
  - frontend/src/components/Course/ContentPage.tsx
  - frontend/src/components/Course/ContentEvaluation.tsx
  - frontend/src/components/Course/readers/FlashcardsReader.tsx
  - frontend/tests/course.spec.ts
  - frontend/tests/content-evaluation.spec.ts
  - frontend/tests/flashcards-reader.spec.ts
  - docs/design/telas-finais/README.md
executor: agente
size: 1
---

# T47 - Tire as bordas azuis das telas de conteúdo

## Contexto

Tutorial, flashcards e quiz compartilham um cabeçalho com faixa azul e uma seção de avaliação com bordas azuis nos trechos citados. O cartão de flashcards também tem uma borda azul.

O ticket trata destes três usos de `border-info`.

| Onde | Classe | O que a pessoa vê |
| --- | --- | --- |
| `frontend/src/components/Course/ContentPage.tsx`, cabeçalho de `ContentScreen` | `border-b-4 border-info` | Uma faixa azul abaixo do cabeçalho escuro, nas três telas |
| `frontend/src/components/Course/ContentEvaluation.tsx`, item de "Trechos citados" | `border-l-[3px] border-info` | Uma borda azul à esquerda de cada trecho citado |
| `frontend/src/components/Course/readers/FlashcardsReader.tsx`, cartão | `border-2 border-info` e `dark:border-info` | Uma borda azul em volta do cartão |

As Telas finais mostram a faixa e a borda do cartão. Esta é uma decisão nova, que diverge do design.

Capturas em `docs/design/ajustes-finais/`:

- [`11-conteudo-tutorial-1440.png`](../design/ajustes-finais/11-conteudo-tutorial-1440.png): faixa do cabeçalho e borda dos trechos citados.
- [`12-flashcards-frente-1440.png`](../design/ajustes-finais/12-flashcards-frente-1440.png): borda do cartão.
- [`15-quiz-aguardando-1440.png`](../design/ajustes-finais/15-quiz-aguardando-1440.png): faixa do cabeçalho no quiz.

## Escopo

- Tirar as três bordas azuis da tabela.
- Registrar a divergência em `docs/design/telas-finais/README.md`.

## Fora do escopo

- O ícone do formato nos cartões da tela do curso.
- A borda azul das opções marcadas em "Novo curso" (`FormatsStep.tsx` e `ProfileStep.tsx`).
- As cores do quiz depois da resposta (T44).
- Mudar a variável `--info` em `index.css`.

## Decisão

Os links azuis, o selo "PERGUNTA" ou "RESPOSTA" e a instrução "Clique no cartão para ver a resposta" ou "Clique no cartão para ver a pergunta" mantêm a cor atual. No cabeçalho de `ContentScreen`, os links "Voltar ao curso" e "Todos os cursos" já usam cores neutras.

## Comportamento esperado

1. **Cabeçalho.** Tire `border-b-4 border-info` do `header` de `ContentScreen`. O resto do cabeçalho fica igual: fundo, cantos, espaçamento e textos.
2. **Trechos citados.** Tire `border-l-[3px] border-info` do `li` de cada citação. O item mantém o fundo `bg-muted/50`, os cantos e o espaçamento.
3. **Cartão de flashcards.** Tire `border-2 border-info` e `dark:border-info` do botão do cartão. O cartão passa a usar a borda de 1 px da variante `outline` do `Button` (`border`, e `dark:border-input` no tema escuro). O resto das classes fica igual.

Confira o resultado no tema claro e no escuro.

## Documentação

Em `docs/design/telas-finais/README.md`, registre o ajuste de T47 depois do último parágrafo. Liste a faixa do cabeçalho, a borda dos trechos citados e a borda azul do cartão de flashcards. Aponte para as capturas anteriores ao ajuste em `../ajustes-finais/README.md`.

## Detalhes técnicos

- Para achar o cabeçalho nos testes, parta do `h1` com o título do curso e suba até o `header` que o contém. A página tem também o cabeçalho da navegação.
- Não edite `ContentView.tsx`, `ContentReader.tsx`, `QuizReader.tsx`, `TutorialReader.tsx` nem `index.css`.

## Critérios de aceite

- [ ] As telas de tutorial, flashcards e quiz não mostram a faixa azul abaixo do cabeçalho.
- [ ] Os trechos citados não têm borda à esquerda.
- [ ] O cartão de flashcards tem a borda neutra de 1 px da variante `outline`.
- [ ] `docs/design/telas-finais/README.md` registra a divergência.
- [ ] Anexe ao PR capturas do tutorial com trechos citados, dos flashcards e do quiz. Use o produto rodando em tema escuro a 1440 px, conforme o passo 7 de `docs/tickets/README.md`.
- [ ] O lint, o build e os testes Playwright passam.

## Cenários de teste

1. Em `frontend/tests/course.spec.ts`, no teste "abre o tutorial pela grade e volta ao curso", confira `border-bottom-width: 0px` no `header` que contém o `h1` do curso.
2. Em `frontend/tests/content-evaluation.spec.ts`, no teste "mostra a avaliação e os trechos do documento", use `citationItems(page)` e confira `border-left-width: 0px` em cada item.
3. Em `frontend/tests/flashcards-reader.spec.ts`, no teste "mostra um cartão por vez e vira com clique ou teclado", confira `border-top-width: 1px` no botão "Virar cartão". Antes do clique, compare a cor calculada da borda com a do botão "Próximo", que também usa `outline`.
