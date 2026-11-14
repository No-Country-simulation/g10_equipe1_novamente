import { expect, test } from "@playwright/test"

test("Home tab is active after login", async ({ page }) => {
  await page.goto("/")
  const nav = page.getByRole("navigation", { name: "Principal" })

  await expect(nav.getByRole("link", { name: "Home" })).toHaveAttribute(
    "aria-current",
    "page",
  )
  await expect(
    nav.getByRole("link", { name: "Novo curso" }),
  ).not.toHaveAttribute("aria-current", "page")
})

test("Novo curso tab opens /courses/new and becomes active", async ({
  page,
}) => {
  await page.goto("/")
  const nav = page.getByRole("navigation", { name: "Principal" })

  await nav.getByRole("link", { name: "Novo curso" }).click()

  await page.waitForURL("/courses/new")
  await expect(nav.getByRole("link", { name: "Novo curso" })).toHaveAttribute(
    "aria-current",
    "page",
  )
  await expect(nav.getByRole("link", { name: "Home" })).not.toHaveAttribute(
    "aria-current",
    "page",
  )
})

test("New course page shows the title, the steps and the step card", async ({
  page,
}) => {
  await page.goto("/courses/new")

  await expect(
    page.getByRole("heading", { name: "Novo curso", level: 1 }),
  ).toBeVisible()
  const steps = page.getByRole("list", { name: "Etapas" }).getByRole("listitem")
  await expect(steps).toHaveText(["1Documentos", "2Perfil", "3Formatos"])
  await expect(steps.first()).toHaveAttribute("aria-current", "step")
  await expect(page.getByText("ETAPA 1 DE 3")).toBeVisible()
  await expect(
    page.getByRole("heading", { name: "Documentos", level: 2 }),
  ).toBeVisible()
})

test.describe("Without login", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("New course page redirects to /login", async ({ page }) => {
    await page.goto("/courses/new")
    await page.waitForURL("/login")
  })
})

test("No tab is active on /settings", async ({ page }) => {
  await page.goto("/settings")
  const nav = page.getByRole("navigation", { name: "Principal" })

  await expect(nav.getByRole("link")).toHaveCount(2)
  await expect(nav.locator('[aria-current="page"]')).toHaveCount(0)
})
