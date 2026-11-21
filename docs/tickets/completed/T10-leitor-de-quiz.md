---
id: T10
title: Mostre o quiz publicado, uma pergunta por vez, com justificativa
blocked_by: [T18]
touches:
  - frontend/src/components/Course/readers/QuizReader.tsx
  - frontend/tests/quiz-reader.spec.ts
executor: agente
size: 2
---

# T10 - Mostre o quiz publicado, uma pergunta por vez, com justificativa

## Contexto

T18 entregou a tela de um conteúdo. Hoje `QuizReader` mostra só "O leitor deste formato ainda não está disponível." O quiz tem 5 perguntas, cada uma com 4 opções, a opção correta e a justificativa. `telas.md` define uma pergunta por vez e mostra a justificativa depois da resposta. O produto não guarda as respostas.

A pessoa escolhe uma opção para abrir a justificativa. A correção imediata segue como diferencial opcional do [escopo do MVP](../../product-specs/escopo-do-mvp.md#o-que-entra-se-sobrar-tempo).

Este ticket troca o conteúdo de `QuizReader.tsx`. A moldura, os metadados e o aviso de estado são de T18 e não mudam.

O layout vem da captura [`tela-q1-quiz.png`](../../design/telas-finais/tela-q1-quiz.png): o cartão branco à direita, com o contador, a barra, a pergunta, as opções e os botões.

Leia antes: `docs/product-specs/conteudos-e-formatos.md`, seção "Quiz", `docs/tickets/completed/T18-tela-curso.md`, seção "Contrato", e `backend/app/services/content_schemas.py`, classe `QuizContent`.

## Escopo

- O leitor do quiz com contador, barra de posição, pergunta, opções, justificativa e navegação.
- O aviso para um conteúdo guardado fora do formato do quiz.

## Fora do escopo

- A moldura da tela, os metadados e os avisos de estado (T18, pronto).
- A coluna de perguntas à esquerda da captura. Veja "Onde o design e a especificação divergem".
- Correção imediata, nota, resumo de acertos e botão para refazer o quiz.
- Guardar as respostas. `conteudos-e-formatos.md` deixa isso fora.
- Fidelidade, clareza e trechos citados (T38).

## Contrato

### Módulos que este ticket usa

Do `master`. Não edite esses arquivos.

```ts
// frontend/src/components/Course/readers/types.ts (T18)
export interface ReaderProps {
  content: { [key: string]: unknown }
}
```

A forma do quiz vem de `QuizContent`, em `backend/app/services/content_schemas.py`:

```python
class QuizQuestion(StrictModel):
    prompt: Text  # 1 caractere ou mais
    options: list[Text]  # exatamente 4, sem repetição
    correct_index: int  # de 0 a 3
    explanation: Text


class QuizContent(StrictModel):
    questions: list[QuizQuestion]  # exatamente 5
```

### O que este ticket muda

`frontend/src/components/Course/readers/QuizReader.tsx` continua a exportar `QuizReader(props: ReaderProps)`. Não mude o nome, a assinatura nem o caminho.

## Comportamento esperado

### Conteúdo no formato do quiz

Use `zod` para validar `QuizContent`. Exija os tipos indicados, textos com ao menos um caractere após `trim()`, 5 perguntas, 4 opções por pergunta e `correct_index` inteiro de 0 a 3. Compare as opções após `trim()`, com distinção entre maiúsculas e minúsculas, como no backend. Ignore campos extras no leitor. `correct_index` serve apenas para conferir o formato dos dados.

Com `content` válido, o leitor mostra um `Card` centralizado, com borda de 1 px, raio de 12 px, fundo `bg-card` e largura máxima de 900 px:

- Na parte de cima, com padding de 24 px:
    - o rótulo "PERGUNTA N DE T", com a regra dos rótulos em caixa alta de T18 (12 px, peso 600, espaçamento de 0,08 em, `text-foreground-tertiary`);
    - uma barra de posição de 4 px de altura, com fundo `bg-muted` e a parte cheia `bg-foreground`, na largura N/T. Use `role="progressbar"`, `aria-valuemin=1`, `aria-valuemax=T`, `aria-valuenow=N`, `aria-valuetext="Pergunta N de T"` e o nome acessível "Posição no quiz";
    - a pergunta, como `h3`, em Space Grotesk (`font-heading`), 28 px, altura de linha 1,25, peso 700;
    - as 4 opções, uma por linha, com 12 px entre elas;
    - depois da escolha, a justificativa.
- Na parte de baixo, uma faixa com padding de 24 px, linha superior de 1 px e fundo `bg-muted/50`. Mostre "Pergunta anterior" à esquerda. Da primeira à quarta pergunta, mostre também "Próxima pergunta" à direita. Em telas de até 360 px, mostre um botão por linha.

### As opções

Cada opção é um `Button` com `variant="outline"`, na largura do cartão, com altura mínima de 64 px, padding de 16 px, raio de 8 px e texto de 18 px alinhado à esquerda. O botão cresce quando o texto quebra linha. À esquerda fica a letra (A, B, C ou D) em um quadrado de 32 px, com borda de 1 px e raio de 6 px.

Qualquer opção revela a mesma justificativa. Guarde apenas se a justificativa de cada pergunta foi revelada. Depois da escolha, desabilite as quatro opções com a mesma aparência, sem marcar a escolhida nem a correta.

### Justificativa

Depois da escolha, mostre o rótulo "Justificativa" e o texto de `explanation` abaixo das opções, com 16 px e altura de linha 1,5. Mantenha a região montada com `role="status"` para anunciar o texto quando ele aparecer.

### Navegação

- "Pergunta anterior" é um `Button` com `variant="outline"`, o ícone `ChevronLeft` e altura mínima de 48 px. Ele fica desabilitado na primeira pergunta.
- Da primeira à quarta pergunta, "Próxima pergunta" fica desabilitado até a escolha. Use o estilo do botão escuro de `DocumentsStep.tsx` (T07), com altura mínima de 48 px.
- Na quinta pergunta, a pessoa pode abrir a justificativa como nas anteriores. A faixa de navegação mostra só "Pergunta anterior".
- Ao voltar para uma pergunta já respondida, a justificativa continua visível e as quatro opções continuam desabilitadas.
- A posição e as justificativas abertas ficam no componente durante a leitura. Recarregar a página ou receber outro conjunto de perguntas volta à primeira pergunta e esconde as justificativas. Uma atualização automática com as mesmas perguntas preserva o estado.

### Conteúdo fora do formato

Quando `content` não passa no schema, por exemplo `{}`, o leitor mostra um `Alert` com o texto "Não foi possível mostrar este conteúdo, porque ele não está no formato esperado." e nada mais. A frase é a mesma de T08 e T09. Cada leitor tem a sua cópia, para os três tickets rodarem ao mesmo tempo sem conflito.

## Onde o design e a especificação divergem

| Elemento | Telas finais | Este ticket | Motivo |
| --- | --- | --- | --- |
| Coluna à esquerda com o nome de cada pergunta e as marcas de acerto | Tela Q1 | Sai | O formato não tem um nome curto por pergunta. O contador e a barra mostram a posição. |
| "PERGUNTA 2 DE 4" e três opções | Tela Q1 | 5 perguntas e 4 opções | Regra de produto, de `conteudos-e-formatos.md`. |
| Selo "Quiz comentado" com o ícone `ListChecks` | Tela Q1 | Selo de T18: "Quiz", com o ícone `CircleQuestionMark` | T18 já decidiu o texto e o ícone. |
| Justificativa | Não aparece na captura Q1 | Abaixo das opções, depois da escolha | `telas.md` pede justificativa depois da resposta. |
| Aviso de conteúdo fora do formato | Não aparece | `Alert` com a frase acima. Proposta. | `telas.md`: uma mensagem de erro diz o que aconteceu. |

## Testes que mudam

Nenhum teste que já existe muda. `frontend/tests/course.spec.ts` não abre um quiz com `content`.

## Detalhes técnicos

- Use o `zod` 4 já instalado (`4.6.5` no `bun.lock`). Defina o schema dentro de `QuizReader.tsx`.
- Use componentes shadcn onde houver: `Card`, `Button` e `Alert` já existem em `frontend/src/components/ui/`. Este ticket não acrescenta dependência: `frontend/package.json` e `bun.lock` não mudam.
- Use só as variáveis de cor de `frontend/src/index.css`. Não escreva valor hexadecimal.
- Não edite `ContentReader.tsx`, `ContentView.tsx`, `readers/types.ts`, os outros leitores, `frontend/tests/course.spec.ts` nem `frontend/tests/utils/`.
- Este ticket não cria rota. `frontend/src/routeTree.gen.ts` não pode aparecer no diff.
- Nos testes, use uma sessão vazia, crie o usuário com `createUser`, crie o curso com `createCourse` e entre com `logInUser`, como em `course.spec.ts`. O seed permite criar um quiz `succeeded` com `content` válido ou inválido para testar a tela real.

## Critérios de aceite

- [x] Um quiz válido mostra uma pergunta por vez, com "PERGUNTA N DE 5", a barra e as 4 opções com as letras A a D.
- [x] Qualquer escolha revela apenas a justificativa e desabilita as quatro opções com a mesma aparência, sem indicar acerto ou erro.
- [x] Da primeira à quarta pergunta, "Próxima pergunta" só funciona depois da escolha. Ao voltar, a justificativa aberta continua visível.
- [x] Na quinta pergunta, a pessoa pode abrir a justificativa e voltar às anteriores. A interface não oferece resultado nem opção de refazer.
- [x] Um `content` fora do formato mostra o aviso, sem erro no console.
- [x] Nenhum componente tem valor hexadecimal.
- [x] Os testes Playwright que já existem passam.
- [x] `bun run lint` e `bun run build` passam.

## Cenários de teste

Em `frontend/tests/quiz-reader.spec.ts`, com um usuário novo por teste e um curso com um só quiz, que abre direto em `/courses/{id}`. As 5 perguntas têm a opção correta em posições diferentes.

1. A tela mostra "PERGUNTA 1 DE 5", a pergunta 1 como `h3` e 4 botões de opção, com as letras A a D. "Pergunta anterior" e "Próxima pergunta" estão desabilitados. A justificativa não aparece.
2. Na primeira pergunta, escolha a opção que corresponde a `correct_index`. Na segunda, escolha outra opção. Nos dois casos, a região de status mostra a justificativa da pergunta. Confira que as quatro opções ficam desabilitadas, nenhuma indica acerto ou erro e "Próxima pergunta" fica habilitado.
3. Use "Pergunta anterior" para voltar à primeira pergunta. A justificativa fica visível e as quatro opções continuam desabilitadas.
4. Chegue à quinta pergunta e escolha uma opção. A justificativa fica visível e a faixa de navegação só mostra "Pergunta anterior".
5. Recarregue a página. A primeira pergunta aparece com as opções habilitadas e sem a justificativa.
6. Teste três entradas inválidas. Uma tem 4 perguntas, outra tem duas opções iguais após `trim()` e a terceira tem `correct_index: 4`. Em cada caso, a tela mostra só o aviso no lugar do leitor, sem emitir erro no console.
7. Abra a justificativa da primeira pergunta de um quiz `running` e avance. Intercepte uma consulta automática do curso e devolva as mesmas perguntas. A posição se mantém e a primeira justificativa continua aberta ao voltar. Em outra consulta, devolva cinco perguntas novas. A primeira aparece com as opções habilitadas e sem a justificativa.

## Verificação do aceite

- PR revisado: [#38](https://github.com/No-Country-simulation/g10_equipe1_novamente/pull/38), integrado no commit `830fdc9`.
- CI do PR: todos os checks obrigatórios passaram, com escopo dentro de `touches`.
- Revisão automática: um achado, o raio das opções era 10 px. O commit `2c7812f` aplicou 8 px.
- Testes: 85 testes Playwright passaram no Chromium, sete deles do quiz. `bun run lint`, `bun run build` e os hooks passaram.
