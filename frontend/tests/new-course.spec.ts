import { expect, test } from "@playwright/test"

test.beforeEach(async ({ page }) => {
  await page.goto("/courses/new")
})

test("valida arquivos, limite e navegação", async ({ page }) => {
  const input = page.getByLabel("Arquivos")
  const next = page.getByRole("button", { name: "Continuar" })
  await expect(next).toBeDisabled()
  await input.setInputFiles([
    { name: "notas.txt", mimeType: "text/plain", buffer: Buffer.from("x") },
    { name: "vazio.md", mimeType: "text/markdown", buffer: Buffer.alloc(0) },
    {
      name: "grande.md",
      mimeType: "text/markdown",
      buffer: Buffer.alloc(5 * 1024 * 1024 + 1),
    },
  ])
  await expect(
    page.getByText("Envie um arquivo .md ou PDF, ou digite o texto."),
  ).toBeVisible()
  await expect(page.getByText("O arquivo não tem texto.")).toBeVisible()
  await expect(page.getByText("O arquivo passa de 5 MiB.")).toBeVisible()
  await input.setInputFiles([
    { name: "guia.md", mimeType: "text/markdown", buffer: Buffer.alloc(2048) },
    {
      name: "guia.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("pdf"),
    },
    {
      name: "limite.md",
      mimeType: "text/markdown",
      buffer: Buffer.alloc(5 * 1024 * 1024),
    },
    { name: "extra.md", mimeType: "text/markdown", buffer: Buffer.from("x") },
  ])
  await expect(page.getByText("Envie até 3 documentos.")).toBeVisible()
  await expect(
    page.getByRole("button", { name: "Escolher arquivos" }),
  ).toBeDisabled()
  await page.getByRole("button", { name: "Remover guia.pdf" }).click()
  await expect(
    page.getByRole("button", { name: "Escolher arquivos" }),
  ).toBeEnabled()
  await next.click()
  await expect(page.getByText("ETAPA 2 DE 3")).toBeVisible()
  await page.getByRole("button", { name: "Voltar" }).click()
  await expect(page.getByText("guia.md")).toBeVisible()
  await next.click()
  await page.getByRole("button", { name: "1 Documentos" }).click()
  await expect(page.getByText("guia.md")).toBeVisible()
})

test("adiciona textos e remove recusas", async ({ page }) => {
  await page.getByRole("tab", { name: "Digitar texto" }).click()
  const field = page.getByLabel("Texto do documento")
  await field.fill("Primeiro")
  await page.getByRole("button", { name: "Adicionar texto" }).click()
  await expect(field).toHaveValue("")
  await field.fill("Segundo")
  await page.getByRole("button", { name: "Adicionar texto" }).click()
  await expect(
    page.getByText("texto-digitado.md", { exact: true }),
  ).toBeVisible()
  await expect(page.getByText("texto-digitado-2.md")).toBeVisible()
})
