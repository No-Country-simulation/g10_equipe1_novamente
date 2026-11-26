import { expect, type Page, test } from "@playwright/test"
import type { CourseDetail, PrivateCourseCreate } from "../src/client"
import { createCourse } from "./utils/course"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test.use({ storageState: { cookies: [], origins: [] } })

const unknownId = "00000000-0000-0000-0000-000000000000"
const generationError = "linha um\nlinha dois"
const publishedTutorial = {
  format: "tutorial",
  status: "succeeded",
  title: "Introdução",
  content: {
    summary: "Aprenda os conceitos básicos do curso.",
    sections: [{ title: "Primeiros passos", body: "Comece pela base." }],
    takeaways: ["Pratique os conceitos do curso."],
  },
  estimated_minutes: 12,
  key_concepts: ["Conceito A", "Conceito B"],
  prerequisites: ["Base"],
} satisfies PrivateCourseCreate["contents"][number]
const mixedContents = [
  publishedTutorial,
  { format: "flashcards", status: "pending" },
  { format: "quiz", status: "failed", error_message: generationError },
] satisfies PrivateCourseCreate["contents"]

async function setup(page: Page, changes: Partial<PrivateCourseCreate> = {}) {
  const email = randomEmail()
  const password = randomPassword()
  await createUser({ email, password })
  const course = await createCourse({
    owner_email: email,
    title: "Curso de teste",
    audience_level: "technical_basic",
    status: "ready",
    documents: [
      { original_filename: "guia.md", status: "indexed" },
      { original_filename: "notas.md", status: "indexed" },
    ],
    contents: [publishedTutorial],
    ...changes,
  })
  await logInUser(page, email, password)
  return course
}

test("abre diretamente o único conteúdo com seus metadados", async ({
  page,
}) => {
  const course = await setup(page)
  await page.goto(`/courses/${course.id}`)

  await expect(
    page.getByRole("heading", { name: course.title, level: 1 }),
  ).toBeVisible()
  await expect(
    page.getByRole("link", { name: "Todos os cursos" }),
  ).toHaveAttribute("href", "/courses")
  await expect(
    page.getByText("Tutorial · Técnico básico · Geral"),
  ).toBeVisible()
  const metadata = page.getByRole("region", { name: "Sobre este conteúdo" })
  await expect(
    metadata.getByRole("heading", { name: "Introdução", level: 2 }),
  ).toBeVisible()
  for (const text of ["cerca de 12 min", "Conceito A", "Conceito B", "Base"]) {
    await expect(metadata.getByText(text, { exact: true })).toBeVisible()
  }
  await expect(page.getByText(publishedTutorial.content.summary)).toBeVisible()
  await expect(page.getByRole("button", { name: /^Abrir / })).toHaveCount(0)
  await expect(page.getByRole("link", { name: /^Abrir / })).toHaveCount(0)
})

test("mostra o resumo e preserva a ordem dos materiais da API", async ({
  page,
}) => {
  const course = await setup(page)
  let order = ["guia.md", "notas.md"]
  // A API não garante que os documentos saiam na ordem do seed.
  await page.route(`**/api/v1/courses/${course.id}`, async (route) => {
    const response = await route.fetch()
    const data: CourseDetail = await response.json()
    const documents = order.map((filename) =>
      data.documents.find(
        (document) => document.original_filename === filename,
      ),
    )
    expect(documents).not.toContain(undefined)
    await route.fulfill({ response, json: { ...data, documents } })
  })

  await page.goto(`/courses/${course.id}`)
  const summary = page.getByRole("region", { name: "Resumo do curso" })
  for (const text of ["Geral", "Técnico básico", "Tutorial"]) {
    await expect(summary.getByText(text, { exact: true })).toBeVisible()
  }
  const materials = summary
    .getByRole("list", { name: "Materiais" })
    .getByRole("listitem")
  await expect(materials).toHaveText(["guia.md", "notas.md"])

  order = ["notas.md", "guia.md"]
  await page.reload()
  await expect(materials).toHaveText(["notas.md", "guia.md"])
})

test("mostra Nenhum quando o tutorial não tem pré-requisitos", async ({
  page,
}) => {
  const course = await setup(page, {
    contents: [{ format: "tutorial", status: "succeeded", content: {} }],
  })
  await page.goto(`/courses/${course.id}`)
  const metadata = page.getByRole("region", { name: "Sobre este conteúdo" })
  await expect(
    metadata.getByText("PRÉ-REQUISITOS", { exact: true }),
  ).toBeVisible()
  await expect(metadata.getByText("Nenhum", { exact: true })).toBeVisible()
})

test("mostra cartões ordenados com estados e só libera conteúdo publicado", async ({
  page,
}) => {
  const course = await setup(page, { contents: mixedContents })
  await page.goto(`/courses/${course.id}`)
  await expect(page.getByText(/^CONTEÚDO \d+ ·/)).toHaveText([
    "CONTEÚDO 1 · TUTORIAL",
    "CONTEÚDO 2 · FLASHCARDS",
    "CONTEÚDO 3 · QUIZ",
  ])
  const card = (title: string) =>
    page.locator('[data-slot="card"]').filter({
      has: page.getByRole("heading", { name: title, level: 2, exact: true }),
    })
  const tutorial = card("Introdução")
  const flashcards = card("Flashcards")
  const quiz = card("Quiz")
  await expect(tutorial.getByText("Pronto", { exact: true })).toBeVisible()
  await expect(tutorial.getByText("cerca de 12 min")).toBeVisible()
  await expect(
    tutorial.getByRole("link", { name: "Abrir Introdução" }),
  ).toBeEnabled()
  await expect(flashcards.getByText("Na fila", { exact: true })).toBeVisible()
  await expect(
    flashcards.getByText("Este conteúdo espera a vez de ser gerado."),
  ).toBeVisible()
  await expect(
    flashcards.getByRole("button", { name: "Abrir Flashcards" }),
  ).toBeDisabled()
  await expect(quiz.getByText("Falhou", { exact: true })).toBeVisible()
  const error = quiz.getByText("linha um linha dois")
  await expect(error).toBeVisible()
  await expect(error).toHaveCSS("white-space", "pre-line")
  await expect(error).toHaveJSProperty("innerText", generationError)
  await expect(quiz.getByRole("button", { name: "Abrir Quiz" })).toBeDisabled()
  await expect(page.getByRole("link", { name: /^Abrir / })).toHaveCount(1)
  await expect(
    page
      .getByRole("region", { name: "Resumo do curso" })
      .getByText("Tutorial, flashcards e quiz"),
  ).toBeVisible()
  await expect(
    page.getByText(/^(Concluído|Em andamento|Não iniciado|Finalizar)$/),
  ).toHaveCount(0)
})

test("abre o tutorial pela grade e volta ao curso", async ({ page }) => {
  const course = await setup(page, { contents: mixedContents })
  const coursePath = `/courses/${course.id}`
  await page.goto(coursePath)
  await page.getByRole("link", { name: "Abrir Introdução" }).click()
  await expect(page).toHaveURL(
    `${coursePath}/contents/${course.contents[0].id}`,
  )
  const heading = page.getByRole("heading", { name: course.title, level: 1 })
  await expect(heading).toBeVisible()
  await expect(
    page.getByText("Tutorial · Técnico básico · Geral"),
  ).toBeVisible()
  const header = page.locator("header").filter({ has: heading })
  await expect(header).toHaveCSS("border-bottom-width", "0px")
  await expect(
    page.getByRole("heading", { name: "Introdução", level: 2 }),
  ).toBeVisible()
  const back = page.getByRole("link", { name: "Voltar ao curso" })
  await expect(back).toHaveAttribute("href", coursePath)
  await back.click()
  await expect(page).toHaveURL(coursePath)
  await expect(
    page.getByRole("link", { name: "Abrir Introdução" }),
  ).toBeVisible()
})

test("mantém o conteúdo publicado legível durante falha ou geração", async ({
  page,
}) => {
  const cards = Array.from({ length: 8 }, (_, index) => ({
    front: `Pergunta ${index + 1}`,
    back: `Resposta ${index + 1}`,
  }))
  const course = await setup(page, {
    contents: [
      {
        ...publishedTutorial,
        status: "failed",
        error_message: generationError,
      },
      {
        format: "flashcards",
        status: "running",
        content: { introduction: "Revise os conceitos do curso.", cards },
      },
    ],
  })
  const coursePath = `/courses/${course.id}`
  const [failed, running] = course.contents
  await page.goto(coursePath)
  await expect(
    page.getByRole("link", { name: "Abrir Introdução" }),
  ).toHaveAttribute("href", `${coursePath}/contents/${failed.id}`)
  await expect(
    page.getByRole("link", { name: "Abrir Flashcards" }),
  ).toHaveAttribute("href", `${coursePath}/contents/${running.id}`)
  await page.goto(`${coursePath}/contents/${failed.id}`)
  const alert = page.getByRole("alert").filter({ hasText: "A geração falhou" })
  await expect(alert).toBeVisible()
  const error = alert.locator('[data-slot="alert-description"]')
  await expect(error).toHaveCSS("white-space", "pre-wrap")
  await expect(error).toHaveJSProperty("innerText", generationError)
  await expect(
    page.getByRole("heading", { name: "Introdução", level: 2 }),
  ).toBeVisible()
  await expect(page.getByText(publishedTutorial.content.summary)).toBeVisible()

  await page.goto(`${coursePath}/contents/${running.id}`)
  await expect(
    page.getByRole("alert").getByText("Gerando. A tela se atualiza sozinha."),
  ).toBeVisible()
  await expect(page.getByText(cards[0].front, { exact: true })).toBeVisible()
})

for (const screen of ["curso", "conteúdo"] as const) {
  test(`atualiza enquanto há conteúdo ativo na tela de ${screen}`, async ({
    page,
  }) => {
    const course = await setup(page, {
      status: "initializing",
      contents: [{ format: "tutorial", status: "pending" }],
    })
    let requests = 0
    page.on("request", (request) => {
      if (request.url().endsWith(`/api/v1/courses/${course.id}`)) requests++
    })
    const coursePath = `/courses/${course.id}`
    await page.goto(
      screen === "curso"
        ? coursePath
        : `${coursePath}/contents/${course.contents[0].id}`,
    )
    await expect(
      page
        .getByRole("alert")
        .getByText("Na fila. Este conteúdo espera a vez de ser gerado."),
    ).toBeVisible()
    await expect
      .poll(() => requests, { timeout: 8000 })
      .toBeGreaterThanOrEqual(2)
  })

  test(`mantém os dados na tela de ${screen} após falha na atualização`, async ({
    page,
  }) => {
    const course = await setup(page, { contents: mixedContents })
    const coursePath = `/courses/${course.id}`
    await page.goto(
      screen === "curso"
        ? coursePath
        : `${coursePath}/contents/${course.contents[0].id}`,
    )
    const title = page.getByRole("heading", { name: "Introdução", level: 2 })
    await expect(title).toBeVisible()

    const endpoint = `/api/v1/courses/${course.id}`
    await page.route(`**${endpoint}`, (route) => route.fulfill({ status: 500 }))
    await page.waitForResponse(
      (response) =>
        response.url().endsWith(endpoint) && response.status() === 500,
    )
    // A próxima consulta só começa depois que o primeiro erro foi processado.
    await page.waitForRequest((request) => request.url().endsWith(endpoint))

    await expect(title).toBeVisible()
    await expect(
      page
        .getByRole("alert")
        .filter({ hasText: "Não foi possível carregar o curso." }),
    ).toHaveCount(0)
  })
}

test("não atualiza curso com todos os conteúdos prontos", async ({ page }) => {
  const course = await setup(page)
  let requests = 0
  page.on("request", (request) => {
    if (request.url().endsWith(`/api/v1/courses/${course.id}`)) requests++
  })
  await page.goto(`/courses/${course.id}`)
  await expect(
    page.getByRole("heading", { name: "Introdução", level: 2 }),
  ).toBeVisible()
  await page.waitForTimeout(5000)
  expect(requests).toBe(1)
})

test("mostra a falha do documento e omite materiais quando todos falharam", async ({
  page,
}) => {
  const course = await setup(page, {
    status: "failed",
    documents: [{ original_filename: "guia.md", status: "failed" }],
    contents: [{ format: "tutorial", status: "failed" }],
  })
  await page.goto(`/courses/${course.id}`)
  const alert = page
    .getByRole("alert")
    .filter({ hasText: "Um documento falhou" })
  await expect(alert.getByText("guia.md")).toBeVisible()
  const summary = page.getByRole("region", { name: "Resumo do curso" })
  await expect(summary).toBeVisible()
  await expect(summary.getByText("MATERIAIS", { exact: true })).toHaveCount(0)
})

test("mostra o retorno correto para curso ou conteúdo inexistente", async ({
  page,
}) => {
  const course = await setup(page)
  await page.goto(`/courses/${unknownId}`)
  await expect(page.getByText("Curso não encontrado.")).toBeVisible()
  await expect(
    page.getByRole("link", { name: "Voltar para os cursos" }),
  ).toHaveAttribute("href", "/courses")

  const coursePath = `/courses/${course.id}`
  await page.goto(`${coursePath}/contents/${unknownId}`)
  await expect(page.getByText("Conteúdo não encontrado.")).toBeVisible()
  await expect(
    page.getByRole("link", { name: "Voltar ao curso" }),
  ).toHaveAttribute("href", coursePath)
})

test("sem login redireciona", async ({ page }) => {
  await page.goto(`/courses/${unknownId}`)
  await page.waitForURL("/login")
})

test("curso de outra pessoa não aparece", async ({ page }) => {
  const otherEmail = randomEmail()
  await createUser({ email: otherEmail, password: randomPassword() })
  const otherCourse = await createCourse({
    owner_email: otherEmail,
    title: "Outro curso",
    audience_level: "non_technical",
    documents: [{ original_filename: "outro.md" }],
    contents: [{ format: "tutorial", status: "pending" }],
  })
  await setup(page)
  await page.goto(`/courses/${otherCourse.id}`)
  await expect(page.getByText("Curso não encontrado.")).toBeVisible()
})
