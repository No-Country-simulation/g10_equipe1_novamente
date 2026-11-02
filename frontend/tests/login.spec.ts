import { expect, type Page, test } from "@playwright/test"
import { createUser } from "./utils/privateApi.ts"
import { randomEmail, randomPassword } from "./utils/random.ts"

test.use({ storageState: { cookies: [], origins: [] } })

let email: string
let password: string

test.beforeAll(async () => {
  email = randomEmail()
  password = randomPassword()
  await createUser({ email, password })
})

const fillForm = async (page: Page, email: string, password: string) => {
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
}

const verifyInput = async (page: Page, testId: string) => {
  const input = page.getByTestId(testId)
  await expect(input).toBeVisible()
  await expect(input).toHaveText("")
  await expect(input).toBeEditable()
}

test("Inputs are visible, empty and editable", async ({ page }) => {
  await page.goto("/login")

  await verifyInput(page, "email-input")
  await verifyInput(page, "password-input")
})

test("Log In button is visible", async ({ page }) => {
  await page.goto("/login")

  await expect(page.getByRole("button", { name: "Entrar" })).toBeVisible()
})

test("Log in with valid email and password ", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, email, password)
  await page.getByRole("button", { name: "Entrar" }).click()

  await page.waitForURL("/")

  await expect(page.getByText("Que bom ter você de volta!")).toBeVisible()
})

test("Log in with invalid email", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, "invalidemail", password)
  await page.getByRole("button", { name: "Entrar" }).click()

  await expect(page.getByText("Informe um e-mail válido")).toBeVisible()
})

test("Log in with invalid password", async ({ page }) => {
  await page.goto("/login")
  await fillForm(page, email, randomPassword())
  await page.getByRole("button", { name: "Entrar" }).click()

  await expect(page.getByText("E-mail ou senha incorretos")).toBeVisible()
})

test("Successful log out", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, email, password)
  await page.getByRole("button", { name: "Entrar" }).click()

  await page.waitForURL("/")

  await expect(page.getByText("Que bom ter você de volta!")).toBeVisible()

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Sair" }).click()
  await page.waitForURL("/login")
})

test("Logged-out user cannot access protected routes", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, email, password)
  await page.getByRole("button", { name: "Entrar" }).click()

  await page.waitForURL("/")

  await expect(page.getByText("Que bom ter você de volta!")).toBeVisible()

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Sair" }).click()
  await page.waitForURL("/login")

  await page.goto("/settings")
  await page.waitForURL("/login")
})

test("Redirects to /login when token is wrong", async ({ page }) => {
  await page.goto("/settings")
  await page.evaluate(() => {
    localStorage.setItem("access_token", "invalid_token")
  })
  await page.goto("/settings")
  await page.waitForURL("/login")
  await expect(page).toHaveURL("/login")
})
