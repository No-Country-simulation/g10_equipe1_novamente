import { expect, type Page, test } from "@playwright/test"
import type { CourseDetail, PrivateCourseCreate } from "../src/client"
import { createCourse } from "./utils/course"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test.use({ storageState: { cookies: [], origins: [] } })

const chunks = [
  "O guia apresenta os conceitos.\nA introdução define os termos.",
  "A seção descreve um exemplo.",
  "O apêndice lista as referências.",
]
const publishedTutorial = {
  format: "tutorial",
  status: "succeeded",
  content: {},
} satisfies PrivateCourseCreate["contents"][number]

async function setup(page: Page, changes: Partial<PrivateCourseCreate> = {}) {
  const email = randomEmail()
  const password = randomPassword()
  await createUser({ email, password })
  const course = await createCourse({
    owner_email: email,
    title: "Curso com avaliação",
    audience_level: "technical_basic",
    documents: [{ original_filename: "guia.md", chunks }],
    contents: [publishedTutorial],
    ...changes,
  })
  await logInUser(page, email, password)
  return course
}

const evaluation = (page: Page) =>
  page.getByRole("region", { name: "Avaliação" })

const citationItems = (page: Page) =>
  evaluation(page)
    .getByRole("list", { name: "Trechos citados" })
    .getByRole("listitem")

test("mostra a avaliação e os trechos do documento", async ({ page }) => {
  const reviewNotes = "A linguagem serve ao público.\nOs exemplos são claros."
  const course = await setup(page, {
    contents: [
      {
        ...publishedTutorial,
        grounding_score: 1,
        clarity: "high",
        review_notes: reviewNotes,
        cited_chunks: [0, 2],
      },
    ],
  })
  await page.goto(`/courses/${course.id}`)

  const card = evaluation(page)
  await expect(
    card.getByRole("heading", { level: 2, name: "Fidelidade e clareza" }),
  ).toBeVisible()
  await expect(card.getByText("100%", { exact: true })).toBeVisible()
  await expect(
    card.getByText(
      "Afirmações técnicas do conteúdo de estudo com apoio nos trechos do documento.",
    ),
  ).toBeVisible()
  const clarity = card
    .getByRole("definition")
    .filter({ hasText: "Para o nível de público do curso." })
  await expect(clarity).toBeVisible()
  await expect(clarity).toHaveText(
    /^Alta\s*Para o nível de público do curso\.$/,
  )
  const notes = card.getByText(reviewNotes, { exact: true })
  await expect(notes).toBeVisible()
  await expect(notes).toHaveCSS("white-space", "pre-line")
  await expect(notes).toHaveJSProperty("innerText", reviewNotes)

  const items = citationItems(page)
  await expect(items).toHaveCount(2)
  for (const text of [chunks[0], chunks[2]]) {
    const item = items.filter({ hasText: text })
    const excerpt = item.getByText(text, { exact: true })
    await expect(excerpt).toBeVisible()
    await expect(excerpt).toHaveJSProperty("innerText", text)
    await expect(item.getByText("guia.md", { exact: true })).toBeVisible()
    await expect(item).toContainText("similaridade 0,90")
    await expect(item).not.toContainText("página")
  }
})

test("mostra a nota de uma publicação anterior e indica a falta de citações", async ({
  page,
}) => {
  const course = await setup(page, {
    contents: [{ ...publishedTutorial, grounding_score: 0.87 }],
  })
  await page.goto(`/courses/${course.id}`)

  const card = evaluation(page)
  await expect(card.getByText("87%", { exact: true })).toBeVisible()
  await expect(card.getByText("Nenhum trecho citado.")).toBeVisible()
  await expect(card.getByRole("list", { name: "Trechos citados" })).toHaveCount(
    0,
  )
})

test("expande e recolhe um trecho com 700 caracteres", async ({ page }) => {
  const start = "a".repeat(600)
  const end = "b".repeat(100)
  const course = await setup(page, {
    documents: [
      { original_filename: "guia.md", chunks: [...chunks, start + end] },
    ],
    contents: [{ ...publishedTutorial, cited_chunks: [3] }],
  })
  await page.goto(`/courses/${course.id}`)

  const item = citationItems(page)
  const shortened = item.getByText(`${start}…`, { exact: true })
  const full = item.getByText(start + end, { exact: true })
  const expand = item.getByRole("button", { name: "Mostrar trecho inteiro" })
  const collapse = item.getByRole("button", { name: "Mostrar menos" })
  await expect(shortened).toBeVisible()
  await expect(full).toHaveCount(0)
  await expect(expand).toHaveAttribute("aria-expanded", "false")
  await expand.click()
  await expect(full).toBeVisible()
  await expect(collapse).toHaveAttribute("aria-expanded", "true")
  await collapse.click()
  await expect(shortened).toBeVisible()
  await expect(full).toHaveCount(0)
})

test("omite a avaliação enquanto o tutorial está na fila sem publicação", async ({
  page,
}) => {
  const course = await setup(page, {
    contents: [{ format: "tutorial", status: "pending" }],
  })
  await page.goto(`/courses/${course.id}`)

  await expect(
    page.getByText("Na fila. Este conteúdo espera a vez de ser gerado."),
  ).toBeVisible()
  await expect(evaluation(page)).toHaveCount(0)
})

for (const { status, alert } of [
  { status: "running", alert: "Gerando. A tela se atualiza sozinha." },
  { status: "failed", alert: "A geração falhou" },
] as const) {
  test(`preserva a avaliação da publicação durante o estado ${status}`, async ({
    page,
  }) => {
    const course = await setup(page, {
      contents: [
        {
          ...publishedTutorial,
          status,
          grounding_score: 1,
          error_message: status === "failed" ? "Erro na nova tentativa." : null,
        },
      ],
    })
    await page.goto(`/courses/${course.id}`)

    await expect(page.getByText(alert, { exact: true })).toBeVisible()
    await expect(
      evaluation(page).getByText("100%", { exact: true }),
    ).toBeVisible()
  })
}

for (const { notes, label } of [
  { notes: null, label: "sem observações" },
  { notes: " \n ", label: "observações em branco" },
]) {
  test(`omite a avaliação sem dados de revisão (${label})`, async ({
    page,
  }) => {
    const course = await setup(page, {
      contents: [{ ...publishedTutorial, review_notes: notes }],
    })
    await page.goto(`/courses/${course.id}`)

    await expect(
      page.getByRole("region", { name: "Sobre este conteúdo" }),
    ).toBeVisible()
    await expect(evaluation(page)).toHaveCount(0)
  })
}

test("mantém a ordem das citações da API na rota do conteúdo", async ({
  page,
}) => {
  const course = await setup(page, {
    contents: [
      { ...publishedTutorial, cited_chunks: [0, 1, 2] },
      { format: "flashcards", status: "pending" },
    ],
  })
  const [tutorial] = course.contents
  const citations = [2, 0, 1].map((index) => {
    const citation = tutorial.citations.find(
      ({ text }) => text === chunks[index],
    )
    if (!citation)
      throw new Error(`A citação do trecho ${index} não foi criada.`)
    return citation
  })
  await page.route(`**/api/v1/courses/${course.id}`, async (route) => {
    const response = await route.fetch()
    const data: CourseDetail = await response.json()
    data.contents[0].citations = [
      { ...citations[0], similarity: 0.91, page_number: 3 },
      { ...citations[1], similarity: 0.82 },
      { ...citations[2], similarity: null },
    ]
    await route.fulfill({ response, json: data })
  })
  await page.goto(`/courses/${course.id}/contents/${tutorial.id}`)

  const items = citationItems(page)
  await expect(items).toContainText([chunks[2], chunks[0], chunks[1]])
  await expect(items.nth(0)).toContainText(
    "guia.md · página 3 · similaridade 0,91",
  )
  await expect(items.nth(1)).toContainText("guia.md · similaridade 0,82")
  await expect(items.nth(2)).not.toContainText("similaridade")
  await expect(items.nth(2)).not.toContainText("página")
})
