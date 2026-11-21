---
id: T38
title: Mostre na tela do conteúdo a fidelidade, a clareza, as observações e os trechos citados
blocked_by: [T18]
touches:
  - frontend/src/components/Course/ContentView.tsx
  - frontend/src/components/Course/ContentEvaluation.tsx
  - frontend/tests/content-evaluation.spec.ts
executor: agente
size: 2
---

# T38 - Mostre na tela do conteúdo a fidelidade, a clareza, as observações e os trechos citados

## Contexto

`docs/product-specs/telas.md` diz que a tela de um conteúdo mostra a fidelidade ao documento, a clareza, as observações da revisão e os trechos citados. T18 entregou a tela com o leitor no fim de `ContentView`. A avaliação entra logo depois do leitor. `GET /api/v1/courses/{course_id}` já devolve os quatro dados em cada `ContentPublic`, com texto e similaridade em cada citação, como descreve `docs/product-specs/pacote-json-e-armazenamento.md`.

T38 saiu de T18, que passava de 5 pontos.

T40 exige apoio para cada afirmação técnica revisada antes de publicar. As novas publicações por essa regra terão fidelidade de 100%. A tela mostra o valor da API, inclusive valores de publicações anteriores. O contrato da API permite entregar T38 antes de T40.

A demonstração mostra à banca a fidelidade ao documento e os trechos citados de um conteúdo (`docs/product-specs/demonstracao.md`, item 4).

Leia antes: `docs/product-specs/telas.md`, seção "O que a tela de um conteúdo mostra", `docs/product-specs/fidelidade-e-qualidade.md`, seção "O que a pessoa vê em um conteúdo publicado", e `docs/tickets/completed/T18-tela-curso.md`, seções "Contrato" e "`ContentView`".

## Escopo

- Um `Card` "Avaliação" no fim de `ContentView`, com a fidelidade, a clareza e as observações da revisão.
- A lista dos trechos citados, com o documento, a página e a similaridade de cada um.

## Fora do escopo

- Calcular a nota ou escolher as citações (T04, T22 e T40, no backend).
- Os leitores (T08, T09 e T10).
- Destacar no texto do conteúdo a frase que cada trecho sustenta. O esquema não liga uma afirmação a um trecho depois da publicação.
- A nota de uma tentativa reprovada. A tela continua mostrando a avaliação da versão publicada anteriormente, se houver.

## Contrato

### Módulos que este ticket usa

Do `master`. Não edite esses arquivos.

```ts
// @/client
type ContentPublic = {
  // ...campos de T18
  content: { [key: string]: unknown } | null
  grounding_score: number | null // de 0 a 1, com 2 casas
  clarity: ClarityLevel | null // "low" | "medium" | "high"
  review_notes: string | null
  citations: Array<CitationPublic> // similaridade decrescente, valores nulos no fim
}
type CitationPublic = {
  chunk_id: string
  document_id: string
  document_title: string
  text: string
  page_number: number | null
  similarity: number | null
}

// @/lib/courses (T17)
export const CLARITY_LABELS: Record<ClarityLevel, string> // Baixa, Média, Alta
```

### Componente que este ticket cria

`frontend/src/components/Course/ContentEvaluation.tsx`:

```ts
interface ContentEvaluationProps {
  content: ContentPublic
}

export function ContentEvaluation(props: ContentEvaluationProps): React.JSX.Element | null
```

### O que este ticket muda em `ContentView.tsx`

Importe `ContentEvaluation` de `./ContentEvaluation` e monte `<ContentEvaluation content={content} />` logo depois de `<ContentReader ... />`, no bloco que exige `content.content !== null`.

## Comportamento esperado

`ContentView` monta a avaliação quando `content.content` contém uma versão publicada. Isso vale durante uma nova geração (`running`) ou depois de uma tentativa que falhou (`failed`), enquanto a versão publicada continuar disponível.

O componente é um `Card` no estilo de "Sobre este conteúdo", de T18: borda de 1 px, raio de 12 px e padding de 24 px. Ele tem `role="region"` e o nome acessível "Avaliação". De cima para baixo:

1. O rótulo "Avaliação" e o título "Fidelidade e clareza" (`h2`, Space Grotesk, 24 px, peso 700), no mesmo arranjo do card de T18.
2. Uma `dl`, no estilo do card de T18, em três colunas a partir de 640 px e em uma coluna abaixo disso:

    | Rótulo | Valor | Quando aparece |
    | --- | --- | --- |
    | FIDELIDADE AO DOCUMENTO | `Math.round(grounding_score * 100)` seguido de "%", em Space Grotesk, 28 px, peso 700. Abaixo, em 14 px com `text-muted-foreground`, mostre "Afirmações técnicas do conteúdo de estudo com apoio nos trechos do documento." | `grounding_score` não é nulo |
    | CLAREZA | `CLARITY_LABELS[clarity]`. Abaixo, 14 px, `text-muted-foreground`: "Para o nível de público do curso." | `clarity` não é nulo |
    | OBSERVAÇÕES DA REVISÃO | `review_notes`, com as quebras de linha preservadas (`whitespace-pre-line`) | `review_notes` tem texto após retirar os espaços das pontas |

3. O título "Trechos citados" (`h3`, Space Grotesk, 18 px, peso 700), com 24 px acima.
4. Uma lista (`ul`) com o nome acessível "Trechos citados" e um item por citação, na ordem da API. Cada item tem borda esquerda de 3 px `border-info`, fundo `bg-muted/50`, raio de 8 px e padding de 16 px:
    - Na primeira linha, 13 px, `text-foreground-tertiary`: o `document_title` em `font-mono`, depois " · página N" quando `page_number` não é nulo, depois " · similaridade 0,91" quando `similarity` não é nulo. Formate a similaridade com 2 casas, em português do Brasil: `similarity.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })`.
    - Abaixo, o `text` do trecho, 15 px, altura de linha 1,5, `text-foreground`, com as quebras de linha preservadas.
    - Um trecho com mais de 600 caracteres mostra os 600 primeiros e "…", além de um `Button` com `variant="link"` e o texto "Mostrar trecho inteiro". O clique alterna entre o trecho inteiro e o encurtado. O botão usa `aria-expanded` e mostra "Mostrar menos" enquanto o trecho está inteiro.
5. Sem nenhuma citação, no lugar da lista: "Nenhum trecho citado." (15 px, `text-muted-foreground`).

Quando faltam os três valores da `dl`, omita a `dl`. Se também não houver citações, `ContentEvaluation` devolve `null`.

## Detalhes técnicos

- Use componentes shadcn onde houver: `Card` e `Button` já existem em `frontend/src/components/ui/`. Este ticket não acrescenta dependência: `frontend/package.json` e `bun.lock` não mudam.
- Use só as variáveis de cor de `frontend/src/index.css`. Não escreva valor hexadecimal.
- Não edite `ContentReader.tsx`, `ContentPage.tsx`, os leitores em `readers/`, `frontend/src/lib/courses.ts`, `frontend/tests/course.spec.ts` nem `frontend/tests/utils/`. T08, T09 e T10 editam os leitores na mesma onda. T08 e T09 também editam `course.spec.ts`.
- Este ticket usa as rotas de T18. O build preserva `frontend/src/routeTree.gen.ts`.
- Nos testes, crie o usuário com `createUser` e o curso com `createCourse`, de `frontend/tests/utils/`. O seed aceita `grounding_score`, `clarity`, `review_notes` e `cited_chunks` no conteúdo, e `chunks` em cada documento. `cited_chunks` traz a posição de cada chunk na lista de todos os chunks do curso, a partir de 0, na ordem dos documentos. Entre com `logInUser` e abra a URL com `page.goto`, como `course.spec.ts` faz.

## Critérios de aceite

- [x] Um conteúdo publicado mostra a fidelidade em porcentagem, a clareza, as observações e os trechos citados, na ordem da API.
- [x] Cada trecho mostra o documento e, quando a API devolve os valores, a página e a similaridade com 2 casas.
- [x] Um trecho com mais de 600 caracteres aparece encurtado e abre por inteiro com "Mostrar trecho inteiro".
- [x] Um conteúdo sem resultado publicado não mostra a avaliação.
- [x] `ContentView.tsx` importa e monta `ContentEvaluation` depois de `ContentReader`.
- [x] Nenhum componente tem valor hexadecimal.
- [x] Os testes Playwright que já existem passam.
- [x] `bun run lint` e `bun run build` passam.

## Cenários de teste

Crie os cenários em `frontend/tests/content-evaluation.spec.ts`, com um usuário novo por teste. Use um documento `guia.md` com três chunks de texto distinto. O curso tem um tutorial publicado com `content` e abre em `/courses/{id}`, salvo onde o cenário indica outra configuração.

1. Use `grounding_score` 1, `clarity` `high`, duas linhas em `review_notes` e `cited_chunks` [0, 2]. A região "Avaliação" mostra "100%", a frase que explica a porcentagem, "Alta" e as duas linhas da revisão. Confira que a lista contém o primeiro e o terceiro chunk, ambos de "guia.md".
2. O seed grava 0,9 de similaridade e deixa a página nula. Cada item mostra "similaridade 0,90" e omite "página". A API deixa a ordem entre citações empatadas em aberto.
3. `grounding_score` 0,87: a tela mostra "87%".
4. Um tutorial publicado sem `cited_chunks`: a tela mostra "Nenhum trecho citado."
5. Use um trecho citado com 700 caracteres. Confira que o item encurta o texto e mostra "Mostrar trecho inteiro". Abra o trecho, confira o fim do texto e use "Mostrar menos" para encurtar de novo.
6. Um curso com tutorial `pending`, sem `content`, abre em `/courses/{id}`: a tela não tem a região "Avaliação".
7. Um tutorial `failed` com `content`, `grounding_score` 1 e `error_message`: a tela mostra "A geração falhou" e a região "Avaliação" com "100%".
8. Use um tutorial publicado sem nota, clareza, observações ou citações. A região "Sobre este conteúdo" fica visível e a região "Avaliação" fica ausente.
9. Em um curso com vários conteúdos, abra o tutorial em `/courses/{id}/contents/{contentId}`. Use `page.route` para devolver três citações na ordem da API, com similaridades 0,91, 0,82 e nula, e `page_number` 3 na primeira. A lista preserva a ordem, mostra "página 3" na primeira e omite a similaridade na última.

## Verificação do aceite

- PR revisado: [#33](https://github.com/No-Country-simulation/g10_equipe1_novamente/pull/33), integrado no commit `a23e200`.
- CI do PR: todos os checks obrigatórios passaram, com escopo dentro de `touches`.
- Revisão automática: um achado, faltavam testes para as linhas que somem sem dados. O commit `dd79dea` acrescentou os casos de campos ausentes e de só trechos citados.
- Testes: `tests/content-evaluation.spec.ts` cobre publicações antigas, campos ausentes, a ordem da API e a expansão dos trechos.
