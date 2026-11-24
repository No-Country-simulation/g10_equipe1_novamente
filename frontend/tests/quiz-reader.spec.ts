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
    feedback: page.getByRole("status"),
    result: page.getByTestId("quiz-result"),
  }
}

test("mostra a primeira pergunta, as opções e a posição no quiz", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 800 })
  await setup(page)
  const { options, previous, next, feedback } = quiz(page)

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
    await expect(options.nth(index)).toHaveCSS("border-radius", "8px")
  }
  await expect(previous).toBeDisabled()
  await expect(next).toBeDisabled()
  await expect(feedback).toHaveAttribute("aria-atomic", "true")
  await expect(feedback).toBeEmpty()
  await expect(
    page.getByRole("navigation", { name: "Navegação do quiz" }),
  ).toHaveCSS("flex-direction", "column")
})

test("corrige a resposta, mostra a justificativa e mantém o resultado ao voltar", async ({
  page,
}) => {
  await setup(page)
  const { options, previous, next, feedback, result } = quiz(page)
  const selected = options.first()

  await selected.press("Enter")
  await expect(next).toBeFocused()
  await expect(selected).toHaveAccessibleName("Logs Sua resposta · correta")
  await expect(selected.locator("svg.lucide-check")).toHaveAttribute(
    "aria-hidden",
    "true",
  )
  await expect(feedback).toHaveText(
    `Resposta correta. ${questions[0].explanation}`,
  )
  await expect(result).toHaveAttribute("aria-hidden", "true")
  await expect(
    result.getByText("Resposta correta", { exact: true }),
  ).toBeVisible()
  await expect(options.and(page.locator(":disabled"))).toHaveCount(4)
  await expect(next).toBeEnabled()
  await next.click()

  await expect(next).toBeDisabled()
  await expect(feedback).toBeEmpty()
  await selected.press("Space")
  await expect(next).toBeFocused()
  await expect(selected).toHaveAccessibleName("Logs Sua resposta · incorreta")
  await expect(selected.locator("svg.lucide-x")).toHaveAttribute(
    "aria-hidden",
    "true",
  )
  await expect(options.nth(1)).toHaveAccessibleName("B logs")
  await expect(options.nth(2)).toHaveAccessibleName("Métricas Resposta correta")
  await expect(options.nth(3)).toHaveAccessibleName("D Traces")
  await expect(options.and(page.locator(":disabled"))).toHaveCount(4)
  await expect(feedback).toHaveText(
    `Não foi dessa vez. A resposta certa é C: Métricas. ${questions[1].explanation}`,
  )
  await expect(result.locator("p")).toHaveText([
    "Não foi dessa vez",
    "A resposta certa é C: Métricas.",
    questions[1].explanation,
  ])

  await previous.click()
  await expect(page.getByText("PERGUNTA 1 DE 5", { exact: true })).toBeVisible()
  await expect(selected).toHaveAccessibleName("Logs Sua resposta · correta")
  await expect(feedback).toContainText("Resposta correta")
  await expect(feedback).toContainText(questions[0].explanation)
  await expect(options.and(page.locator(":disabled"))).toHaveCount(4)
  await expect(next).toBeEnabled()
})

for (const [colorScheme, colors] of [
  [
    "light",
    [
      ["rgb(251, 227, 225)", "rgb(179, 38, 30)", "rgb(127, 29, 23)"],
      ["rgb(246, 247, 244)", "rgb(213, 217, 210)", "rgb(85, 91, 102)"],
      ["rgb(212, 240, 228)", "rgb(20, 82, 58)", "rgb(20, 82, 58)"],
    ],
  ],
  [
    "dark",
    [
      [
        "oklch(0.269 0 0)",
        "oklch(0.704 0.191 22.216)",
        "oklch(0.704 0.191 22.216)",
      ],
      ["oklch(0.145 0 0)", "oklch(1 0 0 / 0.1)", "oklch(0.708 0 0)"],
      ["oklch(0.269 0 0)", "oklch(0.765 0.135 163)", "oklch(0.765 0.135 163)"],
    ],
  ],
] as const) {
  test(`mantém cores e encaixa a correção em 360 px no tema ${colorScheme}`, async ({
    page,
  }) => {
    const longOption = "Métricas".repeat(24)
    await setup(page, {
      questions: [
        questions[0],
        { ...questions[1], options: ["Logs", "logs", longOption, "Traces"] },
        ...questions.slice(2),
      ],
    })
    await page.getByRole("button", { name: "Alterar tema" }).click()
    await page
      .getByRole("menuitem", {
        name: colorScheme === "light" ? "Claro" : "Escuro",
      })
      .click()
    const { options, next, result } = quiz(page)
    const [, incorrectColor] = colors[0]
    const [, correctColor] = colors[2]

    await options.first().click()
    await expect(result).toHaveCSS("border-left-color", correctColor)
    await expect(result).toHaveCSS("border-left-width", "6px")
    await expect(
      result.getByText("Resposta correta", { exact: true }),
    ).toHaveCSS("color", correctColor)

    await next.click()
    await options.first().click()
    await expect(result).toHaveCSS("border-left-color", incorrectColor)
    await expect(result).toHaveCSS("border-left-width", "6px")
    await expect(
      result.getByText("Não foi dessa vez", { exact: true }),
    ).toHaveCSS("color", incorrectColor)

    for (const [index, [background, border, text]] of colors.entries()) {
      const option = options.nth(index)
      await expect(option).toHaveCSS("background-color", background)
      await expect(option).toHaveCSS("border-top-color", border)
      await expect(option).toHaveCSS(
        "border-top-width",
        index === 1 ? "1px" : "2px",
      )
      await expect(option).toHaveCSS("color", text)
    }
    for (const option of await options.all()) {
      await expect(option).toHaveCSS("opacity", "1")
    }
    await expect(options.first().locator("svg")).toHaveCSS("width", "18px")

    await page.setViewportSize({ width: 360, height: 800 })
    const correct = options.nth(2)
    const text = correct.getByText(longOption, { exact: true })
    const label = correct.getByText("Resposta correta", { exact: true })
    await expect(label).toBeVisible()
    const textBox = (await text.boundingBox())!
    const labelBox = (await label.boundingBox())!
    expect(labelBox.y).toBeGreaterThanOrEqual(textBox.y + textBox.height)
    expect(labelBox.x).toBe(textBox.x)
    const hasHorizontalOverflow = await page.evaluate(() =>
      [
        document.documentElement,
        ...document.querySelectorAll(
          'fieldset[aria-label="Opções de resposta"] button, [data-testid="quiz-result"]',
        ),
      ].some((element) => element.scrollWidth > element.clientWidth),
    )
    expect(hasHorizontalOverflow).toBe(false)
  })
}

test("mostra só o botão de voltar na última pergunta e reinicia ao recarregar", async ({
  page,
}) => {
  await setup(page)
  const { options, previous, next, feedback } = quiz(page)

  for (const question of questions.slice(0, -1)) {
    await options.nth(question.correct_index).click()
    await next.click()
  }
  await expect(page.getByText("PERGUNTA 5 DE 5", { exact: true })).toBeVisible()
  await expect(
    page.getByRole("progressbar", { name: "Posição no quiz" }),
  ).toHaveAttribute("aria-valuenow", "5")
  await options.first().press("Enter")
  await expect(previous).toBeFocused()
  await expect(options.first()).toHaveAccessibleName(
    "Logs Sua resposta · correta",
  )
  await expect(feedback).toContainText("Resposta correta")
  await expect(feedback).toContainText(questions[4].explanation)
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
  await expect(feedback).toContainText(questions[3].explanation)

  await page.reload()
  await expect(page.getByRole("heading", { level: 3 })).toHaveText(
    questions[0].prompt,
  )
  await expect(feedback).toBeEmpty()
  await expect(options.first()).toHaveAccessibleName("A Logs")
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
  const { options, previous, next, feedback } = quiz(page)
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
  await expect(options.first()).toHaveAccessibleName(
    "Logs Sua resposta · correta",
  )
  await expect(feedback).toContainText("Resposta correta")
  await expect(feedback).toContainText(questions[0].explanation)
  await expect(options.and(page.locator(":disabled"))).toHaveCount(4)
  await next.click()

  update = {
    title: "Quiz atualizado",
    content: {
      questions: [{ ...questions[0], correct_index: 1 }, ...questions.slice(1)],
      extra: "Campo ignorado",
    },
  }
  await expect(page.getByRole("heading", { level: 3 })).toHaveText(
    questions[0].prompt,
    { timeout: 8000 },
  )
  await expect(feedback).toBeEmpty()
  await expect(options.and(page.locator(":enabled"))).toHaveCount(4)
  await expect(previous).toBeDisabled()
  await expect(next).toBeDisabled()
})
