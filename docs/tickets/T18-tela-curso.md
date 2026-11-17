---
id: T18
title: Monte a tela "Curso", com a lista de conteúdos, os estados e os metadados
blocked_by: [T02, T06]
touches:
  - frontend/src/routes/_layout/courses/$courseId/index.tsx
  - frontend/src/routeTree.gen.ts
  - frontend/src/components/Course/CoursePage.tsx
  - frontend/src/components/Course/ContentView.tsx
  - frontend/src/components/Course/ContentReader.tsx
  - frontend/src/components/Course/readers/types.ts
  - frontend/src/components/Course/readers/TutorialReader.tsx
  - frontend/src/components/Course/readers/FlashcardsReader.tsx
  - frontend/src/components/Course/readers/QuizReader.tsx
  - frontend/src/lib/courses.ts
  - frontend/tests/course.spec.ts
  - frontend/tests/utils/course.ts
executor: agente
size: 3
---

# T18 - Monte a tela "Curso", com a lista de conteúdos, os estados e os metadados

## Contexto

`docs/product-specs/telas.md` define a tela "Curso" em `/courses/$courseId`: a pessoa vê os conteúdos do curso em ordem, com o estado de cada um, e lê um conteúdo. T02 entregou `GET /api/v1/courses/{course_id}` e a rota de seed. Nenhuma tela mostra um curso hoje.

Este ticket entrega a página, os estados e os metadados de estudo. Ele também cria o ponto de encaixe dos leitores: T08 (tutorial), T09 (flashcards) e T10 (quiz) trocam cada um o seu arquivo. A fidelidade, a clareza e os trechos citados entram em T38.

Leia antes: `docs/product-specs/telas.md`, `docs/product-specs/criar-curso.md`, seção "Estados que a pessoa vê", e `docs/product-specs/conteudos-e-formatos.md`.

## Escopo

- Página `/courses/$courseId`, com o cabeçalho do curso.
- Lista de conteúdos em ordem, com um conteúdo aberto por vez.
- Estado de cada conteúdo: na fila, gerando, pronto ou falhou.
- Metadados de estudo de um conteúdo publicado: tempo, conceitos-chave e pré-requisitos.
- Bloco "Materiais usados", com os nomes dos documentos do curso.
- Ponto de encaixe dos leitores, com um arquivo por formato.
- Atualização a cada 3 segundos enquanto algum conteúdo está na fila ou em geração.

## Fora do escopo

- Leitores de tutorial, flashcards e quiz (T08, T09, T10).
- Fidelidade, clareza, observações da revisão e trechos citados (T38).
- Botão "Tentar novamente" (T32). A rota de nova tentativa ainda não existe.
- Excluir o curso (T33).
- Lista de cursos (T17).

## Contrato

### Módulos que este ticket usa

De `@/client`, gerado por T02. Não edite `frontend/src/client/`.

```ts
CoursesService.readCourse({ path: { course_id: string } }): Promise<{ data: CourseDetail }>

type CourseDetail = {
  id: string
  title: string
  audience_level: AudienceLevel
  status: CourseStatus
  niche: NichePublic // { id, slug, name, description }
  created_at: string
  updated_at: string
  contents: Array<ContentPublic>
  documents: Array<DocumentPublic>
}
type ContentPublic = {
  id: string
  format: ContentFormat
  status: GenerationStatus
  position: number
  title: string | null
  content: { [key: string]: unknown } | null
  estimated_minutes: number | null
  key_concepts: Array<string> | null
  prerequisites: Array<string> | null
  grounding_score: number | null
  clarity: ClarityLevel | null
  review_notes: string | null
  oci_object_key: string | null
  error_message: string | null
  updated_at: string
  citations: Array<CitationPublic>
}
type DocumentPublic = {
  id: string
  title: string
  original_filename: string
  mime_type: string
  size_bytes: number
  status: DocumentStatus
  error_message: string | null
}
```

`contents` vem em ordem de `position`. Um curso inexistente ou de outra pessoa responde HTTP 404.

### Módulos que este ticket cria

`frontend/src/lib/courses.ts` e `frontend/tests/utils/course.ts` também são criados por T17, na mesma onda. Crie os dois arquivos exatamente com o conteúdo abaixo, sem acrescentar nem tirar nada. Dois arquivos idênticos não geram conflito. Se você precisa de outro nome ou função, crie em um arquivo seu.

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

Os componentes abaixo são o contrato de T08, T09, T10 e T38. Não mude nome, assinatura nem caminho.

`frontend/src/components/Course/readers/types.ts`:

```ts
export interface ReaderProps {
  /** `ContentPublic.content`, na forma do formato. Veja T05. */
  content: { [key: string]: unknown }
}
```

`frontend/src/components/Course/readers/TutorialReader.tsx`, `FlashcardsReader.tsx` e `QuizReader.tsx` exportam cada um um componente com o nome do arquivo e as props `ReaderProps`. Neste ticket, os três mostram só o texto "O leitor deste formato ainda não está disponível." T08, T09 e T10 trocam cada um o conteúdo do seu arquivo.

`frontend/src/components/Course/ContentReader.tsx`:

```ts
interface ContentReaderProps {
  format: ContentFormat
  content: { [key: string]: unknown }
}

/** Escolhe o leitor pelo formato. T08, T09 e T10 não editam este arquivo. */
export function ContentReader(props: ContentReaderProps): JSX.Element
```

`frontend/src/components/Course/ContentView.tsx`:

```ts
interface ContentViewProps {
  content: ContentPublic
}

/** Mostra um conteúdo: o estado, os metadados e o leitor. T38 acrescenta a avaliação. */
export function ContentView(props: ContentViewProps): JSX.Element
```

`frontend/src/components/Course/CoursePage.tsx`:

```ts
interface CoursePageProps {
  courseId: string
}

export function CoursePage(props: CoursePageProps): JSX.Element
```

A consulta do curso usa a chave `courseQueryKey(courseId)`.

### Rota

T17 cria a moldura `frontend/src/routes/_layout/courses/$courseId/route.tsx`, com o título da aba e um `Outlet`. Este ticket não cria nem edita esse arquivo. Ele cria só a página, em `frontend/src/routes/_layout/courses/$courseId/index.tsx`:

```tsx
import { createFileRoute } from "@tanstack/react-router"

import { CoursePage } from "@/components/Course/CoursePage"

export const Route = createFileRoute("/_layout/courses/$courseId/")({
  component: CourseRoute,
})

function CourseRoute() {
  const { courseId } = Route.useParams()
  return <CoursePage courseId={courseId} />
}
```

A página funciona com e sem a moldura de T17 no `master`.

## Comportamento esperado

### Largura da página

O conteúdo da página fica em uma coluna centralizada, com largura máxima de 880 px. A medida vem do documento de design "NovaMente História 4 - Conteúdo: resumo", do Drive.

### Cabeçalho do curso

- O título do curso (`h1`, Space Grotesk, 40 px, peso 700).
- Três `Badge`: o nível (`AUDIENCE_LABELS`), o setor (`course.niche.name`) e o estado do curso (`COURSE_STATUS_LABELS`).
- Se algum documento tem `status` `failed`, um `Alert` de erro com o título "Um documento falhou" e uma linha por documento que falhou: o `original_filename` e, se existe, o `error_message`.

### Lista de conteúdos

- Com um só conteúdo, a tela mostra esse conteúdo direto, sem lista.
- Com mais de um, a tela mostra abas (`Tabs`), uma por conteúdo, na ordem da API. O rótulo de cada aba é o formato (`FORMAT_LABELS`) seguido do estado (`CONTENT_STATUS_LABELS`), por exemplo "Tutorial Pronto". A primeira aba abre primeiro. A aba escolhida fica em um `useState`.

### Um conteúdo

`ContentView` mostra, de cima para baixo:

1. Um aviso conforme o `status`:

    | `status` | Aviso |
    | --- | --- |
    | `pending` | "Na fila. Este conteúdo espera a vez de ser gerado." |
    | `running` | "Gerando. A tela se atualiza sozinha." |
    | `failed` | Um `Alert` de erro com o título "A geração falhou" e o `error_message`, com as quebras de linha preservadas. Sem `error_message`, o texto é "Não foi possível gerar este conteúdo." |
    | `succeeded` | Nenhum aviso. |

2. O resultado publicado, sempre que `content.content` não é nulo, em qualquer `status`. Uma geração `running` ou `failed` mantém legível o resultado publicado antes (`docs/generated/db-schema.md`).

O resultado publicado mostra:

- O título do conteúdo (`h2`). Sem título, usa o rótulo do formato.
- O tempo estimado, como "N min de estudo", quando `estimated_minutes` não é nulo.
- "Conceitos-chave", com um `Badge` por conceito, quando a lista não é vazia.
- "Pré-requisitos", com uma lista de itens. Com a lista vazia ou nula, o texto "Nenhum".
- `ContentReader`, com o formato e o conteúdo.

### Materiais usados

No fim da página, depois dos conteúdos, um bloco separado por uma linha de 1 px (`--muted`):

- O rótulo "MATERIAIS USADOS": 12 px, peso 600, caixa alta, espaçamento de 0,08 em, cor `--foreground-tertiary`.
- Um item por documento de `course.documents` com `status` diferente de `failed`, na ordem da API, lado a lado e com quebra de linha. Cada item mostra o `original_filename` em IBM Plex Mono (`font-mono`), 13 px, com padding de 6 na vertical e 12 na horizontal, borda de 1 px (`--border`) e raio 6.
- Sem nenhum documento para mostrar, o bloco não aparece.

O bloco vem do design, que lista só os arquivos enviados sem falha.

### Estados da página

| Estado | O que a tela mostra |
| --- | --- |
| Carregando | `Skeleton` no lugar do cabeçalho e do conteúdo. |
| HTTP 404 | "Curso não encontrado." e um link "Voltar para os cursos", para `/`. |
| Outro erro | Um `Alert` de erro com "Não foi possível carregar o curso." e o botão "Tentar novamente". |

### Atualização automática

A consulta se repete a cada `POLL_INTERVAL_MS` enquanto `hasActiveContent(course.contents)` é verdadeiro. Depois disso, ela para de se repetir.

Pendência: o design do Drive só desenha a leitura de um conteúdo ("História 4"). A largura da página e o bloco "Materiais usados" vêm dele. O design não desenha um curso com vários conteúdos nem os estados na fila, gerando e falhou. As abas, a disposição dos metadados e os textos dos avisos são uma proposta deste ticket, a partir de `telas.md`. O botão "Concluir conteúdo" do design não entra, porque `telas.md` deixa a tela de finalização fora do MVP.

Decisão: `telas.md` diz que a tela de um conteúdo que falhou mostra o botão "Tentar novamente". Este ticket mostra só o motivo. O botão entra em T32, junto com a rota de nova tentativa.

## Detalhes técnicos

- Use componentes shadcn em toda a interface, sem HTML cru para elementos que têm componente: `Tabs`, `Badge`, `Alert`, `Skeleton`, `Button` e `Card` já existem em `frontend/src/components/ui/`. Este ticket não acrescenta dependência: `frontend/package.json` e `bun.lock` não mudam.
- Use `useQuery` com `refetchInterval` em forma de função e `retry: false` para o erro 404.
- `frontend/src/routeTree.gen.ts` é gerado. T17 também o muda. Em um conflito, faça `rebase` no `master` e rode `cd frontend && bun run build`. Nunca junte as duas versões à mão.
- T07 e T17 rodam na mesma onda. Não edite `frontend/src/components/Common/TopNav.tsx`, `frontend/src/routes/_layout/index.tsx`, `frontend/tests/utils/user.ts`, `frontend/tests/navigation.spec.ts` nem `frontend/src/components/Courses/`.
- T17 muda o destino de `/` e a função `logInUser`. Nos testes, entre com `logInUser` e abra `/courses/{id}` direto com `page.goto`. Não dependa da tela que aparece depois do login.
- Nos testes, crie um usuário próprio com `createUser` e os cursos com `createCourse`, que chama `POST /api/v1/private/courses/`. O seed não tem campo para `error_message` de documento: confira só o nome do arquivo no alerta.
- O link "Voltar para os cursos" usa `<Link to="/">`. T17 cria `/courses` na mesma onda e faz `/` redirecionar para lá. O tipo do `Link` não aceita `/courses` antes de T17 estar no `master`.

## Critérios de aceite

- [ ] `/courses/$courseId` mostra o cabeçalho, os conteúdos em ordem e o estado de cada um.
- [ ] Um curso com um só conteúdo mostra o conteúdo direto.
- [ ] Um conteúdo que falhou mostra o motivo, e um conteúdo na fila ou em geração não aparece como pronto.
- [ ] Um conteúdo publicado mostra tempo, conceitos-chave e pré-requisitos.
- [ ] "Materiais usados" lista os documentos que não falharam, e só eles.
- [ ] A tela se atualiza a cada 3 segundos só enquanto há conteúdo na fila ou em geração.
- [ ] Um curso inexistente ou de outra pessoa mostra "Curso não encontrado."
- [ ] Os três leitores, `ContentReader`, `ContentView` e os dois arquivos divididos com T17 cumprem o contrato.
- [ ] Os testes Playwright que já existem passam.
- [ ] `bun run lint` e `bun run build` passam.

## Cenários de teste

Em `frontend/tests/course.spec.ts`, com um usuário novo por teste:

1. Curso `ready` com um tutorial `succeeded`, com título, 12 minutos, dois conceitos e um pré-requisito: a tela mostra o título do curso, o nível, o setor "Geral", "Pronto", o título do conteúdo, "12 min de estudo", os dois conceitos e o pré-requisito. Não há abas.
2. O mesmo curso mostra "O leitor deste formato ainda não está disponível."
3. Um tutorial `succeeded` sem pré-requisitos mostra "Nenhum".
4. Curso com três conteúdos, nesta ordem: tutorial `succeeded`, flashcards `pending` e quiz `failed` com `error_message` de duas linhas. As abas aparecem na ordem "Tutorial Pronto", "Flashcards Na fila" e "Quiz Falhou". A aba do quiz mostra "A geração falhou" e as duas linhas. A aba dos flashcards mostra "Na fila."
5. Curso `initializing` com um tutorial `pending`: a tela faz pelo menos 2 pedidos a `/api/v1/courses/{id}` em 8 segundos. Conte os pedidos com `page.on("request")`.
6. Curso com todos os conteúdos `succeeded`: a tela não faz nenhum pedido a `/api/v1/courses/{id}` nos 5 segundos seguintes ao primeiro.
7. Curso `failed` com um documento `failed` chamado `guia.md`: o alerta "Um documento falhou" mostra `guia.md`. A tela não mostra "MATERIAIS USADOS".
8. Um `id` que não existe mostra "Curso não encontrado." O curso de outro usuário mostra o mesmo texto.
9. Sem login, `/courses/{id}` redireciona para `/login`.
10. Curso com os documentos `guia.md` e `notas.md`, os dois `indexed`: o bloco "MATERIAIS USADOS" mostra os dois nomes, nessa ordem.
