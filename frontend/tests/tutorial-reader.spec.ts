import { expect, type Page, test } from "@playwright/test"
import type { PrivateCourseCreate } from "../src/client"
import { createCourse } from "./utils/course"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test.use({ storageState: { cookies: [], origins: [] } })

const tutorial = {
  summary: "Aprenda a medir o tempo de uma operação.",
  sections: [
    { title: "Instale o SDK", body: "Adicione o pacote ao projeto." },
    { title: "Crie um span", body: "Envolva a operação em um span." },
  ],
  takeaways: ["O SDK gera os sinais.", "Um span mede uma operação."],
}

async function openCourse(
  page: Page,
  content: Record<string, unknown> = tutorial,
  otherContents: PrivateCourseCreate["contents"] = [],
) {
  const email = randomEmail()
  const password = randomPassword()
  await createUser({ email, password })
  const course = await createCourse({
    owner_email: email,
    title: "Curso de observabilidade",
    audience_level: "technical_basic",
    status: "ready",
    documents: [{ original_filename: "guia.md", status: "indexed" }],
    contents: [
      { format: "tutorial", status: "succeeded", title: "Introdução", content },
      ...otherContents,
    ],
  })
  await logInUser(page, email, password)
  await page.goto(`/courses/${course.id}`)
}

test("mostra o resumo, as seções em ordem e a lista Para levar", async ({
  page,
}) => {
  await openCourse(page, { ...tutorial, extra: true })

  await expect(page.getByText(tutorial.summary, { exact: true })).toBeVisible()
  await expect(page.getByRole("heading", { level: 3 })).toHaveText([
    "Instale o SDK",
    "Crie um span",
    "Para levar",
  ])
  for (const section of tutorial.sections) {
    await expect(page.getByText(section.body, { exact: true })).toBeVisible()
  }
  await expect(
    page
      .getByRole("list")
      .filter({ hasText: tutorial.takeaways[0] })
      .getByRole("listitem"),
  ).toHaveText(tutorial.takeaways)
})

test("renderiza listas, tabela, bloco de código e código no texto", async ({
  page,
}) => {
  const body = [
    "- Abra o terminal",
    "- Confira a saída",
    "",
    "1. Inicie o serviço",
    "2. Envie uma requisição",
    "",
    "| Sinal | Uso |",
    "| --- | --- |",
    "| Trace | Rastrear uma operação |",
    "",
    "```sh",
    "bun run dev",
    "```",
    "",
    "Execute o `comando` acima.",
  ].join("\n")
  await openCourse(page, { ...tutorial, sections: [{ title: "Passos", body }] })

  await expect(
    page
      .locator("ul")
      .filter({ hasText: "Abra o terminal" })
      .getByRole("listitem"),
  ).toHaveText(["Abra o terminal", "Confira a saída"])
  await expect(page.locator("ol").getByRole("listitem")).toHaveText([
    "Inicie o serviço",
    "Envie uma requisição",
  ])
  const table = page.getByRole("table")
  await expect(table.getByRole("columnheader")).toHaveText(["Sinal", "Uso"])
  await expect(table.getByRole("cell")).toHaveText([
    "Trace",
    "Rastrear uma operação",
  ])
  await expect(page.locator("pre code")).toHaveText("bun run dev")
  await expect(page.locator("p code")).toHaveText("comando")
})

test("mostra o título do Markdown como h4", async ({ page }) => {
  await openCourse(page, {
    ...tutorial,
    sections: [{ title: "Passos", body: "# Título interno" }],
  })

  await expect(
    page.getByRole("heading", { name: "Título interno", level: 4 }),
  ).toBeVisible()
  await expect(
    page.getByRole("heading", { name: "Título interno", level: 1 }),
  ).toHaveCount(0)
})

test("mantém o texto e descarta tags HTML", async ({ page }) => {
  await openCourse(page, {
    ...tutorial,
    sections: [{ title: "Passos", body: "Texto em <b>negrito</b>." }],
  })

  await expect(page.getByText("Texto em negrito.")).toBeVisible()
  await expect(page.locator("b").filter({ hasText: "negrito" })).toHaveCount(0)
})

test("avisa quando o tutorial está fora do formato sem erros no console", async ({
  page,
}) => {
  const errors: string[] = []
  page.on("pageerror", (error) => errors.push(error.message))
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text())
  })
  await openCourse(page, { summary: "Resumo inválido." })

  await expect(page.getByRole("alert")).toHaveText(
    "Não foi possível mostrar este conteúdo, porque ele não está no formato esperado.",
  )
  await expect(page.getByText("Resumo inválido.")).toHaveCount(0)
  await expect(page.getByRole("heading", { level: 3 })).toHaveCount(0)
  expect(errors).toEqual([])
})

test("abre o tutorial pela grade do curso", async ({ page }) => {
  await openCourse(page, tutorial, [{ format: "quiz", status: "pending" }])

  await page.getByRole("link", { name: "Abrir Introdução" }).click()
  await expect(page.getByText(tutorial.summary, { exact: true })).toBeVisible()
})
