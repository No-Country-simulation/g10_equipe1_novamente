import { expect, type Page, test } from "@playwright/test"
import type { CourseDetail } from "../src/client"
import { createCourse } from "./utils/course"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test.use({ storageState: { cookies: [], origins: [] } })

const questions = [0, 2, 3, 1, 0].map((correct_index, index) => ({
  prompt: `Enunciado ${index + 1}`,
  options: ["Logs", "logs", "Métricas", "Traces"],
  correct_index,
  explanation: `Justificativa da pergunta ${index + 1}.`,
}))

async function setup(
  page: Page,
  content: Record<string, unknown> = { questions },
  status: "succeeded" | "running" = "succeeded",
) {
  const email = randomEmail()
  const password = randomPassword()
  await createUser({ email, password })
  const course = await createCourse({
    owner_email: email,
    title: "Curso de observabilidade",
    audience_level: "technical_basic",
    status: status === "running" ? "initializing" : "ready",
    documents: [{ original_filename: "guia.md" }],
    contents: [{ format: "quiz", status, content }],
  })
  await logInUser(page, email, password)
  await page.goto(`/courses/${course.id}`)
  return course
}

function quiz(page: Page) {
  return {
    options: page
      .getByRole("group", { name: "Opções de resposta" })
      .getByRole("button"),
    previous: page.getByRole("button", { name: "Pergunta anterior" }),
    next: page.getByRole("button", { name: "Próxima pergunta" }),
    explanation: page.getByRole("status"),
  }
}

test("mostra a primeira pergunta, as opções e a posição no quiz", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 800 })
  await setup(page)
  const { options, previous, next, explanation } = quiz(page)

  await expect(page.getByText("PERGUNTA 1 DE 5", { exact: true })).toBeVisible()
  await expect(page.getByRole("heading", { level: 3 })).toHaveText(
    questions[0].prompt,
  )
  const progress = page.getByRole("progressbar", { name: "Posição no quiz" })
  await expect(progress).toHaveAttribute("aria-valuemin", "1")
  await expect(progress).toHaveAttribute("aria-valuemax", "5")
  await expect(progress).toHaveAttribute("aria-valuenow", "1")
  await expect(progress).toHaveAttribute("aria-valuetext", "Pergunta 1 de 5")
  await expect(options).toHaveCount(4)
  for (const [index, text] of [
    "A Logs",
    "B logs",
    "C Métricas",
    "D Traces",
  ].entries()) {
    await expect(options.nth(index)).toHaveAccessibleName(text)
    await expect(options.nth(index)).toBeEnabled()
  }
  await expect(previous).toBeDisabled()
  await expect(next).toBeDisabled()
  await expect(explanation).toBeEmpty()
  await expect(
    page.getByRole("navigation", { name: "Navegação do quiz" }),
  ).toHaveCSS("flex-direction", "column")
})

test("revela a justificativa após qualquer escolha e mantém a leitura ao voltar", async ({
  page,
}) => {
  await setup(page)
  const { options, previous, next, explanation } = quiz(page)

  for (const [index, choice] of [questions[0].correct_index, 0].entries()) {
    await expect(next).toBeDisabled()
    const optionClasses = await options.first().getAttribute("class")
    await options.nth(choice).click()
    await expect(
      explanation.getByText("Justificativa", { exact: true }),
    ).toBeVisible()
    await expect(explanation).toContainText(questions[index].explanation)
    for (const option of await options.all()) {
      await expect(option).toBeDisabled()
      await expect(option).toHaveClass(optionClasses ?? "")
    }
    await expect(
      page
        .locator('[aria-pressed="true"], [aria-selected="true"]')
        .and(options),
    ).toHaveCount(0)
    await expect(next).toBeEnabled()
    if (index === 0) await next.click()
  }

  await previous.click()
  await expect(page.getByText("PERGUNTA 1 DE 5", { exact: true })).toBeVisible()
  await expect(explanation).toContainText(questions[0].explanation)
  await expect(options.and(page.locator(":disabled"))).toHaveCount(4)
  await expect(next).toBeEnabled()
})

test("mostra só o botão de voltar na última pergunta e reinicia ao recarregar", async ({
  page,
}) => {
  await setup(page)
  const { options, previous, next, explanation } = quiz(page)

  for (const question of questions.slice(0, -1)) {
    await options.nth(question.correct_index).click()
    await next.click()
  }
  await expect(page.getByText("PERGUNTA 5 DE 5", { exact: true })).toBeVisible()
  await expect(
    page.getByRole("progressbar", { name: "Posição no quiz" }),
  ).toHaveAttribute("aria-valuenow", "5")
  await options.first().click()
  await expect(explanation).toContainText(questions[4].explanation)
  await expect(
    page
      .getByRole("navigation", { name: "Navegação do quiz" })
      .getByRole("button"),
  ).toHaveCount(1)
  await expect(previous).toBeEnabled()
  await expect(next).toHaveCount(0)
  await expect(
    page.getByRole("button", { name: /refazer|resultado/i }),
  ).toHaveCount(0)
  await previous.click()
  await expect(explanation).toContainText(questions[3].explanation)

  await page.reload()
  await expect(page.getByRole("heading", { level: 3 })).toHaveText(
    questions[0].prompt,
  )
  await expect(explanation).toBeEmpty()
  await expect(options.and(page.locator(":enabled"))).toHaveCount(4)
  await expect(next).toBeDisabled()
})

const invalidContents = [
  ["quatro perguntas", { questions: questions.slice(0, -1) }],
  [
    "opções repetidas após trim",
    {
      questions: [
        { ...questions[0], options: ["Logs", " Logs ", "Métricas", "Traces"] },
        ...questions.slice(1),
      ],
    },
  ],
  [
    "índice correto fora do intervalo",
    {
      questions: [{ ...questions[0], correct_index: 4 }, ...questions.slice(1)],
    },
  ],
] as const

for (const [reason, content] of invalidContents) {
  test(`mostra aviso para quiz com ${reason}`, async ({ page }) => {
    const errors: string[] = []
    page.on("pageerror", (error) => errors.push(error.message))
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text())
    })
    await setup(page, content)
    await expect(page.getByRole("alert")).toHaveText(
      "Não foi possível mostrar este conteúdo, porque ele não está no formato esperado.",
    )
    await expect(page.getByRole("progressbar")).toHaveCount(0)
    await expect(page.getByRole("heading", { level: 3 })).toHaveCount(0)
    await expect(quiz(page).options).toHaveCount(0)
    await expect(quiz(page).next).toHaveCount(0)
    expect(errors).toEqual([])
  })
}

test("preserva perguntas iguais e reinicia a leitura quando o quiz muda", async ({
  page,
}) => {
  const course = await setup(page, { questions }, "running")
  const { options, previous, next, explanation } = quiz(page)
  await options.first().click()
  await next.click()

  let update = {
    title: "Quiz consultado",
    content: { questions, extra: "Campo ignorado" },
  }
  await page.route(`**/api/v1/courses/${course.id}`, async (route) => {
    const response = await route.fetch()
    const data: CourseDetail = await response.json()
    await route.fulfill({
      response,
      json: { ...data, contents: [{ ...data.contents[0], ...update }] },
    })
  })
  await expect(page.getByRole("heading", { name: update.title })).toBeVisible({
    timeout: 8000,
  })
  await expect(page.getByRole("heading", { level: 3 })).toHaveText(
    questions[1].prompt,
  )
  await previous.click()
  await expect(explanation).toContainText(questions[0].explanation)
  await expect(options.and(page.locator(":disabled"))).toHaveCount(4)
  await next.click()

  const newQuestions = questions.map((question) => ({
    ...question,
    prompt: `Novo ${question.prompt}`,
  }))
  update = {
    title: "Quiz atualizado",
    content: { questions: newQuestions, extra: "Campo ignorado" },
  }
  await expect(page.getByRole("heading", { level: 3 })).toHaveText(
    newQuestions[0].prompt,
    { timeout: 8000 },
  )
  await expect(explanation).toBeEmpty()
  await expect(options.and(page.locator(":enabled"))).toHaveCount(4)
  await expect(previous).toBeDisabled()
  await expect(next).toBeDisabled()
})
