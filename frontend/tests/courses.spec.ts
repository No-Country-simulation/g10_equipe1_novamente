import { expect, test } from "@playwright/test"
import type {
  AudienceLevel,
  CourseStatus,
  GenerationStatus,
} from "../src/client"
import { createCourse } from "./utils/course"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test.use({ storageState: { cookies: [], origins: [] } })
let email: string

test.beforeEach(async ({ page }) => {
  email = randomEmail()
  const password = randomPassword()
  await createUser({ email, password })
  await logInUser(page, email, password)
})

async function seed(
  title: string,
  status: CourseStatus,
  contentStatus: GenerationStatus,
  level: AudienceLevel = "non_technical",
  owner = email,
) {
  const result = await createCourse({
    owner_email: owner,
    title,
    audience_level: level,
    status,
    documents: [{}],
    contents: [
      {
        format: "tutorial",
        status: contentStatus,
        ...(contentStatus === "succeeded" ? { content: {} } : {}),
      },
    ],
  })
  if (!result) throw new Error("Falha ao criar curso")
  return result
}

test("lista vazia e criação do primeiro curso", async ({ page }) => {
  await expect(page.getByText("Você ainda não tem cursos.")).toBeVisible()
  await page.getByRole("link", { name: "Criar o primeiro curso" }).click()
  await expect(page).toHaveURL("/courses/new")
})

test("lista cursos em ordem com níveis e estados e abre o cartão", async ({
  page,
}) => {
  const a = await seed("Curso A", "ready", "succeeded", "non_technical")
  await seed("Curso B", "failed", "failed", "technical_basic")
  await seed("Curso C", "initializing", "pending", "technical_advanced")
  await page.reload()
  const cards = page.locator('a[aria-label^="Curso "]')
  await expect(cards).toHaveCount(3)
  await expect(cards.locator("h2")).toHaveText([
    "Curso C",
    "Curso B",
    "Curso A",
  ])
  await expect(cards.nth(0)).toContainText("Técnico avançado")
  await expect(cards.nth(0)).toContainText("Gerando")
  await expect(cards.nth(1)).toContainText("Técnico básico")
  await expect(cards.nth(1)).toContainText("Falhou")
  await expect(cards.nth(2)).toContainText("Não técnico")
  await expect(cards.nth(2)).toContainText("Pronto")
  await cards.nth(2).click()
  await expect(page).toHaveURL(`/courses/${a.id}`)
})

test("não mostra curso de outra pessoa", async ({ page }) => {
  const other = randomEmail()
  await createUser({ email: other, password: randomPassword() })
  await seed("Curso alheio", "ready", "succeeded", "non_technical", other)
  await page.reload()
  await expect(page.getByText("Você ainda não tem cursos.")).toBeVisible()
  await expect(page.getByText("Curso alheio")).toHaveCount(0)
})

test("atualiza enquanto há conteúdo na fila", async ({ page }) => {
  await seed("Curso C", "initializing", "pending")
  await page.reload()
  await expect(page.getByRole("link", { name: "Curso C" })).toBeVisible()
  await seed("Curso D", "ready", "succeeded")
  await expect(page.getByRole("link", { name: "Curso D" })).toBeVisible({
    timeout: 6000,
  })
})

test("não atualiza quando todos os conteúdos terminaram", async ({ page }) => {
  await seed("Curso A", "ready", "succeeded")
  let requests = 0
  page.on("request", (request) => {
    if (
      request.url().includes("/api/v1/courses/") &&
      request.method() === "GET"
    )
      requests++
  })
  await page.reload()
  await expect(page.getByRole("link", { name: "Curso A" })).toBeVisible()
  expect(requests).toBe(1)
  await page.waitForTimeout(5000)
  expect(requests).toBe(1)
})

test("permite tentar novamente após erro", async ({ page }) => {
  await seed("Curso A", "ready", "succeeded")
  const pattern = "**/api/v1/courses/"
  await page.route(pattern, (route) => route.fulfill({ status: 500 }))
  await page.reload()
  await expect(
    page.getByText("Não foi possível carregar os cursos."),
  ).toBeVisible({ timeout: 15000 })
  await page.unroute(pattern)
  await page.getByRole("button", { name: "Tentar novamente" }).click()
  await expect(page.getByRole("link", { name: "Curso A" })).toBeVisible()
})

test("login e raiz levam à lista, com Home ativa", async ({ page }) => {
  await expect(page).toHaveURL("/courses")
  await expect(
    page
      .getByRole("navigation", { name: "Principal" })
      .getByRole("link", { name: "Home" }),
  ).toHaveAttribute("aria-current", "page")
  await page.goto("/")
  await expect(page).toHaveURL("/courses")
})

test("botão Novo curso abre o formulário", async ({ page }) => {
  await page.getByRole("link", { name: "Novo curso" }).last().click()
  await expect(page).toHaveURL("/courses/new")
})

test("não mostra cursos da conta anterior após trocar de usuário", async ({
  page,
}) => {
  await seed("Curso privado de A", "ready", "succeeded")
  await page.reload()
  await expect(
    page.getByRole("link", { name: "Curso privado de A" }),
  ).toBeVisible()
  const other = randomEmail()
  const password = randomPassword()
  await createUser({ email: other, password })
  await seed("Curso de B", "ready", "succeeded", "non_technical", other)
  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Sair" }).click()
  await page.waitForURL("/login")
  let release!: () => void
  const gate = new Promise<void>((resolve) => {
    release = resolve
  })
  let requested!: () => void
  const requestStarted = new Promise<void>((resolve) => {
    requested = resolve
  })
  await page.route("**/api/v1/courses/", async (route) => {
    requested()
    await gate
    await route.continue()
  })
  await page.evaluate(() => {
    const seen = { value: false }
    Object.assign(window, { previousCourseSeen: seen })
    new MutationObserver(() => {
      if (document.body.textContent?.includes("Curso privado de A"))
        seen.value = true
    }).observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
    })
  })
  await page.getByTestId("email-input").fill(other)
  await page.getByTestId("password-input").fill(password)
  await page.getByRole("button", { name: "Entrar" }).click()
  await page.waitForURL("/courses")
  await requestStarted
  await expect(
    page.getByRole("link", { name: "Curso privado de A" }),
  ).toHaveCount(0)
  release()
  await expect(page.getByRole("link", { name: "Curso de B" })).toBeVisible()
  expect(
    await page.evaluate(
      () =>
        (window as unknown as { previousCourseSeen: { value: boolean } })
          .previousCourseSeen.value,
    ),
  ).toBe(false)
})

test("permite tentar novamente quando a identidade não carrega", async ({
  page,
}) => {
  await page.route("**/api/v1/users/me", (route) =>
    route.fulfill({ status: 500 }),
  )
  await page.reload()
  await expect(
    page.getByText("Não foi possível carregar os cursos."),
  ).toBeVisible()
  await page.unroute("**/api/v1/users/me")
  await page.getByRole("button", { name: "Tentar novamente" }).click()
  await expect(page.getByText("Você ainda não tem cursos.")).toBeVisible()
})
