import { expect, type Page, test } from "@playwright/test"
import type { PrivateCourseCreate } from "../src/client"
import { createCourse } from "./utils/course"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test.use({ storageState: { cookies: [], origins: [] } })

const blocked = "Espere a geração terminar para excluir o curso."
const inactive = { format: "tutorial", status: "failed" } as const

async function openCourse(
  page: Page,
  contents: PrivateCourseCreate["contents"],
) {
  const email = randomEmail()
  const password = randomPassword()
  await createUser({ email, password })
  const course = await createCourse({
    owner_email: email,
    title: "Curso para excluir",
    audience_level: "technical_basic",
    documents: [{ original_filename: "guia.md", status: "indexed" }],
    contents,
  })
  await logInUser(page, email, password)
  await page.goto(`/courses/${course.id}`)
  return {
    course,
    trigger: page
      .getByRole("region", { name: "Resumo do curso" })
      .getByRole("button", { name: "Excluir curso" }),
    dialog: page.getByRole("dialog", { name: "Excluir este curso?" }),
  }
}

test("cancela e depois exclui um curso de saída única pela API", async ({
  page,
}) => {
  const { course, trigger, dialog } = await openCourse(page, [inactive])
  await trigger.click()
  await dialog.getByRole("button", { name: "Cancelar" }).click()
  await expect(dialog).toBeHidden()
  await expect(page).toHaveURL(`/courses/${course.id}`)

  await trigger.click()
  const deleted = page.waitForResponse(
    (response) =>
      response.url().endsWith(`/api/v1/courses/${course.id}`) &&
      response.request().method() === "DELETE",
  )
  await dialog.getByRole("button", { name: "Excluir", exact: true }).click()
  expect((await deleted).status()).toBe(204)
  await expect(page).toHaveURL("/courses")
  await expect(page.getByText("Curso excluído.", { exact: true })).toBeVisible()
  await expect(page.getByText(course.title, { exact: true })).toHaveCount(0)
})

test("desabilita a exclusão quando uma das saídas está na fila", async ({
  page,
}) => {
  const { trigger } = await openCourse(page, [
    inactive,
    { format: "flashcards", status: "pending" },
  ])
  await expect(trigger).toBeDisabled()
  await expect(page.getByText(blocked, { exact: true })).toBeVisible()
})

test("mostra o detalhe do 409 e mantém o curso com várias saídas aberto", async ({
  page,
}) => {
  const { course, trigger, dialog } = await openCourse(page, [
    inactive,
    { format: "flashcards", status: "failed" },
  ])
  await trigger.click()
  await page.route(`**/api/v1/courses/${course.id}`, async (route) => {
    if (route.request().method() !== "DELETE") {
      await route.continue()
      return
    }
    await route.fulfill({ status: 409, json: { detail: blocked } })
  })
  await dialog.getByRole("button", { name: "Excluir", exact: true }).click()
  await expect(page.getByText(blocked, { exact: true })).toBeVisible()
  await expect(page).toHaveURL(`/courses/${course.id}`)
  await expect(dialog).toBeVisible()
})
