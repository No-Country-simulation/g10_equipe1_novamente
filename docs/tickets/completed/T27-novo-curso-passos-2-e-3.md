---
id: T27
title: Monte os passos 2 e 3 de "Novo curso" e envie o curso à API
blocked_by: [T07, T18, T23, T37]
touches:
  - docs/product-specs/criar-curso.md
  - frontend/src/routes/_layout/courses/new.tsx
  - frontend/src/components/NewCourse/ProfileStep.tsx
  - frontend/src/components/NewCourse/FormatsStep.tsx
  - frontend/src/components/ui/radio-group.tsx
  - frontend/tests/new-course.spec.ts
executor: agente
size: 4
---

# T27 - Monte os passos 2 e 3 de "Novo curso" e envie o curso à API

## Contexto

T07 entregou o passo 1 de `/courses/new`: a pessoa anexa até 3 documentos e passa ao passo 2, que hoje mostra só o título "Perfil" e o botão "Voltar". T23 entregou `POST /api/v1/courses/`, que recebe o formulário, valida, grava os arquivos na OCI e cria o curso. `docs/product-specs/telas.md` define os dois passos que faltam:

| Passo | O que a pessoa faz |
| --- | --- |
| 2. Perfil | Escolhe título, setor e nível de público |
| 3. Formatos | Escolhe de 1 a 3 saídas: tutorial, flashcards ou quiz, e cria o curso |

O envio ao servidor acontece uma vez, no fim do passo 3.

Até T28, o curso criado fica em `initializing` ("Gerando" na lista de cursos) e seus conteúdos ficam em `pending` ("Na fila").

Os passos 2 e 3 seguem a moldura do passo 1, entregue em T07. Após o envio com sucesso, a tela abre o curso criado.

Leia `docs/product-specs/telas.md`, `docs/product-specs/criar-curso.md`, os tickets T07, T18, T23 e T37 em `docs/tickets/completed/` e `frontend/src/routes/_layout/courses/new.tsx`.

## Escopo

- Passo 2: título, setor e nível de público, com a conferência do título.
- Passo 3: escolha de 1 a 3 formatos, na ordem da escolha.
- Envio do formulário a `POST /api/v1/courses/` e ida à tela do curso criado.
- Atualização do caminho após o envio na seção "O que a pessoa vê" de `docs/product-specs/criar-curso.md`.
- Mensagem de erro da API no passo 3, sem perder o que a pessoa preencheu.
- A coluna de etapas com os passos 2 e 3.

## Fora do escopo

- O passo 1 (T07, pronto), exceto o que "Troca de passo" pede em `new.tsx`.
- A tarefa de fundo que gera os conteúdos (T28).
- Guardar o formulário entre recargas da página. Um `File` não sobrevive a uma recarga.
- Mudar a rota da API ou o cliente gerado.

## Contrato

### Módulos que este ticket usa

Do `master`. Não edite esses arquivos.

```ts
// @/client (tipos simplificados para as chamadas deste ticket)
NichesService.readNiches(): Promise<{ data: Array<NichePublic> }> // { id, slug, name, description }
CoursesService.createCourse({ body: Body_courses_create_course }): Promise<{ data: CourseDetail }>

type Body_courses_create_course = {
  niche_id: number
  audience_level: AudienceLevel // "non_technical" | "technical_basic" | "technical_advanced"
  title?: string
  formats?: Array<ContentFormat> | null // a ordem é a ordem das saídas
  files?: Array<Blob | File> | null
}

// @/components/NewCourse/documents (T07)
export interface DraftDocument { id: string; file: File; source: "upload" | "typed" }

// @/components/NewCourse/StepList (T07)
export const STEPS = ["Documentos", "Perfil", "Formatos"] as const
// StepList({ current, completed, onSelect })

// @/lib/courses (T17): AUDIENCE_LABELS, FORMAT_LABELS, coursesQueryKey
// @/components/Course/formatIcons (T18): formatIcons
```

Erros de validação do curso trazem HTTP 422 ou 404 e `detail` em português. O FastAPI usa HTTP 422 com `detail` em lista para erros de tipo. Falhas de armazenamento trazem HTTP 503 com `detail` igual a "O armazenamento de arquivos não está disponível. Tente novamente mais tarde." O cliente lança um `AxiosError`. O tratamento global de HTTP 401 e 403 em `frontend/src/main.tsx` continua valendo.

### Componentes que este ticket cria

`frontend/src/components/NewCourse/ProfileStep.tsx`:

```ts
export interface ProfileDraft {
  title: string
  nicheId: number | null
  audienceLevel: AudienceLevel | null
}

interface ProfileStepProps {
  profile: ProfileDraft
  onChange: (profile: ProfileDraft) => void
  onBack: () => void
  onContinue: () => void
}

export function ProfileStep(props: ProfileStepProps): React.JSX.Element
```

`frontend/src/components/NewCourse/FormatsStep.tsx`:

```ts
interface FormatsStepProps {
  /** Os formatos escolhidos, na ordem da escolha. */
  formats: ContentFormat[]
  onChange: (formats: ContentFormat[]) => void
  onBack: () => void
  onSubmit: () => void
  /** Verdadeiro enquanto o pedido à API não termina. */
  submitting: boolean
  /** Mensagem do último erro de envio, ou `null`. */
  error: string | null
}

export function FormatsStep(props: FormatsStepProps): React.JSX.Element
```

`NewCourse`, em `new.tsx`, guarda os estados `step`, `documents`, `profile` e `formats` com `useState`, e faz o envio com `useMutation`.

## Comportamento esperado

### Moldura

Reutilize o `Card` e o `CardHeader` de `new.tsx` para os três passos. Mantenha a altura mínima de 560 px, o raio de 12 px e o cabeçalho com "ETAPA N DE 3", título e descrição. Use espaços de 24 px entre os blocos e nas laterais do conteúdo.

Siga o rodapé de `DocumentsStep.tsx`, com borda superior, fundo `bg-muted/30`, padding de 24 px e posição no fundo do cartão. À esquerda, mostre "Voltar" como `Button` com `variant="outline"`, altura mínima de 48 px e padding lateral de 22 px. À direita, mostre a ação do passo no estilo do botão escuro de T07, com altura mínima de 48 px, padding lateral de 28 px e raio de 6 px. Use `bg-foreground` e `text-background` no botão ativo, e `bg-muted` e `text-foreground-tertiary` no desabilitado.

| Passo | Título | Frase do cabeçalho | Botão da direita |
| --- | --- | --- | --- |
| 2 | Perfil | "Diga para quem é o curso." | "Continuar" |
| 3 | Formatos | "Escolha o que o curso vai gerar." | "Criar curso" |

### Passo 2: Perfil

Três campos, de cima para baixo, cada um com um `Label`:

1. **Título do curso.** Um `Input` com o rótulo "Título do curso". A conferência roda quando o campo perde o foco e no clique em "Continuar":

    | Condição | Mensagem abaixo do campo |
    | --- | --- |
    | Vazio ou só com espaços | Informe um título. |
    | Mais de 255 caracteres depois de tirar os espaços das pontas | O título passa de 255 caracteres. |

    Use as mensagens de `criar-curso.md`. Conte caracteres Unicode, como o Python, e envie o título sem os espaços das pontas. Depois da primeira conferência, atualize a mensagem conforme a pessoa corrige o título. Associe a mensagem ao campo com `aria-describedby` e marque o campo inválido com `aria-invalid`.

2. **Setor.** Um `Select` com o rótulo "Setor" e uma opção por setor de `NichesService.readNiches`, na ordem da API, com o `name`. Use `useQuery` com a chave `["niches"]` e `retry: false`. Enquanto a lista carrega, o `Select` fica desabilitado. Se a consulta falha, o campo mostra "Não foi possível carregar os setores." e o botão "Tentar novamente", que refaz a consulta.

3. **Nível de público.** Um `RadioGroup` com o rótulo "Nível de público" e três opções, em cartões de borda de 1 px e raio 8, com padding de 16:

    | Valor | Texto | Descrição, 14 px, `text-muted-foreground` |
    | --- | --- | --- |
    | `non_technical` | `AUDIENCE_LABELS.non_technical` | Iniciante ou gestor. Sem jargão, com analogias do dia a dia. |
    | `technical_basic` | `AUDIENCE_LABELS.technical_basic` | Dev júnior ou pleno. Termos explicados e passos práticos. |
    | `technical_advanced` | `AUDIENCE_LABELS.technical_advanced` | Líder técnico ou arquiteto. Direto ao ponto, com limites e custos. |

    As descrições vêm da tabela "O nível de público muda a linguagem e a profundidade", de `conteudos-e-formatos.md`. A opção escolhida usa a borda `border-info`.

"Continuar" fica desabilitado enquanto falta um setor da lista carregada ou o nível. Com os dois presentes e o título inválido, o clique mostra a mensagem do título e fica no passo 2. Com tudo válido, o clique leva ao passo 3. Os campos começam vazios.

### Passo 3: Formatos

Um cartão por formato, na ordem tutorial, flashcards e quiz. Cada cartão tem um `Checkbox` com o rótulo do formato (`FORMAT_LABELS`), o ícone de `formatIcons` (de T18, em `@/components/Course/formatIcons`) e uma descrição de 14 px, `text-muted-foreground`:

| Formato | Descrição |
| --- | --- |
| `tutorial` | Um guia passo a passo, com resumo e seções. |
| `flashcards` | De 8 a 12 cartões para memorizar, com frente e verso. |
| `quiz` | 5 perguntas de múltipla escolha, com justificativa. |

- Marcar um formato o põe no fim de `formats`. Desmarcar o tira da lista.
- Cada cartão marcado mostra, à direita, a posição na ordem de geração: "1º", "2º" ou "3º". Acima dos cartões, o texto "O curso gera os formatos na ordem em que você marca." (14 px, `text-muted-foreground`).
- "Criar curso" fica desabilitado sem nenhum formato ou com `submitting` verdadeiro.

### Envio

O clique em "Criar curso" chama `CoursesService.createCourse` com:

| Campo | Valor |
| --- | --- |
| `title` | `profile.title` sem os espaços das pontas |
| `niche_id` | `profile.nicheId` |
| `audience_level` | `profile.audienceLevel` |
| `formats` | `formats`, na ordem da escolha |
| `files` | `documents.map((document) => document.file)`, na ordem do passo 1 |

Durante o pedido, "Criar curso" mostra o ícone `Loader2` girando e o texto "Criando curso". Bloqueie um novo envio, a mudança de formatos e o retorno aos passos anteriores até o pedido terminar.

Com HTTP 201, o frontend invalida a consulta `coursesQueryKey` e navega para `/courses/$courseId`, com o `id` da resposta. Na tela do curso (T18), os conteúdos começam em "Na fila".

Em "O que a pessoa vê", de `docs/product-specs/criar-curso.md`, registre que o envio bem-sucedido abre o curso criado. Mantenha o estado inicial "Gerando" na lista, a atualização automática a cada 3 segundos durante a geração e o estado de cada conteúdo na tela do curso. T40 edita a seção de erros do mesmo documento.

Com erro, a tela fica no passo 3, com tudo o que a pessoa preencheu, e mostra acima do rodapé um `Alert` de erro com o título "Não foi possível criar o curso" e esta descrição:

| Erro | Descrição |
| --- | --- |
| `detail` é um texto (HTTP 422, 404 ou 503) | O `detail`, como a API devolveu. As mensagens da API já estão em português e dizem o que fazer (`criar-curso.md`). |
| `detail` é uma lista (HTTP 422 do FastAPI) | "Verifique os dados informados e tente novamente." |
| Sem resposta ou outro erro | "Não foi possível falar com o servidor. Tente novamente." |

Não use `handleError` de `frontend/src/utils.ts`: ele troca os textos que não conhece por uma frase genérica. Leia o `detail` de um `AxiosError` direto, em uma função dentro de `new.tsx`.

A mensagem some quando a pessoa clica de novo em "Criar curso" ou volta a um passo anterior. Um erro de documento, como "guia.pdf: Não foi possível abrir o PDF. Envie um PDF sem senha.", traz o nome do arquivo: a pessoa volta ao passo 1 e troca o arquivo.

### Troca de passo e coluna de etapas

- `StepList` recebe `completed` com todos os passos antes do atual: `[]` no passo 1, `[1]` no passo 2 e `[1, 2]` no passo 3.
- O clique em uma etapa concluída leva a essa etapa e mantém todos os dados. Isso já funciona por `onSelect`, de T07.
- "Voltar" no passo 3 leva ao passo 2 e mantém os formatos. "Voltar" no passo 2 leva ao passo 1 e mantém o perfil.
- Durante o envio, `NewCourse` não passa `onSelect` a `StepList`, para a coluna não responder ao clique.

## Detalhes técnicos

- Crie o `RadioGroup` em `frontend/src/components/ui/radio-group.tsx` com `@radix-ui/react-radio-group`, de `frontend/package.json`. Siga o padrão dos componentes shadcn em `frontend/src/components/ui/`.
- Reuse `Input`, `Label`, `Select`, `Checkbox`, `Button`, `Alert` e `Card` de `frontend/src/components/ui/`. Associe os rótulos aos controles, inclusive ao gatilho do `Select` e ao grupo de opções de nível.
- Use só as variáveis de cor de `frontend/src/index.css`. Não escreva valor hexadecimal.
- O `formDataBodySerializer` de `frontend/src/client/core/bodySerializer.gen.ts` repete o nome do campo para cada item do array. Confira o multipart que o navegador envia, com a ordem e os nomes dos arquivos preservados.
- Não edite `StepList.tsx`, `DocumentsStep.tsx`, `documents.ts`, `frontend/src/lib/courses.ts`, `frontend/src/utils.ts`, `frontend/src/components/Course/` nem `frontend/tests/utils/`. Nenhum outro ticket da onda edita `new.tsx` nem `new-course.spec.ts`.
- Este ticket não cria rota. `frontend/src/routeTree.gen.ts` não pode aparecer no diff.
- Os testes de T07 em `new-course.spec.ts` continuam passando. O teste 11 confere o título "Perfil", a etapa ativa e o botão "Voltar". O teste 12 volta ao passo 1 pela coluna de etapas.
- No CI, o backend roda sem as variáveis `OCI_*` e responde HTTP 503 a um curso válido. A máquina de quem executa o ticket pode ter essas variáveis. Por isso, os testes do sucesso e do HTTP 503 trocam a resposta de `POST /api/v1/courses/` com `page.route`. O teste do HTTP 422 usa o backend real: a API recusa o PDF antes de usar o armazenamento.
- Para o teste de sucesso, crie um usuário com `createUser` e um curso dele com `createCourse`, de `frontend/tests/utils/`. Use o estado inicial `initializing`, documentos `uploaded` e conteúdos `pending`. Entre com `logInUser` em um contexto sem sessão e abra `/courses/new`. Intercepte só o POST de criação. Responda HTTP 201 com o `CourseDetail` do seed e deixe a tela de destino consultar o curso pela API real.

## Critérios de aceite

- [x] Os passos 2 e 3 usam o cartão, o cabeçalho e o estilo do rodapé do passo 1.
- [x] O passo 2 pede título, setor e nível, confere o título com as mensagens de `criar-curso.md` e só avança com os três válidos.
- [x] O passo 3 aceita de 1 a 3 formatos e mostra a ordem da escolha.
- [x] "Criar curso" envia um só pedido por tentativa, com título, setor, nível, formatos na ordem escolhida e os arquivos do passo 1.
- [x] Com sucesso, a tela vai para `/courses/{id}` do curso criado.
- [x] A seção "O que a pessoa vê" em `criar-curso.md` descreve a ida direta ao curso, os estados e a atualização automática.
- [x] Com erro, a tela fica no passo 3, mostra a mensagem da API e mantém os dados.
- [x] "Voltar" e a coluna de etapas levam aos passos anteriores sem perder dados.
- [x] Nenhum componente tem valor hexadecimal.
- [x] Os testes Playwright que já existem passam.
- [x] `bun run lint` e `bun run build` passam.

## Cenários de teste

Acrescente os cenários a `frontend/tests/new-course.spec.ts`, depois dos testes de T07. Comece com uma sessão autenticada. Anexe `guia.md` e avance ao passo 2, salvo no teste do PDF inválido.

1. O passo 2 mostra "ETAPA 2 DE 3", os campos "Título do curso", "Setor" e "Nível de público", e "Continuar" desabilitado. O `Select` lista "Fintech", "Saúde", "E-commerce" e "Geral".
2. Saia do campo de título vazio. A tela mostra "Informe um título." Com setor e nível selecionados, clique em "Continuar" e verifique que a tela fica no passo 2. Um título com 256 caracteres mostra "O título passa de 255 caracteres." Com 255 caracteres, a mensagem some.
3. Com título, setor e nível, "Continuar" leva ao passo 3. A etapa 3 tem `aria-current="step"` e as etapas 1 e 2 aparecem como concluídas.
4. No passo 3, "Criar curso" está desabilitado. Marcar "Quiz" e depois "Tutorial" mostra "1º" no quiz e "2º" no tutorial. Desmarcar "Quiz" deixa o tutorial com "1º".
5. Marque um formato. Use "Voltar" para conferir o título, o setor e o nível. Avance e confira que o formato continua marcado. Clique em "Documentos" na coluna e confira que `guia.md` continua na lista.
6. Sucesso, com `page.route`: no passo 1, adicione também um texto digitado. Marque "Quiz" e depois "Tutorial" e clique em "Criar curso". Leia o corpo multipart do único POST com o cabeçalho `Content-Type` da solicitação. Confira `title` sem espaços nas pontas, o `niche_id` e o `audience_level` escolhidos, dois campos `formats` na ordem `quiz` e `tutorial` e dois campos `files` na ordem `guia.md` e `texto-digitado.md`. A tela vai para `/courses/{id}` da resposta e mostra o título do curso.
7. HTTP 503, com `page.route`: a tela fica no passo 3 e mostra "Não foi possível criar o curso" e "O armazenamento de arquivos não está disponível. Tente novamente mais tarde." O formato marcado continua marcado.
8. Com o POST retido em `page.route`, confira que "Criando curso", "Voltar" e os formatos estão desabilitados e que as etapas concluídas não são botões. Libere a resposta e confira que houve um único POST.
9. HTTP 422 do backend real: anexar `guia.pdf` com alguns bytes que não formam um PDF, preencher os passos 2 e 3 e clicar em "Criar curso". A tela mostra "guia.pdf: Não foi possível abrir o PDF. Envie um PDF sem senha." e continua no passo 3.
10. Faça a consulta de setores falhar com `page.route`. O passo 2 mostra a mensagem, desabilita o `Select` e bloqueia "Continuar". Faça a resposta seguinte passar e clique em "Tentar novamente". A lista volta a funcionar.
11. Com `page.route`, teste HTTP 422 com `detail` em lista e falha sem resposta. Confira as mensagens do quadro "Envio". Em cada caso, volte ao passo 2, avance e confira que os dados continuam preenchidos e a mensagem saiu.

## Verificação do aceite

- PR revisado: [#37](https://github.com/No-Country-simulation/g10_equipe1_novamente/pull/37), integrado no commit `ae97671`.
- CI do PR: todos os checks obrigatórios passaram, com escopo dentro de `touches`.
- Revisão automática: um achado, uma atualização em segundo plano dos setores bloqueava "Continuar" com a lista já carregada. O commit `8932e13` corrigiu e acrescentou o teste.
- Testes: 89 testes Playwright passaram com o backend local. `bun run lint`, `bun run build` e os hooks passaram.
