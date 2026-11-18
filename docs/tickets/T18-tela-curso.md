---
id: T18
title: Monte a tela "Curso", com os cartões de conteúdo, os estados e os metadados
blocked_by: [T02, T06]
touches:
  - frontend/src/routes/_layout/courses/$courseId/index.tsx
  - frontend/src/routes/_layout/courses/$courseId/contents/$contentId.tsx
  - frontend/src/routeTree.gen.ts
  - frontend/src/components/Course/CoursePage.tsx
  - frontend/src/components/Course/ContentPage.tsx
  - frontend/src/components/Course/ContentCard.tsx
  - frontend/src/components/Course/CourseSummary.tsx
  - frontend/src/components/Course/CourseFallback.tsx
  - frontend/src/components/Course/useCourse.ts
  - frontend/src/components/Course/formatIcons.ts
  - frontend/src/components/Course/ContentView.tsx
  - frontend/src/components/Course/ContentReader.tsx
  - frontend/src/components/Course/readers/types.ts
  - frontend/src/components/Course/readers/TutorialReader.tsx
  - frontend/src/components/Course/readers/FlashcardsReader.tsx
  - frontend/src/components/Course/readers/QuizReader.tsx
  - frontend/tests/course.spec.ts
executor: agente
size: 3
---

# T18 - Monte a tela "Curso", com os cartões de conteúdo, os estados e os metadados

## Contexto

`docs/product-specs/telas.md` define a tela "Curso": a pessoa vê os conteúdos do curso em ordem, com o estado de cada um, e lê um conteúdo. T02 entregou `GET /api/v1/courses/{course_id}` e a rota de seed. T07 e T17 já estão no `master`.

O layout vem só das Telas finais do Drive. As capturas que este ticket usa estão em [`docs/design/telas-finais/`](../design/telas-finais/README.md):

- [`tela-5-curso.png`](../design/telas-finais/tela-5-curso.png): a tela do curso, com a grade de cartões.
- [`tela-6-conteudo-tutorial.png`](../design/telas-finais/tela-6-conteudo-tutorial.png): a tela de um conteúdo.
- [`tela-q1-quiz.png`](../design/telas-finais/tela-q1-quiz.png) e [`tela-f1-flashcards.png`](../design/telas-finais/tela-f1-flashcards.png): a mesma moldura com outros formatos.

Este ticket traz para o texto todas as medidas, cores e textos de que você precisa. Você não precisa abrir o Drive. As capturas mostram elementos que ficam fora do MVP, como o progresso e o botão "Finalizar". Siga este ticket, não a captura, quando os dois diferem.

Este ticket entrega as duas telas, os estados e os metadados de estudo. Ele também cria o ponto de encaixe dos leitores: T08 (tutorial), T09 (flashcards) e T10 (quiz) trocam cada um o seu arquivo. A fidelidade, a clareza e os trechos citados entram em T38.

Leia antes: `docs/product-specs/telas.md`, `docs/product-specs/criar-curso.md`, seção "Estados que a pessoa vê", e `docs/product-specs/conteudos-e-formatos.md`.

## Escopo

- Tela do curso em `/courses/$courseId`: cabeçalho, um cartão por conteúdo e o bloco "Resumo do curso".
- Tela de um conteúdo em `/courses/$courseId/contents/$contentId`: cabeçalho escuro, estado, metadados de estudo e leitor.
- Com um só conteúdo, `/courses/$courseId` mostra a tela do conteúdo direto.
- Estado de cada conteúdo: na fila, gerando, pronto ou falhou.
- Metadados de estudo de um conteúdo publicado: tempo, conceitos-chave e pré-requisitos.
- Ponto de encaixe dos leitores, com um arquivo por formato.
- Atualização a cada 3 segundos enquanto algum conteúdo está na fila ou em geração.

## Fora do escopo

- Leitores de tutorial, flashcards e quiz (T08, T09, T10). O cartão branco do tutorial e a coluna de perguntas ou cartões das capturas são deles.
- Fidelidade, clareza, observações da revisão e trechos citados (T38).
- Botão "Tentar novamente" de um conteúdo que falhou (T32). A rota de nova tentativa ainda não existe.
- Excluir o curso (T33).
- Progresso do curso e tela de finalização. `telas.md` deixa os dois fora do MVP.

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

De `@/lib/courses`, que T17 criou e já está no `master`: `POLL_INTERVAL_MS`, `courseQueryKey`, `AUDIENCE_LABELS`, `CONTENT_STATUS_LABELS`, `FORMAT_LABELS` e `hasActiveContent`. Não edite esse arquivo.

Nos testes, use `createCourse` de `frontend/tests/utils/course.ts`, que já está no `master`. Não edite esse arquivo. `createCourse` devolve o `CourseDetail`, com os `id` dos conteúdos.

### Módulos que este ticket cria

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

Os arquivos abaixo são internos deste ticket. Os nomes servem para evitar conflito com outros tickets. A forma interna fica a seu critério.

| Arquivo | O que tem |
| --- | --- |
| `useCourse.ts` | `useCourse(courseId)`: o `useQuery` do curso, com a chave, o `retry` e o `refetchInterval` de "Atualização automática". As duas telas usam o mesmo hook e dividem o mesmo cache. |
| `CourseFallback.tsx` | O que as duas telas mostram ao carregar, em HTTP 404 e em outro erro. |
| `ContentPage.tsx` | `ContentPage({ courseId, contentId })`, usado pela rota do conteúdo. Exporta também a tela do conteúdo já com os dados, que `CoursePage` usa quando o curso tem um só conteúdo. |
| `ContentCard.tsx` | O cartão de um conteúdo. |
| `CourseSummary.tsx` | O bloco "Resumo do curso". |
| `formatIcons.ts` | O ícone de cada formato. |

### Rotas

T17 criou a moldura `frontend/src/routes/_layout/courses/$courseId/route.tsx`, com o título da aba e um `Outlet`. Este ticket não edita esse arquivo. As duas páginas ficam dentro dela.

`frontend/src/routes/_layout/courses/$courseId/index.tsx`:

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

`frontend/src/routes/_layout/courses/$courseId/contents/$contentId.tsx`:

```tsx
import { createFileRoute } from "@tanstack/react-router"

import { ContentPage } from "@/components/Course/ContentPage"

export const Route = createFileRoute(
  "/_layout/courses/$courseId/contents/$contentId",
)({
  component: ContentRoute,
})

function ContentRoute() {
  const { courseId, contentId } = Route.useParams()
  return <ContentPage courseId={courseId} contentId={contentId} />
}
```

## Comportamento esperado

### Cores e fontes

Use só as variáveis de `frontend/src/index.css`, pelas classes do Tailwind. Não escreva valor hexadecimal nos componentes. A tabela liga cada cor do design à variável que a substitui.

| Uso no design | Valor no design | Classe |
| --- | --- | --- |
| Fundo da página | `#f6f7f4` | `bg-background` (vem do layout) |
| Texto principal, fundo do cabeçalho escuro | `#11151c` | `text-foreground`, `bg-foreground` |
| Texto secundário | `#3d434d` | `text-muted-foreground` |
| Rótulos em caixa alta, tempo | `#555b66` | `text-foreground-tertiary` |
| Bordas de cartão | `#d5d9d2` | `border` |
| Link, faixa azul do cabeçalho | `#1f4fd8` | `text-info`, `border-info` |
| Fundo do ícone do cartão | `#e8edfb` | `bg-info/10` |
| Link no cabeçalho escuro | `#c9d6fa` | `text-background/80` |
| Borda do selo no cabeçalho escuro | `#5b6575` | `border-background/30` |

Títulos usam Space Grotesk (`font-heading`). O resto usa IBM Plex Sans, que já é a fonte padrão. Nomes de arquivo usam IBM Plex Mono (`font-mono`).

Os rótulos em caixa alta ("CURSO", "CONTEÚDO 1 · TUTORIAL", "SETOR") têm 12 px, peso 600, espaçamento de 0,08 em e cor `text-foreground-tertiary`. Escreva o texto já em caixa alta no código, como T07 faz com "ETAPA 1 DE 3". Para o formato, use `FORMAT_LABELS[format].toUpperCase()`.

### Ícones

Cada formato tem um ícone do `lucide-react`, em `formatIcons.ts`:

| Formato | Ícone |
| --- | --- |
| `tutorial` | `SquareCheckBig` |
| `quiz` | `CircleQuestionMark` |
| `flashcards` | `Layers` |

O cartão e o selo do cabeçalho escuro usam o mesmo ícone.

### Selo de estado

Um `Badge` mostra `CONTENT_STATUS_LABELS[content.status]`, com as mesmas cores do `CourseCard` de T17:

| `status` | Texto | Classes |
| --- | --- | --- |
| `succeeded` | Pronto | `bg-success text-white` |
| `failed` | Falhou | `bg-destructive-background text-destructive-foreground` |
| `pending` | Na fila | `bg-muted text-foreground` |
| `running` | Gerando | `bg-muted text-foreground` |

O selo tem 12 px, peso 500, padding de 2 na vertical e 10 na horizontal (`px-2.5`), e cantos redondos (o `Badge` já traz isso).

### Tela do curso, com mais de um conteúdo

Captura: [`tela-5-curso.png`](../design/telas-finais/tela-5-curso.png). A tela usa a largura do layout, como `/courses`. De cima para baixo, com 32 px entre os blocos (`gap-8`):

1. **Cabeçalho.**
    - O link "Todos os cursos", para `/courses`: 15 px, `text-info`, com o ícone `ChevronLeft` de 18 px à esquerda e altura mínima de 44 px.
    - O rótulo "CURSO".
    - O título do curso (`h1`, Space Grotesk, 40 px, altura de linha 42 px, peso 700).
2. **Alerta de documento que falhou**, só se algum documento tem `status` `failed`. Veja "Documento que falhou".
3. **Grade de cartões**, um por conteúdo, na ordem da API. A grade é a mesma de `/courses`: `grid gap-6 sm:grid-cols-2 lg:grid-cols-3`.
4. **"Resumo do curso".**

#### Cartão de um conteúdo

Um `Card` com borda de 1 px, raio de 12 px, fundo `bg-card` e padding de 20 px. De cima para baixo:

| Elemento | Regra |
| --- | --- |
| Ícone e selo | Na mesma linha. À esquerda, o ícone do formato, de 22 px, `text-info`, em um quadrado de 44 px com raio 8 e fundo `bg-info/10`. À direita, o selo de estado. |
| Rótulo | "CONTEÚDO N · FORMATO", em que N é a posição na lista, a partir de 1. Por exemplo, "CONTEÚDO 2 · FLASHCARDS". 14 px abaixo do ícone. |
| Título | `h2`, Space Grotesk, 21 px, altura de linha 1,2, peso 700. Sem `title`, usa `FORMAT_LABELS[format]`. 6 px abaixo do rótulo. |
| Texto de estado | Veja a tabela abaixo. 15 px, altura de linha 1,5, `text-muted-foreground`. 14 px abaixo do título. |
| Tempo | "cerca de N min", quando `estimated_minutes` não é nulo. 14 px, `text-foreground-tertiary`. |
| Botão | "Abrir", em toda a largura, `variant="outline"`, altura de 48 px, 16 px, peso 600. Fica no pé do cartão (`mt-auto`), para os botões da grade se alinharem. |

Texto de estado do cartão:

| `status` | Texto |
| --- | --- |
| `pending` | "Este conteúdo espera a vez de ser gerado." |
| `running` | "A tela se atualiza sozinha." |
| `failed` | O `error_message`, com as quebras de linha preservadas (`whitespace-pre-line`), em `text-destructive-foreground`. Sem `error_message`, "Não foi possível gerar este conteúdo." |
| `succeeded` | Nenhum. |

O botão "Abrir" é um link para `/courses/$courseId/contents/$contentId` quando `content.content` não é nulo, em qualquer `status`. Uma geração `running` ou `failed` mantém legível o resultado publicado antes (`docs/generated/db-schema.md`). Quando `content.content` é nulo, o botão fica desabilitado e não é link. O nome acessível do botão é "Abrir" seguido do título do cartão, por exemplo "Abrir Introdução" (`aria-label`).

#### Resumo do curso

Um `Card` com borda de 1 px, raio de 12 px e padding de 24 px. Em telas a partir de 1024 px, o título fica à esquerda, em uma coluna de 240 px, e os itens ficam em linha, com 40 px entre eles. Em telas menores, tudo fica em coluna.

- O título "Resumo do curso" (`h2`, Space Grotesk, 24 px, peso 700).
- Uma lista de definição (`dl`). Cada rótulo (`dt`) segue a regra dos rótulos em caixa alta. Cada valor (`dd`) tem 15 px, altura de linha 21 px, `text-foreground`.

| Rótulo | Valor |
| --- | --- |
| SETOR | `course.niche.name` |
| NÍVEL | `AUDIENCE_LABELS[course.audience_level]` |
| FORMATOS | Os formatos dos conteúdos, na ordem da API, unidos por vírgula e "e". O primeiro fica como em `FORMAT_LABELS` e os outros em minúscula. Por exemplo, "Tutorial, flashcards e quiz". |
| MATERIAIS | Um item por documento com `status` diferente de `failed`, na ordem da API, lado a lado e com quebra de linha. Cada item mostra o `original_filename` em `font-mono`, 13 px, com padding de 6 na vertical e 12 na horizontal, borda de 1 px e raio 6. Sem nenhum documento para mostrar, o item MATERIAIS não aparece. |

### Tela do curso, com um só conteúdo

`/courses/$courseId` mostra a tela do conteúdo direto, sem cartão. O link do cabeçalho escuro é "Todos os cursos", para `/courses`. Abaixo do conteúdo, a tela mostra o "Resumo do curso", com 32 px de distância.

### Tela de um conteúdo

Captura: [`tela-6-conteudo-tutorial.png`](../design/telas-finais/tela-6-conteudo-tutorial.png). As capturas de quiz e flashcards mostram a mesma moldura.

De cima para baixo, com 32 px entre os blocos:

1. **Cabeçalho escuro.**
2. **Alerta de documento que falhou**, só se algum documento tem `status` `failed`.
3. **`ContentView`**, com o conteúdo.

#### Cabeçalho escuro

Uma faixa na largura da coluna, com fundo `bg-foreground`, texto `text-background`, borda inferior de 4 px `border-info`, raio de 12 px e padding de 20 px na vertical e 32 px na horizontal. No tema escuro, use `dark:bg-card dark:text-card-foreground`.

- Na primeira linha, o link de volta: 15 px, `text-background/80` (no tema escuro, `dark:text-muted-foreground`), com o ícone `ChevronLeft` de 18 px e altura mínima de 44 px.
    - Em `/courses/$courseId/contents/$contentId`: "Voltar ao curso", para `/courses/$courseId`.
    - Em `/courses/$courseId`, com um só conteúdo: "Todos os cursos", para `/courses`.
- Na segunda linha, à esquerda, o título do curso (`h1`, Space Grotesk, 32 px, altura de linha 1,1, peso 700).
- Na segunda linha, à direita, o selo do conteúdo: o ícone do formato, de 16 px, e o texto "Formato · Nível · Setor", por exemplo "Tutorial · Técnico básico · Geral". Use `FORMAT_LABELS`, `AUDIENCE_LABELS` e `course.niche.name`. 14 px, peso 500, borda de 1 px `border-background/30`, cantos redondos, padding de 8 na vertical e 14 na horizontal. Em telas estreitas, o selo desce para baixo do título.

#### `ContentView`

`ContentView` usa a largura da coluna. Cada leitor decide a própria largura: o tutorial de T08 usa um cartão de 800 px, centralizado. De cima para baixo, com 24 px entre os blocos:

1. Um aviso conforme o `status`:

    | `status` | Aviso |
    | --- | --- |
    | `pending` | Um `Alert` com "Na fila. Este conteúdo espera a vez de ser gerado." |
    | `running` | Um `Alert` com "Gerando. A tela se atualiza sozinha." |
    | `failed` | Um `Alert` de erro com o título "A geração falhou" e o `error_message`, com as quebras de linha preservadas. Sem `error_message`, o texto é "Não foi possível gerar este conteúdo." |
    | `succeeded` | Nenhum aviso. |

2. O resultado publicado, sempre que `content.content` não é nulo, em qualquer `status`.

O resultado publicado mostra:

- Um `Card` "Sobre este conteúdo", no mesmo estilo do "Resumo do curso": borda de 1 px, raio de 12 px, padding de 24 px.
    - O título do conteúdo (`h2`, Space Grotesk, 24 px, peso 700). Sem título, usa `FORMAT_LABELS[format]`.
    - Uma `dl` com os rótulos e valores no estilo do "Resumo do curso", em três colunas a partir de 640 px e em uma coluna abaixo disso:

    | Rótulo | Valor |
    | --- | --- |
    | TEMPO DE ESTUDO | "cerca de N min". Sem `estimated_minutes`, o item não aparece. |
    | CONCEITOS-CHAVE | Um `Badge` (`variant="outline"`) por conceito. Com a lista vazia ou nula, o item não aparece. |
    | PRÉ-REQUISITOS | Uma lista com marcadores. Com a lista vazia ou nula, o texto "Nenhum". |

- `ContentReader`, com o formato e o conteúdo.

T38 acrescenta a avaliação no fim de `ContentView`, depois do leitor, em outro `Card` no mesmo estilo.

### Documento que falhou

O alerta segue o padrão de erro de `DocumentsStep`, de T07: um `Alert` com borda de 1,5 px `border-destructive`, fundo `bg-destructive-background/30` e texto `text-destructive-foreground`, com o ícone `CircleAlert`.

- O título "Um documento falhou".
- Uma linha por documento que falhou: o `original_filename` em `font-mono` e, se existe, ": " seguido do `error_message`.

### Estados das telas

`CourseFallback` cobre as duas telas:

| Estado | O que a tela mostra |
| --- | --- |
| Carregando | Um `Skeleton` de 128 px de altura no lugar do cabeçalho e três `Skeleton` de 160 px na grade de `/courses`. |
| HTTP 404 | "Curso não encontrado." e um link "Voltar para os cursos", para `/courses`. |
| Outro erro | Um `Alert` de erro com o título "Não foi possível carregar o curso." e o botão "Tentar novamente", que refaz a consulta. É o mesmo padrão de `/courses`. |

Na rota do conteúdo, se o curso existe mas nenhum conteúdo tem o `id` da URL, a tela mostra "Conteúdo não encontrado." e um link "Voltar ao curso", para `/courses/$courseId`.

### Atualização automática

A consulta se repete a cada `POLL_INTERVAL_MS` enquanto `hasActiveContent(course.contents)` é verdadeiro. Depois disso, ela para de se repetir. A regra vale para as duas telas.

## Onde o design e a especificação divergem

As linhas marcadas como "Proposta" não têm desenho nas Telas finais. Quem cuida do design (Karina) confere na revisão.

| Elemento | Telas finais | Este ticket | Motivo |
| --- | --- | --- | --- |
| Linha numerada entre os cartões e texto "Cada um libera o próximo" | Tela 5 | Sai | Progresso fica fora do MVP (`telas.md`). |
| Selos "Concluído", "Em andamento" e "Não iniciado" | Tela 5 | Selo de estado da geração | `criar-curso.md`: cada conteúdo mostra na fila, gerando, pronto ou falhou. |
| Destaque azul do cartão atual | Tela 5 | Sai | Marca o conteúdo em andamento, que é progresso. |
| Botões "Revisar", "Continuar" e "Começar" | Tela 5 | "Abrir", em todos os cartões. Proposta. | Os três textos dependem do progresso. |
| Descrição do cartão e contagem ("5 etapas") | Tela 5 | Sai. No lugar, o texto de estado. | O esquema não guarda descrição. A contagem dependeria da forma de cada formato, que é dos leitores. |
| Rótulo "ROADMAP DO CURSO" | Tela 5 | "CURSO" | `conteudos-e-formatos.md`: o produto não propõe uma trilha. |
| Link "Meus cursos" na tela 5 | Tela 5 | "Todos os cursos", para `/courses` | O mesmo texto da tela 6. O `master` chama a lista de "Cursos". |
| Progresso, TEMA e "Continuar curso" no "Resumo do curso" | Tela 5 | Saem. Entram FORMATOS e MATERIAIS. | Progresso fica fora do MVP. O esquema não tem tema. |
| "Materiais usados" | Não aparece | Item MATERIAIS do "Resumo do curso" | Mantém a informação que a versão anterior deste ticket pedia, no bloco que o design já tem. |
| Faixa escura de borda a borda e fundo azul claro | Tela 6 | Faixa com raio de 12 px na largura da coluna. O fundo da página não muda. Proposta. | O layout de `_layout.tsx` limita a largura e dá o padding. T07 e T17 seguem esse layout. |
| Título no cabeçalho escuro | Título do curso | Título do curso | Igual ao design. O título do conteúdo fica em "Sobre este conteúdo". |
| Link "Todos os cursos" na tela 6 | Leva à lista | "Voltar ao curso", para `/courses/$courseId` | A pessoa abriu o conteúdo a partir do curso. Com um só conteúdo, o link continua "Todos os cursos". |
| Selo "Tutorial · Nível básico" | Formato e nível | Formato, nível e setor | `telas.md`: a tela de um conteúdo mostra o nível e o setor. |
| Texto "Quiz comentado" | Telas 5, Q1 a Q3 | "Quiz", de `FORMAT_LABELS` | `@/lib/courses` já está no `master` e é dividido com T17. |
| Ícones do quiz e dos flashcards | `CircleQuestionMark` e `Layers` nas telas 2 e 5. `ListChecks` e `Copy` nas telas Q1 e F1 | Os das telas 2 e 5, em todo lugar | O mesmo formato usa um só ícone. |
| Tempo, conceitos-chave e pré-requisitos | Não aparecem | Card "Sobre este conteúdo". Proposta. | O briefing e `conteudos-e-formatos.md` exigem os três. |
| Botão "Finalizar" | Tela 6 | Sai | Tela de finalização fica fora do MVP (`telas.md`). |
| Estados na fila, gerando e falhou | Não aparecem | Selo e texto no cartão, aviso na tela do conteúdo. Proposta. | `criar-curso.md`. |
| Alerta "Um documento falhou", carregamento, 404 e erro | Não aparecem | Padrões de T07 e T17. Proposta. | `telas.md`: uma mensagem de erro diz o que aconteceu e o que a pessoa pode fazer. |

Decisão: `telas.md` diz que a tela de um conteúdo que falhou mostra o botão "Tentar novamente". Este ticket mostra só o motivo. O botão entra em T32, junto com a rota de nova tentativa.

## O que o PR #24 aproveita e o que muda

O PR #24 seguiu um design anterior às Telas finais. Faça `rebase` no `master` depois que a revisão deste ticket entrar.

Fica como está:

- A consulta, com `courseQueryKey`, `retry: false` e `refetchInterval` em forma de função. Mova para `useCourse.ts`.
- Os estados de carregamento, de HTTP 404 e de erro. Mude só o que "Estados das telas" pede: o link do 404 vai para `/courses` e o erro ganha `AlertTitle`.
- Os textos dos avisos de `ContentView` e o `whitespace-pre-wrap` do erro.
- `ContentReader`, `readers/types.ts` e os três leitores, sem nenhuma mudança.
- A rota `$courseId/index.tsx`.
- Os testes de atualização automática, de login e de curso de outra pessoa.

Muda:

- As abas (`Tabs`) saem. Entram a grade de `ContentCard` e a rota do conteúdo.
- Com um só conteúdo, a tela mostra o cabeçalho escuro, não o cabeçalho claro.
- Os três `Badge` do cabeçalho saem. O nível e o setor vão para o "Resumo do curso" e para o selo do cabeçalho escuro. O estado do curso não aparece nesta tela: os selos dos conteúdos já mostram o estado de cada um.
- "N min de estudo" vira "cerca de N min".
- Os metadados vão para o card "Sobre este conteúdo".
- O bloco "MATERIAIS USADOS" vira o item MATERIAIS do "Resumo do curso".
- O alerta de documento que falhou ganha o estilo de T07.

## Detalhes técnicos

- Use componentes shadcn em toda a interface, sem HTML cru para elementos que têm componente: `Badge`, `Alert`, `Skeleton`, `Button` e `Card` já existem em `frontend/src/components/ui/`. Este ticket não acrescenta dependência: `frontend/package.json` e `bun.lock` não mudam.
- O botão "Abrir" habilitado é `<Button asChild variant="outline"><Link to="/courses/$courseId/contents/$contentId" params={...}>`. O desabilitado é `<Button variant="outline" disabled>`.
- `frontend/src/routeTree.gen.ts` é gerado. Em um conflito, faça `rebase` no `master` e rode `cd frontend && bun run build`. Nunca junte as duas versões à mão.
- Não edite `frontend/src/components/Common/TopNav.tsx`, `frontend/src/routes/_layout.tsx`, `frontend/src/routes/_layout/courses/$courseId/route.tsx`, `frontend/src/lib/courses.ts`, `frontend/tests/utils/` nem `frontend/src/components/Courses/`.
- Nos testes, crie um usuário próprio com `createUser` e os cursos com `createCourse`, que chama `POST /api/v1/private/courses/`. Entre com `logInUser` e abra a URL direto com `page.goto`. O seed não tem campo para `error_message` de documento: confira só o nome do arquivo no alerta.

## Critérios de aceite

- [ ] Com mais de um conteúdo, `/courses/$courseId` mostra o cabeçalho, um cartão por conteúdo, em ordem, com o selo de estado, e o "Resumo do curso".
- [ ] Um curso com um só conteúdo mostra a tela do conteúdo direto, com o link "Todos os cursos".
- [ ] "Abrir" leva a `/courses/$courseId/contents/$contentId` e fica desabilitado enquanto o conteúdo não tem resultado publicado.
- [ ] A tela do conteúdo mostra o cabeçalho escuro, o selo "Formato · Nível · Setor" e o link "Voltar ao curso".
- [ ] Um conteúdo que falhou mostra o motivo no cartão e na tela do conteúdo. Um conteúdo na fila ou em geração não aparece como pronto.
- [ ] Um conteúdo publicado mostra tempo, conceitos-chave e pré-requisitos.
- [ ] MATERIAIS lista os documentos que não falharam, e só eles.
- [ ] Nenhuma tela mostra progresso, "Concluído", "Em andamento", "Não iniciado" ou "Finalizar".
- [ ] A tela se atualiza a cada 3 segundos só enquanto há conteúdo na fila ou em geração.
- [ ] Um curso inexistente ou de outra pessoa mostra "Curso não encontrado." Um conteúdo que não é do curso mostra "Conteúdo não encontrado."
- [ ] Os três leitores, `ContentReader`, `ContentView` e `CoursePage` cumprem o contrato.
- [ ] Nenhum componente tem valor hexadecimal.
- [ ] Os testes Playwright que já existem passam.
- [ ] `bun run lint` e `bun run build` passam.

## Cenários de teste

Em `frontend/tests/course.spec.ts`, com um usuário novo por teste:

1. Curso `ready` com um tutorial `succeeded`, com título "Introdução", 12 minutos, dois conceitos e um pré-requisito, e os documentos `guia.md` e `notas.md`, os dois `indexed`. A tela mostra o `h1` com o título do curso, o link "Todos os cursos" para `/courses`, o selo "Tutorial · Técnico básico · Geral", o `h2` "Introdução", "cerca de 12 min", os dois conceitos, o pré-requisito e "O leitor deste formato ainda não está disponível." Não há botão "Abrir".
2. O mesmo curso mostra o "Resumo do curso" com "Geral", "Técnico básico", "Tutorial" e os itens `guia.md` e `notas.md`, nessa ordem.
3. Um tutorial `succeeded` sem pré-requisitos mostra "Nenhum".
4. Curso com três conteúdos, nesta ordem: tutorial `succeeded` com `content`, flashcards `pending` e quiz `failed` com `error_message` de duas linhas. Os rótulos aparecem na ordem "CONTEÚDO 1 · TUTORIAL", "CONTEÚDO 2 · FLASHCARDS" e "CONTEÚDO 3 · QUIZ". Os selos são "Pronto", "Na fila" e "Falhou". O cartão dos flashcards mostra "Este conteúdo espera a vez de ser gerado." O cartão do quiz mostra as duas linhas: confira o `innerText` e o `white-space`. Só o botão do tutorial está habilitado. FORMATOS mostra "Tutorial, flashcards e quiz". A tela não mostra "Concluído", "Em andamento", "Não iniciado" nem "Finalizar".
5. No mesmo curso, o clique em "Abrir" do tutorial leva a `/courses/{id}/contents/{contentId}`. A tela mostra o link "Voltar ao curso", e o clique nele volta a `/courses/{id}`.
6. A URL de um conteúdo `failed` com `content` e `error_message` mostra "A geração falhou", a mensagem e o resultado publicado. A URL de um conteúdo `running` mostra "Gerando. A tela se atualiza sozinha."
7. Curso `initializing` com um tutorial `pending`: a tela faz pelo menos 2 pedidos a `/api/v1/courses/{id}` em 8 segundos. Conte os pedidos com `page.on("request")`.
8. Curso com todos os conteúdos `succeeded`: a tela não faz nenhum pedido a `/api/v1/courses/{id}` nos 5 segundos seguintes ao primeiro.
9. Curso `failed` com um documento `failed` chamado `guia.md`: o alerta "Um documento falhou" mostra `guia.md`. O "Resumo do curso" não mostra MATERIAIS.
10. Um `id` de curso que não existe mostra "Curso não encontrado." O curso de outro usuário mostra o mesmo texto. Um `id` de conteúdo que não é do curso mostra "Conteúdo não encontrado."
11. Sem login, `/courses/{id}` redireciona para `/login`.
