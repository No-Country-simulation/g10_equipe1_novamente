---
id: T45
title: Mostre a frase do produto também no cadastro, alinhe o rodapé dos cartões de curso e troque o ícone do nível
blocked_by: [T06, T17]
touches:
  - frontend/src/components/Common/AuthLayout.tsx
  - frontend/src/routes/login.tsx
  - frontend/src/components/Courses/CourseCard.tsx
  - frontend/tests/login.spec.ts
  - frontend/tests/sign-up.spec.ts
  - frontend/tests/courses.spec.ts
executor: agente
size: 2
---

# T45 - Mostre a frase do produto também no cadastro, alinhe o rodapé dos cartões de curso e troque o ícone do nível

## Contexto

Este ticket junta três ajustes pequenos de interface. Os três vêm de uma revisão das telas e não mudam regra de produto.

**Cadastro sem a frase do produto.** No login, a coluna da esquerda mostra o logo e, abaixo dele, a frase "Cursos personalizados a partir dos seus materiais, no nível que você escolher." No cadastro, a mesma coluna mostra só o logo.

- `frontend/src/routes/login.tsx` passa a frase a `AuthLayout` pela propriedade `tagline`.
- `frontend/src/routes/signup.tsx` usa `<AuthLayout>` sem a propriedade.
- Só essas duas rotas usam `AuthLayout`.

**Rodapé dos cartões desalinhado.** Na lista de cursos, a linha com o nível de público e o selo do estado fica em alturas diferentes em cartões da mesma fileira. O estado não causa a diferença: o título usa `line-clamp-2`, e a linha vem logo depois dele. Um título em duas linhas empurra a linha para baixo. O cartão já ocupa toda a altura da fileira (`h-full`), mas a linha não fica presa ao fim dele.

**Ícone do nível quase invisível.** Na mesma linha, um ícone do lucide indica o nível de público: `SignalLow`, `SignalMedium` ou `SignalHigh`, com 16 px. Esses ícones desenham só as barras do nível e omitem as demais. Com 16 px, `SignalLow` vira um ponto e uma barra de menos de 3 px, e a pessoa mal vê o ícone. A pessoa pediu um ícone melhor. Só `CourseCard.tsx` usa esse ícone. As outras telas mostram o nível só em texto: o selo da tela de conteúdo, os metadados da tela do curso e as opções do passo 2 de "Novo curso".

Capturas em `docs/design/ajustes-finais/`:

- [`01-login-1440.png`](../../design/ajustes-finais/01-login-1440.png): login, com a frase.
- [`02-signup-1440.png`](../../design/ajustes-finais/02-signup-1440.png): cadastro, sem a frase.
- [`04-cursos-lista-1440.png`](../../design/ajustes-finais/04-cursos-lista-1440.png): dois cartões, com a linha de baixo desalinhada e o ícone do nível quase invisível.

## Escopo

- A mesma frase no login e no cadastro.
- A linha do nível e do estado presa ao fim de cada cartão de curso.
- Um indicador do nível visível e fácil de distinguir nos dois temas.

## Fora do escopo

- Mudar o texto da frase.
- Exibir a coluna do logo e da frase em telas abaixo de 1024 px.
- Alterar o selo do estado ou o título do cartão.
- Mostrar o indicador do nível em outras telas. Elas mostram o nível só em texto, e T47 edita a tela de conteúdo.
- Mudar a grade da lista de cursos.

## Comportamento esperado

### Frase no login e no cadastro

- Em `frontend/src/components/Common/AuthLayout.tsx`, a frase passa a ser fixa: tire a propriedade `tagline` e mostre sempre o texto "Cursos personalizados a partir dos seus materiais, no nível que você escolher." no mesmo lugar e com as mesmas classes de hoje.
- Em `frontend/src/routes/login.tsx`, tire a propriedade `tagline` da chamada a `AuthLayout`.
- `frontend/src/routes/signup.tsx` não muda.

Assim, as duas telas mostram a mesma frase, e uma tela nova que use `AuthLayout` também.

### Rodapé dos cartões

Em `frontend/src/components/Courses/CourseCard.tsx`, prenda `CardContent` ao fim do cartão com `mt-auto`. O `Card` do shadcn já usa `flex flex-col`, e o cartão já tem `h-full`. Não mude outras classes.

Em uma mesma fileira da grade, a linha do nível e do estado fica na mesma altura em todos os cartões, com título em uma ou em duas linhas.

### Indicador do nível

Em `CourseCard.tsx`, use três barras crescentes desenhadas com elementos `span` e classes do Tailwind.

- As barras têm 4 px de largura, 2 px de espaço entre elas e alturas de 6, 10 e 16 px. Alinhe as três pela base e use `shrink-0` no grupo.
- As barras ativas usam `bg-foreground`. As inativas usam `bg-border-strong`.
- "Não técnico" ativa a primeira barra, "Técnico básico" as duas primeiras e "Técnico avançado" as três.
- Use o atributo `data-active` só nas barras ativas. Omita o atributo nas inativas.
- O indicador continua com `aria-hidden="true"`. O texto do nível continua visível ao lado dele, e o nome acessível do cartão continua o título.
- Tire a importação de `SignalLow`, `SignalMedium` e `SignalHigh` e o mapa `audienceIcons`.

## Detalhes técnicos

- O Playwright usa o perfil "Desktop Chrome", com 1280 px de largura. Nessa largura, a coluna esquerda de `AuthLayout` está visível e a lista de cursos tem três colunas.
- Não edite `frontend/src/routes/signup.tsx`, `frontend/src/components/ui/card.tsx` nem `frontend/src/routes/_layout/courses/index.tsx`.

## Critérios de aceite

- [x] A partir de 1024 px, o login e o cadastro mostram a frase "Cursos personalizados a partir dos seus materiais, no nível que você escolher." abaixo do logo.
- [x] `AuthLayout` não tem mais a propriedade `tagline`.
- [x] Em uma fileira de cartões de curso, a linha do nível e do estado fica na mesma altura, com títulos de uma e de duas linhas.
- [x] Cada cartão mostra três barras, com uma, duas ou três barras fortes conforme o nível, e as inativas em uma cor mais fraca, nos temas claro e escuro.
- [x] As barras ativas têm pelo menos 3:1 de contraste com o fundo do cartão em ambos os temas. [WCAG 2.2, critério 1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)
- [x] O texto do nível continua visível ao lado das barras.
- [x] Anexe ao PR as capturas do cadastro com a frase e de três cartões na mesma fileira, um de cada nível, com o rodapé alinhado. Use o produto rodando a 1440 px, conforme o passo 7 de `docs/tickets/README.md`. Capture os cartões no tema escuro e no claro, para mostrar as barras nos dois.
- [x] O lint, o build e os testes Playwright passam.

## Cenários de teste

1. Em `frontend/tests/sign-up.spec.ts`: a página de cadastro mostra a frase.
2. Em `frontend/tests/login.spec.ts`: a página de login continua mostrando a frase.
3. Em `frontend/tests/courses.spec.ts`, use `seed` para criar dois cursos da mesma pessoa, com o mesmo nível e estado. Use um título curto e outro que quebre em duas linhas. Depois de carregar as fontes, confira que os cartões começam na mesma altura e que o `h2` do título longo é mais alto. Compare a posição vertical dos selos de estado, com tolerância de 1 px.
4. Em `frontend/tests/courses.spec.ts`, amplie o teste "lista cursos em ordem com níveis e estados e abre o cartão". Em cada cartão, confira três barras visíveis no indicador e o texto do nível. As três primeiras barras de "Técnico avançado", as duas primeiras de "Técnico básico" e só a primeira de "Não técnico" têm `data-active`. No cartão "Não técnico", compare a cor de fundo calculada da primeira barra com a da segunda. As cores devem ser diferentes.

## Verificação do aceite

- PR revisado: [#59](https://github.com/No-Country-simulation/g10_equipe1_novamente/pull/59), integrado no commit `2b2fa66`.
- CI do PR: todos os checks passaram.
- Revisão automática: nenhum achado. A revisão mediu no Chromium os selos de estado na mesma altura com títulos de uma e duas linhas, as barras de nível com 1, 2 e 3 barras ativas e contraste de cerca de 18:1 no tema claro e 17:1 no escuro. Três testes novos falham no código anterior.
- Teste de ponta a ponta no `master` em 26/11/2026: os 141 testes Playwright passaram. No produto rodando com Gemini e OCI reais, um curso com os três formatos ficou pronto em cerca de 35 segundos, os três leitores abriram e a exclusão limpou o prefixo no bucket.
