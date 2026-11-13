---
id: T06
title: Troque a barra lateral pela navegação no topo e aplique fontes e cores do design
blocked_by: []
touches:
  - frontend/package.json
  - bun.lock
  - frontend/src/main.tsx
  - frontend/src/index.css
  - frontend/src/routes/_layout.tsx
  - frontend/src/routes/_layout/courses/new.tsx
  - frontend/src/routeTree.gen.ts
  - frontend/src/components/Common/TopNav.tsx
  - frontend/src/components/Common/UserMenu.tsx
  - frontend/src/components/Common/Appearance.tsx
  - frontend/src/components/NewCourse/StepList.tsx
  - frontend/src/components/Sidebar/
  - frontend/tests/navigation.spec.ts
  - frontend/tests/user-settings.spec.ts
executor: agente
size: 3
---

# T06 - Troque a barra lateral pela navegação no topo e aplique fontes e cores do design

## Contexto

O frontend ainda usa a barra lateral do template. `docs/product-specs/telas.md` define uma navegação no topo, com "Home" e "Novo curso", e todas as telas do design assumem essa navegação. As fontes do design também não estão carregadas, embora `telas.md` diga que estão.

Este ticket entrega a moldura que as outras telas usam: a navegação, as fontes, as cores e a base da tela `/courses/new`. O passo 1 dessa tela entra em T07, e a tela "Cursos", em T17.

Leia antes: `docs/product-specs/telas.md` e `frontend/src/routes/_layout.tsx`.

## Escopo

- Navegação no topo, com menu da conta e botão de tema.
- Fontes e cores do design no tema claro.
- Rota `/courses/new` com o título e a coluna de etapas.
- Remoção da barra lateral.

## Fora do escopo

- Conteúdo do passo 1 (T07) e dos passos 2 e 3 (T27).
- Tela "Cursos" em `/courses` (T17). "Home" leva a `/` por enquanto.
- Redesenho das telas de acesso e de dados da conta.
- Cores do tema escuro. O tema escuro continua funcionando com as cores atuais.

## Comportamento esperado

### Navegação

Uma faixa no topo de toda tela com login, com fundo `#FFFFFF` e borda inferior de 1 px `#D5D9D2`.

| Posição | Elemento | Regra |
| --- | --- | --- |
| Esquerda | Logo | Componente `Logo` atual. Leva a `/`. |
| Esquerda, depois do logo | Abas "Home" e "Novo curso" | "Home" leva a `/`. "Novo curso" leva a `/courses/new`. |
| Direita | Botão de tema | Mantém `data-testid="theme-button"` e as três opções atuais. |
| Direita | Menu da conta | Avatar com as iniciais e o nome. Mantém `data-testid="user-menu"` e os itens "Configurações da conta" e "Sair". |

A aba da rota atual tem fundo `#E3E6E1`, texto `#11151C` e peso 600. As outras têm texto `#3D434D`, peso 400 e nenhum fundo. Em `/settings`, nenhuma aba fica ativa.

Abaixo de 640 px de largura, o nome some e o avatar fica. As abas continuam visíveis.

O documento de design da navegação (História 1) não estava acessível quando este ticket foi escrito. Use estes valores: altura de 64 px, padding lateral de 40 px, abas com 16 px, padding de 8 px por 14 px e raio de 6 px. Uma pessoa confere com o design na revisão.

### Fontes

| Uso | Família | Pesos |
| --- | --- | --- |
| Títulos | Space Grotesk | 700 |
| Texto | IBM Plex Sans | 400 e 600 |
| Nomes de arquivo e código | IBM Plex Mono | 400 |

### Cores do tema claro

| Uso | Hex |
| --- | --- |
| Texto principal | `#11151C` |
| Texto de apoio | `#3D434D` |
| Texto terciário | `#555B66` |
| Borda forte: campos e botões brancos | `#7A818C` |
| Borda: cartões e navegação | `#D5D9D2` |
| Fundo da página | `#F6F7F4` |
| Fundo de cartão | `#FFFFFF` |
| Fundo neutro: aba ativa, etapa futura, botão desabilitado | `#E3E6E1` |
| Laranja: ação principal e etapa atual | `#F26B21` |
| Texto sobre o laranja | `#11151C` |
| Verde: etapa concluída | `#3FB68B` |
| Azul: rótulos | `#1F4FD8` |
| Erro: borda e ícone, fundo, texto | `#B3261E`, `#FBE3E1`, `#7F1D17` |

### Tela `/courses/new`

A rota exige login, como as outras rotas de `_layout`. Ela mostra:

1. O título "Novo curso" (Space Grotesk, 40 px, peso 700).
2. À esquerda, a coluna de etapas, com 280 px de largura: 1 "Documentos", 2 "Perfil", 3 "Formatos".
3. À direita, um cartão com fundo `#FFFFFF`, borda `#D5D9D2`, raio de 12 px e altura mínima de 560 px, com o rótulo "ETAPA 1 DE 3" e o título "Documentos".

Cada etapa tem um círculo de 32 px com o número e, ao lado, o nome. A etapa atual tem círculo `#F26B21` e nome em peso 600. A etapa concluída tem círculo `#3FB68B` e um ícone de visto. A etapa futura tem círculo `#E3E6E1` e não responde ao clique.

Neste ticket a etapa 1 é a atual e as outras são futuras. Em janelas estreitas, a coluna de etapas fica acima do cartão.

## Detalhes técnicos

- Carregue as fontes com os pacotes `@fontsource/space-grotesk`, `@fontsource/ibm-plex-sans` e `@fontsource/ibm-plex-mono`, importados em `frontend/src/main.tsx`. A demonstração não pode depender de um servidor de fontes externo.
- Em `frontend/src/index.css`, mapeie as cores para as variáveis que os componentes já usam (`--background`, `--foreground`, `--card`, `--border`, `--input`, `--muted`, `--muted-foreground`, `--primary`, `--primary-foreground`, `--destructive`) e crie variáveis para as cores sem equivalente. Declare as famílias de fonte no bloco `@theme`.
- `StepList` recebe a etapa atual e a lista de etapas concluídas. T07 e T27 usam o mesmo componente.
- Mova o menu da conta de `components/Sidebar/User.tsx` para `components/Common/UserMenu.tsx` e tire a dependência de `useSidebar`. Faça o mesmo em `Appearance.tsx`.
- Apague `frontend/src/components/Sidebar/`. Não apague `frontend/src/components/ui/sidebar.tsx`.
- `frontend/tests/utils/user.ts` espera a URL `/` e o texto "Que bom ter você de volta!" depois do login. Não mude a tela `/`.
- Não edite `docs/product-specs/telas.md`. A frase "As cores e as fontes da marca já estão aplicadas no frontend" passa a ser verdadeira com este ticket.

## Critérios de aceite

- [ ] Nenhuma tela mostra a barra lateral.
- [ ] As abas levam às rotas certas e a aba ativa segue a rota.
- [ ] O menu da conta abre as configurações e faz o logout.
- [ ] As três famílias de fonte carregam sem pedido a outro domínio.
- [ ] `/courses/new` mostra o título, as três etapas e o cartão, e manda para `/login` sem login.
- [ ] Os testes Playwright que já existem passam.
- [ ] `bun run lint` e `bun run build` passam.

## Cenários de teste

Em `frontend/tests/navigation.spec.ts`:

1. Depois do login, a navegação mostra "Home" e "Novo curso", e "Home" está ativa.
2. O clique em "Novo curso" abre `/courses/new`, e a aba "Novo curso" fica ativa.
3. `/courses/new` mostra "Novo curso", as etapas "Documentos", "Perfil" e "Formatos", e "ETAPA 1 DE 3".
4. Sem login, `/courses/new` redireciona para `/login`.
5. Em `/settings`, nenhuma aba está ativa.

Em `frontend/tests/user-settings.spec.ts`, ajuste o nome do teste que cita a barra lateral.
