import { expect, type Page, test } from "@playwright/test"
import type { CourseDetail } from "../src/client"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test.use({ storageState: { cookies: [], origins: [] } })

const sourceSentence =
  "O comando git status mostra o estado da árvore de trabalho."
const markdown = [
  "# Comandos Git",
  "",
  sourceSentence,
  "O comando git add prepara alterações para o próximo commit.",
  "O comando git commit registra as alterações preparadas.",
  "O comando git log mostra o histórico de commits.",
  "O comando git diff mostra diferenças entre versões.",
  "O comando git branch lista as branches locais.",
  "O comando git switch troca a branch atual.",
  "O comando git fetch busca referências de um repositório remoto.",
].join("\n")

async function submitCourse(page: Page, title: string, formats: string[]) {
  const email = randomEmail()
  const password = randomPassword()
  await createUser({ email, password })
  await logInUser(page, email, password)
  await page.goto("/courses/new")

  await page.getByLabel("Arquivos", { exact: true }).setInputFiles({
    name: "comandos-git.md",
    mimeType: "text/markdown",
    buffer: Buffer.from(markdown),
  })
  const next = page.getByRole("button", { name: "Continuar" })
  await next.click()
  await page.getByRole("textbox", { name: "Título do curso" }).fill(title)
  await page.getByRole("combobox", { name: "Setor" }).click()
  await page.getByRole("option", { name: "Geral", exact: true }).click()
  await page.getByRole("radio", { name: "Técnico básico" }).check()
  await next.click()
  for (const name of formats) {
    await page.getByRole("checkbox", { name, exact: true }).check()
  }

  const created = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/courses/") &&
      response.request().method() === "POST",
  )
  await page.getByRole("button", { name: "Criar curso", exact: true }).click()
  const response = await created
  expect(response.status()).toBe(201)
  const course: CourseDetail = await response.json()
  const coursePath = `/courses/${course.id}`
  await expect(page).toHaveURL(coursePath)
  await expect(
    page.getByRole("heading", { name: title, level: 1 }),
  ).toBeVisible()
  return coursePath
}

test("cria um curso e abre os três leitores com conteúdo gerado", async ({
  page,
}) => {
  const title = "Comandos Git"
  const coursePath = await submitCourse(page, title, [
    "Tutorial",
    "Flashcards",
    "Quiz",
  ])
  await expect(page.getByText("Pronto", { exact: true })).toHaveCount(3, {
    timeout: 15_000,
  })

  await page.getByRole("link", { name: "Todos os cursos" }).click()
  const courseEntry = page.getByRole("link", { name: title, exact: true })
  await expect(courseEntry).toHaveAttribute("href", coursePath)
  await expect(courseEntry.getByText("Pronto", { exact: true })).toBeVisible()
  await courseEntry.click()

  await page.getByRole("link", { name: "Abrir Guia de comandos Git" }).click()
  await expect(
    page.getByText("Conheça os comandos básicos do Git."),
  ).toBeVisible()
  await expect(
    page.getByRole("heading", { name: "Estado da árvore de trabalho" }),
  ).toBeVisible()
  await expect(page.getByRole("heading", { name: "Para levar" })).toBeVisible()
  await expect(
    page.getByText("Use git status para conferir a árvore de trabalho."),
  ).toBeVisible()
  const evaluation = page.getByRole("region", { name: "Avaliação" })
  await expect(evaluation.getByText("100%", { exact: true })).toBeVisible()
  const citations = evaluation
    .getByRole("list", { name: "Trechos citados" })
    .getByRole("listitem")
  await expect(citations).toHaveCount(1)
  await expect(citations).toContainText(sourceSentence)
  await expect(
    citations.getByText("comandos-git.md", { exact: true }),
  ).toBeVisible()

  await page.getByRole("link", { name: "Voltar ao curso" }).click()
  await page
    .getByRole("link", { name: "Abrir Cartões de comandos Git" })
    .click()
  const card = page.getByRole("button", { name: "Virar cartão" })
  await expect(card).toContainText("O que faz git status?")
  await card.click()
  await expect(card).toContainText("Mostra o estado da árvore de trabalho.")

  await page.getByRole("link", { name: "Voltar ao curso" }).click()
  await page.getByRole("link", { name: "Abrir Quiz de comandos Git" }).click()
  await page.getByRole("button", { name: "A git status", exact: true }).click()
  const feedback = page
    .getByRole("status")
    .filter({ hasText: "Resposta correta" })
  await expect(feedback).toBeVisible()
  await expect(feedback).toContainText(sourceSentence)
})

test("mostra a reprovação do foco e omite o leitor", async ({ page }) => {
  const title = "[falha] Administração de banco de dados"
  const coursePath = await submitCourse(page, title, ["Tutorial"])

  const alert = page.getByRole("alert").filter({ hasText: "A geração falhou" })
  await expect(alert).toBeVisible({ timeout: 15_000 })
  await expect(alert).toContainText("O documento não trata do assunto pedido.")
  await expect(
    page.getByRole("region", { name: "Sobre este conteúdo" }),
  ).toHaveCount(0)
  await expect(page.getByRole("heading", { name: "Para levar" })).toHaveCount(0)

  await page.getByRole("link", { name: "Todos os cursos" }).click()
  const courseEntry = page.getByRole("link", { name: title, exact: true })
  await expect(courseEntry).toHaveAttribute("href", coursePath)
  await expect(courseEntry.getByText("Falhou", { exact: true })).toBeVisible()
})
