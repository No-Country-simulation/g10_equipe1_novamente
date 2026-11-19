import { expect, type Page, test } from "@playwright/test"
import type { CourseDetail } from "../src/client"
import { createCourse } from "./utils/course"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test.use({ storageState: { cookies: [], origins: [] } })

const introduction = "Revise os conceitos de observabilidade."
const hint = "Pense em como você investiga uma falha."

function flashcards(count = 8, topic = "Observabilidade") {
  return {
    introduction,
    cards: Array.from({ length: count }, (_, index) => ({
      front: `${topic}: pergunta ${index + 1}`,
      back: `${topic}: resposta ${index + 1}`,
      hint: index === 0 ? hint : null,
    })),
  }
}

async function openFlashcards(
  page: Page,
  content = flashcards(),
  status: "succeeded" | "running" = "succeeded",
) {
  const email = randomEmail()
  const password = randomPassword()
  await createUser({ email, password })
  const course = await createCourse({
    owner_email: email,
    title: "Curso de observabilidade",
    audience_level: "technical_basic",
    documents: [{ original_filename: "guia.md", status: "indexed" }],
    contents: [{ format: "flashcards", status, content }],
  })
  await logInUser(page, email, password)
  await page.goto(`/courses/${course.id}`)
  return course
}

test("mostra um cartão por vez e vira com clique ou teclado", async ({
  page,
}) => {
  await openFlashcards(page)

  const card = page.getByRole("button", { name: "Virar cartão" })
  const liveRegion = page.locator('[aria-live="polite"]').filter({
    hasText: "Observabilidade:",
  })
  await expect(page.getByText(introduction)).toBeVisible()
  await expect(page.getByText("CARTÃO 1 DE 8")).toBeVisible()
  await expect(card.getByText("PERGUNTA", { exact: true })).toBeVisible()
  await expect(card.getByText("Observabilidade: pergunta 1")).toBeVisible()
  await expect(
    card.getByText("Clique no cartão para ver a resposta"),
  ).toBeVisible()
  await expect(
    page.getByText("Observabilidade: pergunta 2", { exact: true }),
  ).toHaveCount(0)
  await expect(
    page.getByText("Observabilidade: resposta 1", { exact: true }),
  ).toHaveCount(0)
  await expect(page.getByRole("button", { name: "Anterior" })).toBeDisabled()
  await expect(card).toHaveAttribute("aria-pressed", "false")
  await expect(liveRegion).toHaveText("Pergunta: Observabilidade: pergunta 1")

  await card.click()
  await expect(card.getByText("RESPOSTA", { exact: true })).toBeVisible()
  await expect(card.getByText("Observabilidade: resposta 1")).toBeVisible()
  await expect(
    card.getByText("Clique no cartão para ver a pergunta"),
  ).toBeVisible()
  await expect(card).toHaveAttribute("aria-pressed", "true")
  await expect(liveRegion).toHaveText("Resposta: Observabilidade: resposta 1")

  await card.click()
  await expect(card.getByText("Observabilidade: pergunta 1")).toBeVisible()
  await card.focus()
  await page.keyboard.press("Space")
  await expect(card.getByText("Observabilidade: resposta 1")).toBeVisible()
  await page.keyboard.press("Enter")
  await expect(card.getByText("Observabilidade: pergunta 1")).toBeVisible()
})

test("mostra a dica sob demanda e fecha ao virar ou navegar", async ({
  page,
}) => {
  await openFlashcards(page)

  const card = page.getByRole("button", { name: "Virar cartão" })
  const showHint = page.getByRole("button", { name: "Mostrar dica" })
  const hintText = page.getByText(`Dica: ${hint}`)
  await expect(hintText).toHaveCount(0)
  await showHint.click()
  await expect(hintText).toBeVisible()
  await expect(hintText).toBeFocused()
  await expect(showHint).toHaveCount(0)

  await card.click()
  await expect(hintText).toHaveCount(0)
  await expect(showHint).toHaveCount(0)
  await card.click()
  await showHint.click()
  await page.getByRole("button", { name: "Próximo" }).click()
  await expect(showHint).toHaveCount(0)
  await expect(hintText).toHaveCount(0)

  await page.getByRole("button", { name: "Anterior" }).click()
  await expect(showHint).toBeVisible()
  await expect(hintText).toHaveCount(0)
})

test("navega até o último cartão e abre cada cartão pela frente", async ({
  page,
}) => {
  await openFlashcards(page)

  const card = page.getByRole("button", { name: "Virar cartão" })
  const next = page.getByRole("button", { name: "Próximo" })
  const previous = page.getByRole("button", { name: "Anterior" })
  const progress = page.getByRole("progressbar", {
    name: "Posição no conjunto",
  })
  await next.click()
  await expect(page.getByText("CARTÃO 2 DE 8")).toBeVisible()
  await expect(card.getByText("Observabilidade: pergunta 2")).toBeVisible()
  await expect(progress).toHaveAttribute("aria-valuemin", "1")
  await expect(progress).toHaveAttribute("aria-valuemax", "8")
  await expect(progress).toHaveAttribute("aria-valuenow", "2")
  await expect(progress).toHaveAttribute("aria-valuetext", "Cartão 2 de 8")

  await card.click()
  await expect(card.getByText("Observabilidade: resposta 2")).toBeVisible()
  await next.click()
  await previous.click()
  await expect(card.getByText("Observabilidade: pergunta 2")).toBeVisible()

  for (let position = 3; position <= 8; position++) {
    await next.click()
    await expect(page.getByText(`CARTÃO ${position} DE 8`)).toBeVisible()
  }
  await expect(next).toBeDisabled()
  await expect(previous).toBeEnabled()

  await page.reload()
  await expect(page.getByText("CARTÃO 1 DE 8")).toBeVisible()
  await expect(card.getByText("Observabilidade: pergunta 1")).toBeVisible()
})

test("mostra um aviso quando o conjunto está fora do formato", async ({
  page,
}) => {
  const errors: string[] = []
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text())
  })
  page.on("pageerror", (error) => errors.push(error.message))

  await openFlashcards(page, flashcards(3))

  await expect(page.getByRole("alert")).toHaveText(
    "Não foi possível mostrar este conteúdo, porque ele não está no formato esperado.",
  )
  await expect(page.getByText(introduction)).toHaveCount(0)
  await expect(page.getByRole("button", { name: "Virar cartão" })).toHaveCount(
    0,
  )
  await expect(
    page.getByRole("progressbar", { name: "Posição no conjunto" }),
  ).toHaveCount(0)
  expect(errors).toEqual([])
})

test("preserva o cartão durante a consulta e reinicia quando chega outro conjunto", async ({
  page,
}) => {
  const course = await openFlashcards(page, flashcards(12), "running")
  const card = page.getByRole("button", { name: "Virar cartão" })
  const next = page.getByRole("button", { name: "Próximo" })
  const progress = page.getByRole("progressbar", {
    name: "Posição no conjunto",
  })
  for (let position = 2; position <= 12; position++) {
    await next.click()
    await expect(progress).toHaveAttribute("aria-valuenow", String(position))
  }
  await card.click()
  await expect(card.getByText("Observabilidade: resposta 12")).toBeVisible()

  let replacement = false
  await page.route(`**/api/v1/courses/${course.id}`, async (route) => {
    const response = await route.fetch()
    const data: CourseDetail = await response.json()
    const [published] = data.contents
    const updated = replacement
      ? { ...published, content: flashcards(8, "Telemetria") }
      : {
          ...published,
          title: "Flashcards em atualização",
          content: { ...published.content, extra: true },
        }
    await route.fulfill({ response, json: { ...data, contents: [updated] } })
  })

  await expect(
    page.getByRole("heading", { name: "Flashcards em atualização" }),
  ).toBeVisible({ timeout: 8000 })
  await expect(progress).toHaveAttribute("aria-valuenow", "12")
  await expect(card.getByText("Observabilidade: resposta 12")).toBeVisible()

  replacement = true
  await expect(page.getByText("CARTÃO 1 DE 8")).toBeVisible({ timeout: 8000 })
  await expect(card.getByText("Telemetria: pergunta 1")).toBeVisible()
  await expect(card).toHaveAttribute("aria-pressed", "false")
  await expect(page.getByRole("button", { name: "Mostrar dica" })).toBeVisible()
  await expect(page.getByText(`Dica: ${hint}`)).toHaveCount(0)
})
