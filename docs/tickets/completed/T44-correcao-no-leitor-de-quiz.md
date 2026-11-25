---
id: T44
title: Mostre no quiz se a opção escolhida está certa e qual é a correta
blocked_by: [T10, T31]
touches:
  - frontend/src/index.css
  - frontend/src/components/Course/readers/QuizReader.tsx
  - frontend/tests/quiz-reader.spec.ts
  - frontend/tests/generation.spec.ts
executor: agente
size: 2
---

# T44 - Mostre no quiz se a opção escolhida está certa e qual é a correta

## Contexto

Hoje, depois da escolha, o leitor do quiz mostra a justificativa e desabilita as quatro opções com a mesma aparência. A pessoa não sabe se acertou nem qual opção era a correta. T10 deixou a correção fora do escopo de propósito.

As especificações pedem correção e justificativa logo após a escolha. T10 entregou o leitor. T31 entregou o teste que cria um curso, abre o quiz gerado e confere o resultado.

O layout vem de duas capturas das Telas finais:

- [`tela-q2-quiz-correta.png`](../../design/telas-finais/tela-q2-quiz-correta.png): a pessoa acertou.
- [`tela-q3-quiz-incorreta.png`](../../design/telas-finais/tela-q3-quiz-incorreta.png): a pessoa errou, e a tela mostra a correta.

Use as capturas como referência para as opções respondidas e o bloco de resultado. A seção "Onde o design e a especificação divergem" indica as adaptações ao produto.

Leia a seção "Quiz" de `docs/product-specs/conteudos-e-formatos.md` e os tickets T10 e T31 em `docs/tickets/completed/`.

## Escopo

- Guardar no componente a opção escolhida em cada pergunta.
- Marcar a opção escolhida como certa ou errada.
- Quando a pessoa erra, marcar também a opção correta.
- Trocar o bloco "Justificativa" pelo bloco de resultado, com título, justificativa e, no erro, a resposta certa.
- Criar as variáveis de cor `--success-background` e `--success-foreground`.

## Fora do escopo

- A coluna à esquerda com o nome e a marca de cada pergunta (T10 já a tirou).
- Nota, resumo de acertos e botão para refazer o quiz.
- Guardar as respostas no servidor. `conteudos-e-formatos.md` deixa isso fora.
- Uma explicação por opção errada ("Por que não as outras?"). O quiz tem uma só `explanation` por pergunta.
- A moldura, o selo do formato e os metadados (T18).

## Contrato

`QuizReader.tsx` continua a exportar `QuizReader(props: ReaderProps)`. Não mude o nome, a assinatura nem o caminho. Não edite `readers/types.ts`, `ContentReader.tsx`, `ContentView.tsx` nem os outros leitores.

A API já entrega `content.questions` ao leitor, incluindo `correct_index`. O contrato é `QuizContent`, em `backend/app/services/content_schemas.py`. São cinco perguntas. Cada uma tem `prompt`, quatro `options`, `correct_index` inteiro de 0 a 3 e `explanation`. Retire o `transform` que descarta `correct_index` no schema Zod e preserve as validações.

## Comportamento esperado

### Cores novas

Em `frontend/src/index.css`, crie o par de variáveis de sucesso. Siga o modelo de `--destructive-background` e `--destructive-foreground`.

| Variável | `:root` | `.dark` |
| --- | --- | --- |
| `--success-background` | `#d4f0e4` | `oklch(0.269 0 0)` |
| `--success-foreground` | `#14523a` | `oklch(0.765 0.135 163)` |

Registre as duas em `@theme inline`, como `--color-success-background` e `--color-success-foreground`, ao lado de `--color-success`. Os valores de `:root` vêm das telas Q2 e Q3. No tema escuro, o fundo segue `--destructive-background`. O texto de acerto tem contraste de 7,57:1 no tema claro e 7,59:1 no escuro sobre o fundo da opção. [Cálculo de contraste na WCAG 2.2](https://www.w3.org/TR/WCAG22/#dfn-contrast-ratio)

Use só variáveis do tema, pelas classes do Tailwind. Não escreva valor hexadecimal no componente.

### Estado da pergunta

Guarde o índice da opção escolhida por pergunta no lugar do `Set` de justificativas reveladas. O índice 0 também conta como resposta. Ao voltar a uma pergunta respondida, a escolha, as marcas e o bloco de resultado continuam visíveis.

Recarregar a página volta à primeira pergunta e limpa as escolhas. A chave de `Quiz` usa as perguntas validadas, incluindo `correct_index`. Uma atualização com as mesmas perguntas mantém posição e escolhas. Se mudar qualquer dado validado de uma pergunta, mesmo só `correct_index`, reinicie o quiz.

### Opções antes da escolha

Nada muda.

### Opções depois da escolha

As quatro opções ficam desabilitadas. Aplique `disabled:opacity-100` aos quatro botões para sobrepor a opacidade do `Button`. No tema escuro, as classes de fundo e borda de cada estado respondido devem prevalecer sobre `dark:bg-input/30` e `dark:border-input` da variante `outline`.

Depois da escolha, aplique os estilos da tabela.

| Opção | Fundo e borda | Quadrado da esquerda (32 px, raio 6 px) | Texto da opção | Rótulo à direita |
| --- | --- | --- | --- | --- |
| Escolhida e certa | `bg-success-background`, borda de 2 px `border-success-foreground` | Fundo `bg-success-foreground`, ícone `Check` de 18 px em `text-card` | 18 px, peso 600, `text-success-foreground` | "Sua resposta · correta" |
| Escolhida e errada | `bg-destructive-background`, borda de 2 px `border-destructive` | Fundo `bg-destructive`, ícone `X` de 18 px em `text-card` | 18 px, peso 600, `text-destructive-foreground` | "Sua resposta · incorreta" |
| Correta, quando a pessoa errou | O mesmo estilo de "Escolhida e certa" | O mesmo estilo de "Escolhida e certa" | O mesmo estilo de "Escolhida e certa" | "Resposta correta" |
| As outras | `bg-background`, borda de 1 px `border-border` | Letra e borda de 1 px, com fundo `bg-card` | 18 px, peso 400, `text-foreground-tertiary` | Nenhum |

O rótulo tem 14 px, peso 600 e a cor do texto da opção. Alinhe à direita quando houver espaço. Em 360 px de largura, coloque o rótulo abaixo do texto da opção. Quebre linhas longas dentro do botão.

O ícone substitui a letra nas opções marcadas. Use `aria-hidden="true"` e uma classe de tamanho como `size-[18px]` para aplicar 18 px no `Button`. Deixe o rótulo dentro do botão, no nome acessível. Exemplo de nome acessível: "Traces Sua resposta · correta".

Raio, altura mínima e padding das opções não mudam.

### Bloco de resultado

Mantenha a região `role="status"` montada desde antes da escolha, com `aria-atomic="true"`, para o leitor de tela anunciar o resultado. Deixe a região vazia antes da escolha. Depois, mostre o título, a resposta certa se a pessoa errou e a justificativa. [Técnica ARIA22 do W3C](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA22.html)

O bloco fica 20 px abaixo das opções. Use fundo `bg-card`, borda de 1 px, borda esquerda de 6 px, raio de 8 px e padding de 20 px. A cor das bordas segue o resultado.

| Resultado | Cor das bordas | Ícone (20 px) | Título |
| --- | --- | --- | --- |
| Certa | `border-success-foreground` | `CircleCheck` | "Resposta correta", em `text-success-foreground` |
| Errada | `border-destructive` | `CircleX` | "Não foi dessa vez", em `text-destructive` |

Mostre os itens nesta ordem.

1. O ícone com `aria-hidden="true"` e o título na mesma linha, com 8 px entre eles. O título usa Space Grotesk (`font-heading`), 18 px e peso 700.
2. Se a pessoa errou, mostre a resposta certa 10 px abaixo. Use a letra e o texto de `options[correct_index]`. Exemplo: "A resposta certa é C: Traces." Use 15 px, peso 600, altura de linha 1,6 e `text-muted-foreground`.
3. Mostre `explanation` uma vez, 10 px abaixo do item anterior. Use 16 px, altura de linha 1,6 e `text-foreground`.

### Quinta pergunta e navegação

Nada muda em relação a T10. Na quinta pergunta, a pessoa vê as marcas e o bloco de resultado, e a faixa de navegação mostra só "Pergunta anterior".

## Onde o design e a especificação divergem

| Elemento | Telas finais | Este ticket | Motivo |
| --- | --- | --- | --- |
| "Por que não as outras?" e a explicação da opção errada | Telas Q2 e Q3 | Sai. Fica a `explanation` única. | O quiz tem uma só `explanation` por pergunta (`QuizContent`). |
| Cores do acerto | `#d4f0e4` e `#14523a` | Variáveis novas `--success-background` e `--success-foreground` | O tema não tinha um par de sucesso para fundo e texto. `--success` puro sobre fundo claro não tem contraste para texto. |
| Coluna de perguntas com marcas de acerto | Telas Q2 e Q3 | Não entra | T10 já tirou a coluna. |
| "PERGUNTA 2 DE 4" e três opções | Telas Q2 e Q3 | 5 perguntas e 4 opções | Regra de produto, de `conteudos-e-formatos.md`. |
| Frase que identifica a opção correta | "A resposta certa é Traces.", na Q3 | "A resposta certa é C: Traces.", seguida da justificativa. | A letra identifica a posição original da opção. |
| Tema escuro | O design mostra o tema claro. | Use os valores de `.dark` da tabela. | O tema escuro usa o mesmo fundo neutro do estado de erro e adapta a cor dos ícones ao fundo. |

## Testes que mudam

- Em `frontend/tests/quiz-reader.spec.ts`, troque as asserções sobre a aparência igual e o título "Justificativa" pelos cenários abaixo. Mantenha os testes de conteúdo inválido e adapte os de navegação e atualização automática.
- Em `frontend/tests/generation.spec.ts`, ajuste a asserção do quiz no teste "cria um curso e abre os três leitores com conteúdo gerado". A escolha "A git status" acerta. Confira "Resposta correta" no status e mantenha a asserção da justificativa.

## Detalhes técnicos

- Os ícones `Check`, `X`, `CircleCheck` e `CircleX` vêm do `lucide-react`, que já está instalado.
- Use componentes shadcn: o `Button` das opções continua o mesmo. Este ticket não acrescenta dependência: `frontend/package.json` e `bun.lock` não mudam.
- Em `index.css`, acrescente só as linhas das duas variáveis e os dois registros em `@theme inline`. Não mude outras variáveis.
- Este ticket não cria rota. `frontend/src/routeTree.gen.ts` não pode aparecer no diff.
- Nos testes, siga o `setup` de `quiz-reader.spec.ts`: sessão vazia, `createUser`, `createCourse` com um quiz `succeeded` e `logInUser`.
- Concentre o diff nesses quatro arquivos e mire um PR abaixo de 400 linhas.

## Critérios de aceite

- [x] Depois de uma escolha certa, a opção escolhida aparece com o estilo de acerto e o rótulo "Sua resposta · correta", e o bloco de resultado mostra "Resposta correta" e a justificativa.
- [x] Depois de uma escolha errada, a opção escolhida aparece com o estilo de erro e o rótulo "Sua resposta · incorreta". A opção correta aparece com o estilo de acerto e o rótulo "Resposta correta". O bloco mostra "Não foi dessa vez", a justificativa e "A resposta certa é ...".
- [x] As outras opções ficam desabilitadas, sem marca, com o texto em `text-foreground-tertiary`.
- [x] O acerto e o erro aparecem por texto e ícone. A região de status anuncia o resultado após a escolha.
- [x] Em ambos os temas, os textos de correção têm contraste de pelo menos 4,5:1, e os ícones de acerto e erro têm pelo menos 3:1 contra o próprio fundo. Em 360 px, as opções e o bloco de resultado cabem sem rolagem horizontal.
- [x] Ao voltar a uma pergunta respondida, as marcas e o bloco continuam visíveis. Recarregar a página ou receber um quiz alterado limpa as respostas.
- [x] `index.css` tem `--success-background` e `--success-foreground` em `:root` e `.dark`, registradas em `@theme inline`. Nenhum componente tem valor hexadecimal.
- [x] Anexe ao PR capturas do produto rodando, conforme o passo 7 de `docs/tickets/README.md`. Mostre acerto e erro em tema claro a 1440 px, erro a 360 px e erro em tema escuro. Anexe a saída do Playwright para `quiz-reader.spec.ts` e `generation.spec.ts`.
- [x] Responda pelo teclado e confira o anúncio de acerto e erro com um leitor de tela. Registre o resultado no PR.
- [x] Os testes Playwright que já existem passam.
- [x] `bun run lint` e `bun run build` passam.

## Cenários de teste

Em `frontend/tests/quiz-reader.spec.ts`, com as perguntas que o arquivo já define (a correta muda de posição a cada pergunta):

1. Na primeira pergunta, confira que o status tem `aria-atomic="true"` e está vazio. Escolha a opção de `correct_index`. O botão dela tem no nome "Sua resposta · correta". O status mostra "Resposta correta" e a justificativa. O texto "A resposta certa é" fica ausente. Confira que as quatro opções estão desabilitadas e que "Próxima pergunta" está habilitado.
2. Na segunda pergunta, escolha "A Logs". O botão escolhido tem no nome "Sua resposta · incorreta". O botão de "Métricas" tem "Resposta correta". Os outros dois mantêm a letra e o texto no nome. A região de status mostra "Não foi dessa vez", "A resposta certa é C: Métricas." e a justificativa. Confira que as quatro opções estão desabilitadas.
3. Em tema claro e escuro, confira o fundo e a borda calculados pelo navegador para uma resposta errada, a correta e uma opção sem marca. Compare com as cores da tabela. A opacidade das quatro opções é 1. Em 360 px, confira a quebra do rótulo e a ausência de corte ou rolagem horizontal.
4. Volte para a primeira pergunta com "Pergunta anterior". A marca de acerto e o bloco "Resposta correta" continuam visíveis.
5. Recarregue a página. A primeira pergunta aparece com as opções habilitadas, sem marca e sem bloco de resultado.
6. Responda à quinta pergunta. As marcas e o bloco aparecem, e a faixa de navegação mostra só "Pergunta anterior".
7. No teste de atualização automática, confira que perguntas iguais preservam a posição e o resultado. Troque só o `correct_index` de uma pergunta na atualização seguinte. O leitor volta à primeira pergunta, com opções habilitadas e status vazio.

## Verificação do aceite

- PR revisado: [#57](https://github.com/No-Country-simulation/g10_equipe1_novamente/pull/57), integrado no commit `0c62871`.
- CI do PR: os 15 checks passaram.
- Revisão automática: três achados, corrigidos nos commits `084501b` e `24b8e14`. O foco do teclado passa ao botão de navegação depois da escolha, com teste. O resultado é anunciado uma vez, numa frase única, e o bloco visual fica fora da árvore de acessibilidade. Os testes conferem a cor e a largura da borda do bloco e a cor do título no acerto e no erro.
- Leitor de tela: o PR registra a conferência no Firefox com Orca 46.1, com um anúncio por resposta.
