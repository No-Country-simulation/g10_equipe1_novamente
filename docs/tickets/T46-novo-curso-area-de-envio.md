---
id: T46
title: Redesenhe a área de envio do passo 1 e dê a mesma altura às duas abas
blocked_by: [T07]
touches:
  - frontend/src/components/NewCourse/DocumentsStep.tsx
  - frontend/tests/new-course.spec.ts
executor: agente
size: 2
---

# T46 - Redesenhe a área de envio do passo 1 e dê a mesma altura às duas abas

## Contexto

O passo 1 de "Novo curso" (T07) tem duas abas: "Enviar arquivo" e "Digitar texto". Uma revisão das telas achou dois problemas.

**O cartão muda de altura ao trocar de aba.** Nas capturas de 1440 px, o cartão tem 560 px na aba "Enviar arquivo" e 659 px na aba "Digitar texto". O botão "Continuar" muda de posição. Só o painel ativo ocupa espaço. A área de envio é mais baixa que o painel de texto, cujo campo tem 176 px de altura.

**A área de envio tem outro layout.** Hoje ela é uma faixa horizontal: o ícone, "Arraste os arquivos até aqui" e "MD ou PDF, até 5 MiB" à esquerda, e o botão "Escolher arquivos" à direita. A pessoa quer o layout do bloco [File Upload Dropzone 1](https://www.shadcnblocks.com/component/file-upload/file-upload-dropzone-1), do shadcnblocks: tudo empilhado e centralizado dentro de uma borda tracejada e arredondada.

Capturas em `docs/design/ajustes-finais/`:

- [`05-novo-curso-passo1-1440.png`](../design/ajustes-finais/05-novo-curso-passo1-1440.png) e [`05-novo-curso-passo1-360.png`](../design/ajustes-finais/05-novo-curso-passo1-360.png): aba "Enviar arquivo" hoje.
- [`06-novo-curso-passo1-texto-1440.png`](../design/ajustes-finais/06-novo-curso-passo1-texto-1440.png) e [`06-novo-curso-passo1-texto-360.png`](../design/ajustes-finais/06-novo-curso-passo1-texto-360.png): aba "Digitar texto" hoje.
- [`referencia-dropzone.png`](../design/ajustes-finais/referencia-dropzone.png): a referência do layout novo.

O bloco do shadcnblocks é Pro. Use a imagem pública como referência visual e mantenha o `input` nativo e os eventos de envio atuais.

Leia `docs/tickets/completed/T07-novo-curso-passo-1.md` e a seção "Tela Novo curso em 3 passos" de `docs/product-specs/telas.md`.

## Escopo

- O layout novo da área de envio, empilhado e centralizado.
- A mesma altura para os painéis das duas abas, em qualquer largura.

## Fora do escopo

- Mudar os tipos aceitos, o limite de 5 MiB ou o limite de 3 documentos.
- Mudar as linhas dos documentos aceitos e recusados.
- Mostrar avisos (toasts) para arquivos recusados. As linhas recusadas já mostram o motivo.
- Tornar a área inteira clicável. Só o botão abre a escolha de arquivos, como hoje.
- Acrescentar diceui, react-dropzone ou outro pacote.
- Mudar o painel "Digitar texto", exceto pelo que a altura igual pede.
- Mudar os passos 2 e 3.

## Decisão

A linha de ajuda da área de envio continua "MD ou PDF, até 5 MiB", sem citar o limite de 3 documentos. O contador acima das abas já mostra esse limite.

## Comportamento esperado

### Área de envio

Mantenha a `section` atual, com o mesmo `aria-label` ("Área de envio de arquivos"), o mesmo `aria-disabled`, os mesmos eventos de arraste e o mesmo `input` oculto. Mude só o layout:

1. Mantenha uma coluna centralizada na horizontal e na vertical em todas as larguras. Tire `sm:flex-row`, `sm:text-left` e o `flex-1` do grupo de texto, para que os quatro elementos fiquem juntos no centro.
2. Mantenha esta ordem de cima para baixo.
    - o ícone `Upload` dentro de um círculo pequeno com borda (por exemplo, `size-12 rounded-full border bg-card`), com o ícone em `size-5` e `text-muted-foreground`;
    - "Arraste os arquivos até aqui", em `font-semibold`;
    - A linha de ajuda, hoje "MD ou PDF, até 5 MiB", em `text-sm text-muted-foreground`;
    - o botão "Escolher arquivos", `variant="outline"`, como hoje.
3. A borda continua tracejada, com 2 px e cantos de 12 px. Os estados continuam: borda mais forte no `hover`, borda e fundo da cor primária durante o arraste, e opacidade de 60% quando o limite de documentos foi atingido.

Use os rótulos em português do produto. A imagem serve de referência para a disposição dos elementos.

### Mesma altura nas duas abas

Os painéis das duas abas ocupam a mesma área, e a altura dessa área é a do painel mais alto. Assim, trocar de aba não muda a altura do cartão em nenhuma largura de tela.

- Envolva os dois `TabsContent` em um contêiner `grid` e ponha os dois na mesma célula (`col-start-1 row-start-1`).
- Passe `forceMount` aos dois `TabsContent`. Com `forceMount`, o Radix mantém os dois painéis montados e marca o inativo com `data-state="inactive"`.
- Esconda o painel inativo com `data-[state=inactive]:invisible`. Ele continua ocupando espaço, mas sai da tela, da ordem do Tab e da árvore de acessibilidade.
- Use `flex` no painel de envio e `flex-1` na `section`, para que a borda tracejada preencha o painel. A altura da grade acompanha o conteúdo mais alto, inclusive quando aparece um erro no painel de texto.

O texto digitado já fica no estado de `DocumentsStep`, então ele se mantém ao trocar de aba, como hoje.

## Detalhes técnicos

- Na versão instalada de Radix Tabs, `forceMount` mantém a presença do painel e o atributo `hidden` fica ausente. Os dois painéis mantêm `role="tabpanel"` no DOM. `visibility: hidden` exclui o inativo da busca por papel acessível.
- O cartão do passo é o `Card` de `frontend/src/routes/_layout/courses/new.tsx`. Nos testes, filtre `[data-slot="card"]` pelo texto "ETAPA 1 DE 3".
- Os testes existentes procuram "Arraste os arquivos até aqui", o botão "Escolher arquivos" e a região "Área de envio de arquivos". Eles continuam passando sem mudança.
- Não edite `frontend/src/components/ui/tabs.tsx`, `documents.ts`, os outros passos nem `frontend/src/routes/_layout/courses/new.tsx`.

## Onde a referência e o produto divergem

| Referência | Produto |
| --- | --- |
| "Drag & drop files here" | "Arraste os arquivos até aqui" |
| "Or click to browse (max 5 files, up to 5MB each)" | O produto aceita MD ou PDF de até 5 MiB. O contador mostra o limite de 3 documentos. |
| "Browse files" | "Escolher arquivos" |
| Avisos (toasts) para arquivos recusados | Linhas recusadas abaixo da área, como hoje |
| Tema claro | Tema claro e escuro, com as cores do projeto |

## Critérios de aceite

- [ ] A área de envio mostra, empilhados e centralizados, o ícone no círculo, o título, a linha dos limites e o botão.
- [ ] A escolha de arquivos e o arraste continuam aplicando os limites. Os documentos aceitos e recusados aparecem na lista.
- [ ] A altura do painel ativo e do cartão do passo e a posição de "Continuar" se mantêm ao trocar de aba a 1440 px e a 360 px.
- [ ] A tela, a navegação por Tab e a árvore de acessibilidade expõem só o painel ativo e seus controles.
- [ ] Nenhum pacote novo.
- [ ] Anexe ao PR capturas do produto rodando nas duas abas, a 1440 px e a 360 px, no tema escuro, conforme o passo 7 de `docs/tickets/README.md`.
- [ ] O lint, o build e os testes Playwright passam.

## Cenários de teste

Em `frontend/tests/new-course.spec.ts`:

1. A 1440 px e a 360 px, meça a altura do painel ativo (`getByRole("tabpanel")`), a altura do cartão e a posição vertical de "Continuar" no documento. Troque de aba e compare as três medidas, com tolerância de 1 px.
2. Na aba "Enviar arquivo", confira a ordem vertical de ícone, título, linha de ajuda e botão. Confira que o botão está centrado na área de envio, com tolerância de 2 px.
3. Em cada aba, confira que a busca por papel acessível retorna só o painel ativo. Com Tab a partir desse painel, o primeiro controle recebe foco: "Escolher arquivos" ou "Texto do documento", conforme a aba. O controle do outro painel fica fora da navegação.
4. Digite texto, troque de aba e volte. O campo mantém o texto.
