---
id: T17
title: Monte a tela "Cursos", com a lista, os estados e a atualização automática
blocked_by: [T02, T06]
touches:
  - frontend/src/routes/_layout/index.tsx
  - frontend/src/routes/_layout/courses/index.tsx
  - frontend/src/routes/_layout/courses/$courseId/route.tsx
  - frontend/src/routeTree.gen.ts
  - frontend/src/components/Common/TopNav.tsx
  - frontend/src/components/Courses/CourseCard.tsx
  - frontend/src/lib/courses.ts
  - frontend/src/hooks/useAuth.ts
  - frontend/tests/courses.spec.ts
  - frontend/tests/utils/course.ts
  - frontend/tests/utils/user.ts
  - frontend/tests/auth.setup.ts
  - frontend/tests/login.spec.ts
  - frontend/tests/navigation.spec.ts
executor: agente
size: 3
---

# T17 - Monte a tela "Cursos", com a lista, os estados e a atualização automática

## Contexto

`docs/product-specs/telas.md` define a tela "Cursos" em `/courses`: a pessoa vê seus cursos com título, nível e estado, abre um curso e clica em "Novo curso". A navegação chama essa tela de "Home". T06 deixou "Home" apontando para `/`, que ainda mostra a saudação do template.

T02 entregou `GET /api/v1/courses/` e a rota de seed. Este ticket entrega a lista. A tela de um curso entra em T18, na mesma onda.

Leia antes: `docs/product-specs/telas.md`, `docs/product-specs/criar-curso.md`, seção "Estados que a pessoa vê", e `frontend/src/components/Common/TopNav.tsx`.

## Escopo

- Rota `/courses`, com a lista de cursos da pessoa.
- Estados da lista: carregando, vazia, com erro e com cursos.
- Atualização a cada 3 segundos enquanto algum conteúdo está na fila ou em geração.
- "Home" e `/` levam a `/courses`.
- Moldura da rota `/courses/$courseId`, para o cartão ter um destino.

## Fora do escopo

- Conteúdo da tela de um curso (T18).
- Busca, filtro e paginação. `telas.md` deixa busca e filtro fora do MVP.
- Excluir um curso (T33).

## Contrato

### Módulos que este ticket usa

De `@/client`, gerado por T02. Não edite `frontend/src/client/`.

```ts
CoursesService.readCourses(): Promise<{ data: CoursesPublic }>

type CoursesPublic = { data: Array<CourseSummary>; count: number }
type CourseSummary = {
  id: string
  title: string
  audience_level: AudienceLevel
  status: CourseStatus
  niche: NichePublic
  created_at: string
  updated_at: string
  contents: Array<ContentSummary>
}
type ContentSummary = {
  id: string
  format: ContentFormat
  status: GenerationStatus
  position: number
  title: string | null
}
```

A API devolve só os cursos da pessoa, do mais novo ao mais antigo.

### Módulos que este ticket cria

`frontend/src/lib/courses.ts` e `frontend/tests/utils/course.ts` também são criados por T18, na mesma onda. Crie os dois arquivos exatamente com o conteúdo abaixo, sem acrescentar nem tirar nada. Dois arquivos idênticos não geram conflito. Se você precisa de outro nome ou função, crie em um arquivo seu.

`frontend/src/lib/courses.ts`:

```ts
import type {
  AudienceLevel,
  ClarityLevel,
  ContentFormat,
  CourseStatus,
  GenerationStatus,
} from "@/client"

export const POLL_INTERVAL_MS = 3000

export const coursesQueryKey = ["courses"] as const

export const courseQueryKey = (courseId: string) =>
  ["courses", courseId] as const

export const AUDIENCE_LABELS: Record<AudienceLevel, string> = {
  non_technical: "Não técnico",
  technical_basic: "Técnico básico",
  technical_advanced: "Técnico avançado",
}

export const COURSE_STATUS_LABELS: Record<CourseStatus, string> = {
  initializing: "Gerando",
  ready: "Pronto",
  failed: "Falhou",
}

export const CONTENT_STATUS_LABELS: Record<GenerationStatus, string> = {
  pending: "Na fila",
  running: "Gerando",
  succeeded: "Pronto",
  failed: "Falhou",
}

export const FORMAT_LABELS: Record<ContentFormat, string> = {
  tutorial: "Tutorial",
  flashcards: "Flashcards",
  quiz: "Quiz",
}

export const CLARITY_LABELS: Record<ClarityLevel, string> = {
  low: "Baixa",
  medium: "Média",
  high: "Alta",
}

export function hasActiveContent(
  contents: Array<{ status: GenerationStatus }>,
): boolean {
  return contents.some(
    (content) => content.status === "pending" || content.status === "running",
  )
}
```

`frontend/tests/utils/course.ts`:

```ts
// Note: the `PrivateService` is only available when generating the client
// for local environments
import { type PrivateCourseCreate, PrivateService } from "../../src/client"
import { client } from "../../src/client/client.gen"

client.setConfig({
  baseURL: `${process.env.VITE_API_URL}`,
})

export const createCourse = async (body: PrivateCourseCreate) => {
  const response = await PrivateService.createCourse({ body })
  return response.data
}
```

`frontend/src/routes/_layout/courses/$courseId/route.tsx` é a moldura da rota `/courses/$courseId`. Ela tem só o título da aba e um `Outlet`. T18 cria a página em `frontend/src/routes/_layout/courses/$courseId/index.tsx` e não edita a moldura.

```tsx
import { createFileRoute, Outlet } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/courses/$courseId")({
  component: Outlet,
  head: () => ({
    meta: [
      {
        title: "Curso - NovaMente",
      },
    ],
  }),
})
```

A consulta da lista usa a chave `coursesQueryKey`. T27 invalida essa chave depois de criar um curso.

## Comportamento esperado

### Rotas e navegação

- `/courses` exige login, como as outras rotas de `_layout`. O título da aba é "Cursos - NovaMente".
- `/` redireciona para `/courses`. Troque o componente de `frontend/src/routes/_layout/index.tsx` por um `beforeLoad` que levanta `redirect({ to: "/courses" })`. A saudação "Que bom ter você de volta!" deixa de existir.
- Em `TopNav.tsx`, a aba "Home" leva a `/courses`. A aba fica ativa só em `/courses`, com a mesma regra exata de hoje. Mude só o valor de `to`.
- O login, o cadastro e o logo continuam navegando para `/`. O redirecionamento leva a pessoa a `/courses`.

Decisão: `telas.md` diz que "Home" é a lista de cursos e não lista uma tela de saudação. Este ticket remove a saudação de `/`. O PR #8 ("tela de home") propõe outra tela, com busca, sugestão de temas, progresso e desempenho, que `telas.md` deixa fora do MVP. Este ticket não usa nada do PR #8.

### Tela

De cima para baixo:

1. Uma linha com o título "Cursos" (`h1`, Space Grotesk, 40 px, peso 700) e, à direita, o botão "Novo curso", que leva a `/courses/new`.
2. A lista, em uma grade de cartões: 1 coluna abaixo de 640 px, 2 colunas de 640 px a 1023 px e 3 colunas a partir de 1024 px.

Cada cartão (`CourseCard`) mostra:

| Elemento | Regra |
| --- | --- |
| Título do curso | Texto em `h2`. Corta em duas linhas. |
| Nível | `AUDIENCE_LABELS[course.audience_level]`. |
| Estado | Um `Badge` com `COURSE_STATUS_LABELS[course.status]`. |

O cartão inteiro é um link para `/courses/$courseId`. O nome acessível do link é o título do curso.

As cores do `Badge` de estado vêm das variáveis de T06: "Pronto" usa `--success`, "Falhou" usa `--destructive-background` com texto `--destructive-foreground`, e "Gerando" usa `--muted`. Um curso "Gerando" ou "Falhou" nunca aparece com a cor de "Pronto".

### Estados da lista

| Estado | O que a tela mostra |
| --- | --- |
| Carregando | Três `Skeleton` no lugar dos cartões. |
| Vazia | O texto "Você ainda não tem cursos." e o botão "Criar o primeiro curso", que leva a `/courses/new`. |
| Erro | Um `Alert` de erro com "Não foi possível carregar os cursos." e o botão "Tentar novamente", que refaz a consulta. |
| Com cursos | A grade de cartões, na ordem da API. |

### Atualização automática

A consulta se repete a cada `POLL_INTERVAL_MS` enquanto `hasActiveContent` é verdadeiro para os conteúdos de algum curso da lista. Quando nenhum conteúdo está `pending` ou `running`, a consulta para de se repetir.

Pendência: os documentos de design lidos no Drive não desenham a lista de cursos. O modelo de telas que mostra a Home não estava acessível quando este ticket foi escrito. A grade, o conteúdo do cartão e os textos dos estados vazio e de erro são uma proposta deste ticket, a partir de `telas.md`. Uma pessoa confere com o modelo na revisão.

## Detalhes técnicos

- Use componentes shadcn em toda a interface, sem HTML cru para elementos que têm componente: `Card`, `Badge`, `Button`, `Alert` e `Skeleton` já existem em `frontend/src/components/ui/`. Este ticket não acrescenta dependência: `frontend/package.json` e `bun.lock` não mudam.
- Use `useQuery` com `refetchInterval` em forma de função, que lê os dados da consulta e devolve `POLL_INTERVAL_MS` ou `false`.
- `frontend/src/routeTree.gen.ts` é gerado. T18 também o muda. Em um conflito, faça `rebase` no `master` e rode `cd frontend && bun run build`. Nunca junte as duas versões à mão.
- `route.tsx` dentro de uma pasta é o arquivo de layout dessa pasta no roteamento por arquivos do TanStack Router. Confira na documentação da versão instalada. Se o gerador não aceitar a moldura como está no contrato, pare e relate.
- Depois deste ticket e antes de T18, `/courses/$courseId` mostra só a navegação. Isso é esperado.
- T07 e T18 rodam na mesma onda. Não edite `frontend/src/routes/_layout/courses/new.tsx`, `frontend/src/components/NewCourse/` nem `frontend/src/components/Course/`.
- Nos testes, crie um usuário próprio com `createUser` e entre com `logInUser`. Crie os cursos com `createCourse`, de `frontend/tests/utils/course.ts`, que chama `POST /api/v1/private/courses/`. O usuário padrão do projeto é dividido entre os arquivos de teste, e a lista dele muda.

### Ajustes nos testes que já existem

O login passa a terminar em `/courses`, sem a saudação.

- `frontend/tests/utils/user.ts`, função `logInUser`: espere a URL `/courses` e o título "Cursos" no lugar da URL `/` e da saudação.
- `frontend/tests/auth.setup.ts`: espere a URL `/courses`.
- `frontend/tests/login.spec.ts`: nas três passagens que esperam `/` e a saudação, espere `/courses` e o título "Cursos".
- `frontend/tests/navigation.spec.ts`: os testes que abrem `/` passam a abrir `/courses`.

## Critérios de aceite

- [ ] `/courses` mostra os cursos da pessoa com título, nível e estado, do mais novo ao mais antigo.
- [ ] A lista trata os estados carregando, vazia e com erro.
- [ ] A lista se atualiza a cada 3 segundos só enquanto há conteúdo na fila ou em geração.
- [ ] "Home", o login e `/` levam a `/courses`.
- [ ] O cartão abre `/courses/$courseId`.
- [ ] `frontend/src/lib/courses.ts`, `frontend/tests/utils/course.ts` e a moldura da rota têm o conteúdo exato do contrato.
- [ ] Os testes Playwright que já existem passam, com os ajustes acima.
- [ ] `bun run lint` e `bun run build` passam.

## Cenários de teste

Em `frontend/tests/courses.spec.ts`, com um usuário novo por teste:

1. Usuário sem cursos: a tela mostra "Você ainda não tem cursos." e "Criar o primeiro curso" abre `/courses/new`.
2. Seed de três cursos, nesta ordem: "Curso A" `ready` com um tutorial `succeeded`, "Curso B" `failed` com um tutorial `failed` e "Curso C" `initializing` com um tutorial `pending`, com níveis diferentes. A tela mostra os cartões na ordem C, B, A, cada um com o rótulo do nível e o estado "Gerando", "Falhou" e "Pronto".
3. O clique no cartão "Curso A" leva a `/courses/{id}`, com o `id` devolvido pelo seed.
4. Um curso de outro usuário não aparece na lista.
5. Com "Curso C" (`pending`) na lista, um seed de "Curso D" feito depois de a tela abrir aparece em até 6 segundos, sem recarregar a página.
6. Com só "Curso A" (`succeeded`) na lista, a tela não faz nenhum pedido a `/api/v1/courses/` nos 5 segundos seguintes ao primeiro. Conte os pedidos com `page.on("request")`.
7. Com `GET /api/v1/courses/` respondendo 500 (`page.route`), a tela mostra "Não foi possível carregar os cursos." Depois de liberar a rota, "Tentar novamente" mostra a lista.
8. Depois do login, a URL é `/courses` e a aba "Home" tem `aria-current="page"`. Abrir `/` leva a `/courses`.
9. O botão "Novo curso" leva a `/courses/new`.
