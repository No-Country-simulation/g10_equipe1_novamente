import { expect, type Page, test } from "@playwright/test"
import { createCourse } from "./utils/course"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test.use({ storageState: { cookies: [], origins: [] } })

async function setup(page: Page, multiple = false) {
  const email = randomEmail()
  const password = randomPassword()
  await createUser({ email, password })
  const course = await createCourse({
    owner_email: email,
    title: "Curso de teste",
    audience_level: "technical_basic",
    status: "failed",
    documents: [{ original_filename: "guia.md", status: "indexed" }],
    contents: [
      { format: "quiz", status: "failed", error_message: "Falha de teste." },
      ...(multiple
        ? ([{ format: "flashcards", status: "pending" }] as const)
        : []),
    ],
  })
  await logInUser(page, email, password)
  return course
}

test("tenta de novo no alerta e volta a consultar o curso", async ({
  page,
}) => {
  const course = await setup(page)
  const content = course.contents[0]
  const pending = {
    ...course,
    status: "initializing",
    contents: [{ ...content, status: "pending", error_message: null }],
  }
  const apiPath = `**/api/v1/courses/${course.id}`
  const retryPath = `${apiPath}/contents/${content.id}/retry`
  let sends = 0
  let accepted = false
  let release = () => {}
  const response = new Promise<void>((resolve) => {
    release = resolve
  })
  await page.route(retryPath, async (route) => {
    expect(route.request().method()).toBe("POST")
    sends++
    await response
    accepted = true
    await route.fulfill({ status: 202, json: pending })
  })
  await page.route(apiPath, (route) =>
    accepted ? route.fulfill({ json: pending }) : route.continue(),
  )

  await page.goto(`/courses/${course.id}`)
  const retry = page.getByRole("alert").getByRole("button", {
    name: "Tentar novamente",
  })
  await retry.click()
  await expect(retry).toBeDisabled()
  await retry.evaluate((button: HTMLButtonElement) => button.click())
  const nextGet = page.waitForResponse(
    (reply) => accepted && reply.url().endsWith(`/courses/${course.id}`),
  )
  release()
  await expect(page.getByText(/^Na fila\./)).toBeVisible()
  expect(await (await nextGet).json()).toMatchObject(pending)
  expect(sends).toBe(1)
  await expect(retry).toHaveCount(0)
})

test("mostra o botão só no cartão que falhou e exibe o erro da API", async ({
  page,
}) => {
  const course = await setup(page, true)
  const detail = "A geração foi interrompida. Tente novamente."
  await page.route(
    `**/api/v1/courses/${course.id}/contents/${course.contents[0].id}/retry`,
    (route) => route.fulfill({ status: 409, json: { detail } }),
  )
  await page.goto(`/courses/${course.id}`)
  await expect(
    page.getByRole("button", { name: "Tentar novamente" }),
  ).toHaveCount(1)
  const retry = page
    .locator('[data-slot="card"]')
    .filter({ has: page.getByRole("heading", { name: "Quiz", exact: true }) })
    .getByRole("button", { name: "Tentar novamente" })
  await retry.click()
  await expect(page.getByText(detail)).toBeVisible()
  await expect(retry).toBeEnabled()
})
