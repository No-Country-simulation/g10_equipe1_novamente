---
id: T44
title: Mostre no quiz se a opção escolhida está certa e qual é a correta
blocked_by: [T10]
touches:
  - frontend/src/index.css
  - frontend/src/components/Course/readers/QuizReader.tsx
  - frontend/tests/quiz-reader.spec.ts
executor: agente
size: 2
---

# T44 - Mostre no quiz se a opção escolhida está certa e qual é a correta

## Contexto

Hoje, depois da escolha, o leitor do quiz mostra a justificativa e desabilita as quatro opções com a mesma aparência. A pessoa não sabe se acertou nem qual opção era a correta. T10 deixou a correção fora do escopo de propósito.

As specs já pedem a correção: `conteudos-e-formatos.md` diz que "a pessoa responde ao quiz na tela e vê a correção e a justificativa na hora", e `escopo-do-mvp.md` lista "Quiz com correção e justificativa na tela". Este ticket alinha o leitor a essas specs.

O layout vem de duas capturas das Telas finais:

- [`tela-q2-quiz-correta.png`](../design/telas-finais/tela-q2-quiz-correta.png): a pessoa acertou.
- [`tela-q3-quiz-incorreta.png`](../design/telas-finais/tela-q3-quiz-incorreta.png): a pessoa errou, e a tela mostra a correta.

Este ticket traz as medidas, as cores e os textos de que você precisa. Você não precisa abrir o Drive. As capturas mostram elementos que não entram, como a coluna de perguntas à esquerda e o selo "Quiz comentado". Siga este ticket quando os dois diferem.

Leia antes: `docs/tickets/completed/T10-leitor-de-quiz.md`, `docs/product-specs/conteudos-e-formatos.md`, seção "Quiz", e `frontend/src/components/Course/readers/QuizReader.tsx`.

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

A forma do quiz não muda. Ela vem de `QuizContent`, em `backend/app/services/content_schemas.py`: 5 perguntas, cada uma com `prompt`, 4 `options`, `correct_index` de 0 a 3 e `explanation`. Hoje o schema `zod` do leitor descarta `correct_index` no `transform`. Mantenha o campo no resultado do schema e mantenha as mesmas validações.

## Comportamento esperado

### Cores novas

Crie em `frontend/src/index.css` o par de variáveis de sucesso, no mesmo modelo do par de erro (`--destructive-background` e `--destructive-foreground`):

| Variável | `:root` | `.dark` |
| --- | --- | --- |
| `--success-background` | `#d4f0e4` | `oklch(0.269 0 0)` |
| `--success-foreground` | `#14523a` | `oklch(0.765 0.135 163)` |

Registre as duas em `@theme inline`, como `--color-success-background` e `--color-success-foreground`, ao lado de `--color-success`. Os valores de `:root` vêm do design. Os de `.dark` seguem o padrão do par de erro.

Use só variáveis do tema, pelas classes do Tailwind. Não escreva valor hexadecimal no componente.

### Estado da pergunta

Guarde, por pergunta, o índice da opção escolhida, por exemplo em um `Map<number, number>`. Isso substitui o `Set` de justificativas reveladas: uma pergunta está respondida quando tem uma opção guardada. As regras de T10 sobre navegação, recarga e atualização automática continuam iguais. Ao voltar a uma pergunta respondida, as marcas e o bloco de resultado continuam visíveis.

### Opções antes da escolha

Nada muda.

### Opções depois da escolha

As quatro opções ficam desabilitadas. O `Button` aplica `disabled:opacity-50`. Anule isso com `disabled:opacity-100`, para as cores continuarem legíveis.

Cada opção recebe um de três estilos:

| Opção | Fundo e borda | Quadrado da esquerda (32 px, raio 6 px) | Texto da opção | Rótulo à direita |
| --- | --- | --- | --- | --- |
| Escolhida e certa | `bg-success-background`, borda de 2 px `border-success-foreground` | Fundo `bg-success-foreground`, ícone `Check` de 18 px em `text-white` | 18 px, peso 600, `text-success-foreground` | "Sua resposta · correta" |
| Escolhida e errada | `bg-destructive-background`, borda de 2 px `border-destructive` | Fundo `bg-destructive`, ícone `X` de 18 px em `text-white` | 18 px, peso 600, `text-destructive-foreground` | "Sua resposta · incorreta" |
| Correta, quando a pessoa errou | O mesmo estilo de "Escolhida e certa" | O mesmo estilo de "Escolhida e certa" | O mesmo estilo de "Escolhida e certa" | "Resposta correta" |
| As outras | `bg-background`, borda de 1 px `border` | A letra, como antes, com fundo `bg-card` | 18 px, peso 400, `text-foreground-tertiary` | Nenhum |

O rótulo à direita tem 14 px, peso 600 e a mesma cor do texto da opção. Ele fica alinhado à direita (`ml-auto`). Em telas estreitas, ele desce para baixo do texto. O ícone substitui a letra. Marque o ícone com `aria-hidden="true"`. O rótulo fica dentro do botão e entra no nome acessível, por exemplo "Traces Sua resposta · correta".

Raio, altura mínima e padding das opções não mudam.

### Bloco de resultado

O bloco substitui o rótulo "Justificativa" e o texto de T10. Ele continua dentro da região `role="status"`, que fica montada o tempo todo, 24 px abaixo das opções.

O bloco tem fundo `bg-card`, borda de 1 px, borda esquerda de 4 px, raio de 8 px e padding de 20 px. A cor das bordas segue o resultado:

| Resultado | Cor das bordas | Ícone (20 px) | Título |
| --- | --- | --- | --- |
| Certa | `border-success-foreground` | `CircleCheck` | "Resposta correta", em `text-success-foreground` |
| Errada | `border-destructive` | `CircleX` | "Não foi dessa vez", em `text-destructive` |

De cima para baixo:

1. O ícone e o título, na mesma linha, com 8 px entre eles. O título usa Space Grotesk (`font-heading`), 18 px, peso 700.
2. 10 px abaixo, a `explanation`, com 16 px, altura de linha 1,6 e `text-foreground`.
3. Só quando a pessoa errou: 10 px abaixo, "A resposta certa é C: Traces.", com a letra e o texto da opção correta. 15 px, altura de linha 1,6 e `text-muted-foreground`. O trecho "A resposta certa é C:" fica em peso 600.

### Quinta pergunta e navegação

Nada muda em relação a T10. Na quinta pergunta, a pessoa vê as marcas e o bloco de resultado, e a faixa de navegação mostra só "Pergunta anterior".

## Onde o design e a especificação divergem

| Elemento | Telas finais | Este ticket | Motivo |
| --- | --- | --- | --- |
| "Por que não as outras?" e a explicação da opção errada | Telas Q2 e Q3 | Sai. Fica a `explanation` única. | O quiz tem uma só `explanation` por pergunta (`QuizContent`). |
| Cores do acerto | `#d4f0e4` e `#14523a` | Variáveis novas `--success-background` e `--success-foreground` | O tema não tinha um par de sucesso para fundo e texto. `--success` puro sobre fundo claro não tem contraste para texto. |
| Coluna de perguntas com marcas de acerto | Telas Q2 e Q3 | Não entra | T10 já tirou a coluna. |
| "PERGUNTA 2 DE 4" e três opções | Telas Q2 e Q3 | 5 perguntas e 4 opções | Regra de produto, de `conteudos-e-formatos.md`. |
| Tema escuro | Não aparece | Valores de `.dark` acima. Proposta. | O design só desenha o tema claro. |

## Testes que mudam

`frontend/tests/quiz-reader.spec.ts`, de T10, confere que nenhuma opção indica acerto ou erro e procura o rótulo "Justificativa". Troque essas verificações pelos cenários abaixo. Os outros testes de T10 continuam iguais.

## Detalhes técnicos

- Os ícones `Check`, `X`, `CircleCheck` e `CircleX` vêm do `lucide-react`, que já está instalado.
- Use componentes shadcn: o `Button` das opções continua o mesmo. Este ticket não acrescenta dependência: `frontend/package.json` e `bun.lock` não mudam.
- Em `index.css`, acrescente só as linhas das duas variáveis e os dois registros em `@theme inline`. Não mude outras variáveis.
- Este ticket não cria rota. `frontend/src/routeTree.gen.ts` não pode aparecer no diff.
- Nos testes, siga o `setup` de `quiz-reader.spec.ts`: sessão vazia, `createUser`, `createCourse` com um quiz `succeeded` e `logInUser`.

## Critérios de aceite

- [ ] Depois de uma escolha certa, a opção escolhida aparece com o estilo de acerto e o rótulo "Sua resposta · correta", e o bloco de resultado mostra "Resposta correta" e a justificativa.
- [ ] Depois de uma escolha errada, a opção escolhida aparece com o estilo de erro e o rótulo "Sua resposta · incorreta". A opção correta aparece com o estilo de acerto e o rótulo "Resposta correta". O bloco mostra "Não foi dessa vez", a justificativa e "A resposta certa é ...".
- [ ] As outras opções ficam desabilitadas, sem marca, com o texto em `text-foreground-tertiary`.
- [ ] O acerto e o erro aparecem também por texto e ícone, não só por cor.
- [ ] Ao voltar a uma pergunta respondida, as marcas e o bloco continuam visíveis. Recarregar a página apaga as respostas.
- [ ] `index.css` tem `--success-background` e `--success-foreground` em `:root` e `.dark`, registradas em `@theme inline`. Nenhum componente tem valor hexadecimal.
- [ ] O PR traz evidência anexada, conforme o passo 7 de `docs/tickets/README.md`: uma captura de tela da pergunta com acerto e uma da pergunta com erro, a 1440 px de largura, uma captura com erro a 360 px e a saída do Playwright de `quiz-reader.spec.ts`.
- [ ] Os testes Playwright que já existem passam.
- [ ] `bun run lint` e `bun run build` passam.

## Cenários de teste

Em `frontend/tests/quiz-reader.spec.ts`, com as perguntas que o arquivo já define (a correta muda de posição a cada pergunta):

1. Na primeira pergunta, escolha a opção de `correct_index`. O botão dela tem no nome "Sua resposta · correta". Nenhum botão tem "incorreta" nem "Resposta correta". A região de status mostra "Resposta correta" e a justificativa, e não mostra "A resposta certa é".
2. Na segunda pergunta, escolha uma opção errada. O botão escolhido tem no nome "Sua resposta · incorreta". O botão da opção correta tem "Resposta correta". Os outros dois botões não têm rótulo. A região de status mostra "Não foi dessa vez", a justificativa e "A resposta certa é C: Métricas." (a letra e o texto da correta). Confira que as quatro opções estão desabilitadas.
3. Confira as cores pela classe ou pelo estilo calculado: a opção certa usa `--success-background`, a errada usa `--destructive-background` e as opções sem marca não usam nenhuma das duas. A opacidade das opções desabilitadas é 1.
4. Volte para a primeira pergunta com "Pergunta anterior". A marca de acerto e o bloco "Resposta correta" continuam visíveis.
5. Recarregue a página. A primeira pergunta aparece com as opções habilitadas, sem marca e sem bloco de resultado.
6. Responda à quinta pergunta. As marcas e o bloco aparecem, e a faixa de navegação mostra só "Pergunta anterior".
