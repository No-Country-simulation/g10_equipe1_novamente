import { expect, test } from "@playwright/test"
import type { PrivateCourseCreate } from "../src/client"
import { createCourse } from "./utils/course"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test.use({ storageState: { cookies: [], origins: [] } })

async function setup(
  page: import("@playwright/test").Page,
  changes: Partial<PrivateCourseCreate> = {},
) {
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
    contents: [
      {
        format: "tutorial",
        status: "succeeded",
        title: "Introdução",
        content: {},
        estimated_minutes: 12,
        key_concepts: ["Conceito A", "Conceito B"],
        prerequisites: ["Base"],
      },
    ],
    ...changes,
  })
  await logInUser(page, email, password)
  return course
}

test("mostra conteúdo publicado e materiais", async ({ page }) => {
  const course = await setup(page)
  await page.goto(`/courses/${course.id}`)
  for (const text of [
    "Curso de teste",
    "Técnico básico",
    "Geral",
    "Pronto",
    "Introdução",
    "12 min de estudo",
    "Conceito A",
    "Conceito B",
    "Base",
    "O leitor deste formato ainda não está disponível.",
    "MATERIAIS USADOS",
    "guia.md",
    "notas.md",
  ])
    await expect(page.getByText(text, { exact: true })).toBeVisible()
  await expect(
    page.getByRole("heading", { name: "Curso de teste", level: 1 }),
  ).toBeVisible()
  await expect(
    page.getByRole("heading", { name: "Introdução", level: 2 }),
  ).toBeVisible()
  const materials = page
    .locator("section")
    .filter({ has: page.getByRole("heading", { name: "MATERIAIS USADOS" }) })
  await expect(materials.locator("span")).toHaveText(["guia.md", "notas.md"])
  await expect(page.getByRole("tab")).toHaveCount(0)
})

test("mostra abas, estados e erro preservando linhas", async ({ page }) => {
  const course = await setup(page, {
    contents: [
      { format: "tutorial", status: "succeeded", content: {} },
      { format: "flashcards", status: "pending" },
      {
        format: "quiz",
        status: "failed",
        error_message: "linha um\nlinha dois",
      },
    ],
  })
  await page.goto(`/courses/${course.id}`)
  await expect(page.getByRole("tab")).toHaveText([
    "Tutorial Pronto",
    "Flashcards Na fila",
    "Quiz Falhou",
  ])
  await expect(page.getByText("Nenhum")).toBeVisible()
  await page.getByRole("tab", { name: "Quiz Falhou" }).click()
  await expect(page.getByText("A geração falhou")).toBeVisible()
  const error = page
    .getByRole("alert")
    .locator('[data-slot="alert-description"]')
  await expect(error).toHaveCSS("white-space", "pre-wrap")
  await expect(error).toHaveJSProperty("innerText", "linha um\nlinha dois")
  await page.getByRole("tab", { name: "Flashcards Na fila" }).click()
  await expect(page.getByText(/Na fila\./)).toBeVisible()
})

test("atualiza somente conteúdo ativo", async ({ page }) => {
  const course = await setup(page, {
    status: "initializing",
    contents: [{ format: "tutorial", status: "pending" }],
  })
  let requests = 0
  page.on("request", (request) => {
    if (request.url().includes(`/api/v1/courses/${course.id}`)) requests++
  })
  await page.goto(`/courses/${course.id}`)
  await expect.poll(() => requests, { timeout: 8000 }).toBeGreaterThanOrEqual(2)
})

test("não atualiza curso concluído", async ({ page }) => {
  const course = await setup(page)
  let requests = 0
  page.on("request", (request) => {
    if (request.url().includes(`/api/v1/courses/${course.id}`)) requests++
  })
  await page.goto(`/courses/${course.id}`)
  await expect(page.getByText("Introdução")).toBeVisible()
  await page.waitForTimeout(5000)
  expect(requests).toBe(1)
})

test("documento com falha e curso inexistente", async ({ page }) => {
  const course = await setup(page, {
    status: "failed",
    documents: [{ original_filename: "guia.md", status: "failed" }],
  })
  await page.goto(`/courses/${course.id}`)
  const alert = page.getByRole("alert")
  await expect(alert.getByText("Um documento falhou")).toBeVisible()
  await expect(alert.getByText("guia.md")).toBeVisible()
  await expect(page.getByText("MATERIAIS USADOS")).toHaveCount(0)
  await page.goto("/courses/00000000-0000-0000-0000-000000000000")
  await expect(page.getByText("Curso não encontrado.")).toBeVisible()
})

test("sem login redireciona", async ({ page }) => {
  await page.goto("/courses/00000000-0000-0000-0000-000000000000")
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
