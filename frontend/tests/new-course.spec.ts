import { expect, type Page, test } from "@playwright/test"

const file = (name: string, size = 1) => ({
  name,
  mimeType: "application/octet-stream",
  buffer: Buffer.alloc(size, 65),
})
const input = (page: Page) => page.getByLabel("Arquivos", { exact: true })
const next = (page: Page) => page.getByRole("button", { name: "Continuar" })
const remove = (page: Page, name: string) =>
  page.getByRole("button", { name: `Remover ${name}` })
const steps = (page: Page) =>
  page.getByRole("list", { name: "Etapas" }).getByRole("listitem")

test.beforeEach(async ({ page }) => {
  await page.goto("/courses/new")
})

test("1. mostra os controles iniciais", async ({ page }) => {
  await expect(page.getByText("Seus próprios materiais")).toBeVisible()
  await expect(
    page.getByRole("tab", { name: "Enviar arquivo" }),
  ).toHaveAttribute("aria-selected", "true")
  await expect(page.getByRole("tab", { name: "Digitar texto" })).toBeVisible()
  await expect(page.getByText("Arraste os arquivos até aqui")).toBeVisible()
  await expect(
    page.getByRole("button", { name: "Escolher arquivos" }),
  ).toBeEnabled()
  await expect(next(page)).toBeDisabled()
})

test("2. aceita Markdown e habilita continuar", async ({ page }) => {
  await input(page).setInputFiles(file("guia.md", 2048))
  await expect(page.getByText("guia.md")).toBeVisible()
  await expect(remove(page, "guia.md")).toBeVisible()
  await expect(next(page)).toBeEnabled()
})

test("3. aceita PDF", async ({ page }) => {
  await input(page).setInputFiles(file("guia.pdf"))
  await expect(page.getByText("guia.pdf")).toBeVisible()
  await expect(next(page)).toBeEnabled()
})

test("4. recusa outro tipo e mantém continuar desabilitado", async ({
  page,
}) => {
  await input(page).setInputFiles(file("notas.txt"))
  await expect(page.getByText("notas.txt")).toBeVisible()
  await expect(
    page.getByText("Envie um arquivo .md ou PDF, ou digite o texto."),
  ).toBeVisible()
  await expect(next(page)).toBeDisabled()
})

test("5. recusa arquivo vazio", async ({ page }) => {
  await input(page).setInputFiles(file("vazio.md", 0))
  await expect(page.getByText("vazio.md")).toBeVisible()
  await expect(page.getByText("O arquivo não tem texto.")).toBeVisible()
  await expect(next(page)).toBeDisabled()
})

test("6. aplica limite de 5 MiB", async ({ page }) => {
  await input(page).setInputFiles([
    file("grande.md", 5 * 1024 * 1024 + 1),
    file("limite.md", 5 * 1024 * 1024),
  ])
  await expect(page.getByText("O arquivo passa de 5 MiB.")).toBeVisible()
  await expect(page.getByText("limite.md")).toBeVisible()
  await expect(next(page)).toBeEnabled()
  await remove(page, "grande.md").click()
  await expect(page.getByText("O arquivo passa de 5 MiB.")).toHaveCount(0)
  await expect(page.getByText("limite.md")).toBeVisible()
})

test("7. remove apenas a linha recusada", async ({ page }) => {
  await input(page).setInputFiles([file("guia.md"), file("notas.txt")])
  await expect(next(page)).toBeEnabled()
  await expect(
    page.getByText("Envie um arquivo .md ou PDF, ou digite o texto."),
  ).toBeVisible()
  await remove(page, "notas.txt").click()
  await expect(page.getByText("notas.txt")).toHaveCount(0)
  await expect(
    page.getByText("Envie um arquivo .md ou PDF, ou digite o texto."),
  ).toHaveCount(0)
  await expect(page.getByText("guia.md")).toBeVisible()
  await expect(next(page)).toBeEnabled()
})

test("8. adiciona dois textos com nomes distintos", async ({ page }) => {
  await page.getByRole("tab", { name: "Digitar texto" }).click()
  const text = page.getByLabel("Texto do documento")
  const add = page.getByRole("button", { name: "Adicionar texto" })
  await expect(add).toBeDisabled()
  await text.fill("Primeiro")
  await add.click()
  await expect(text).toHaveValue("")
  await expect(
    page.getByText("texto-digitado.md", { exact: true }),
  ).toBeVisible()
  await text.fill("Segundo")
  await add.click()
  await expect(text).toHaveValue("")
  await expect(page.getByText("texto-digitado-2.md")).toBeVisible()
})

test("9. limita documentos e desabilita os controles", async ({ page }) => {
  await input(page).setInputFiles([
    file("um.md"),
    file("dois.md"),
    file("tres.pdf"),
    file("quatro.md"),
  ])
  for (const name of ["um.md", "dois.md", "tres.pdf", "quatro.md"])
    await expect(page.getByText(name)).toBeVisible()
  await expect(page.getByText("Envie até 3 documentos.")).toBeVisible()
  await expect(page.getByText("Limite de 3 documentos atingido.")).toBeVisible()
  await expect(
    page.getByRole("button", { name: "Escolher arquivos" }),
  ).toBeDisabled()
  await expect(
    page.getByRole("region", { name: "Área de envio de arquivos" }),
  ).toHaveAttribute("aria-disabled", "true")
  await page.getByRole("tab", { name: "Digitar texto" }).click()
  await expect(page.getByLabel("Texto do documento")).toBeDisabled()
  await expect(
    page.getByRole("button", { name: "Adicionar texto" }),
  ).toBeDisabled()
})

test("10. remover documento libera os controles", async ({ page }) => {
  await input(page).setInputFiles([
    file("um.md"),
    file("dois.md"),
    file("tres.md"),
  ])
  await remove(page, "um.md").click()
  await expect(page.getByText("um.md")).toHaveCount(0)
  await expect(
    page.getByRole("button", { name: "Escolher arquivos" }),
  ).toBeEnabled()
  await page.getByRole("tab", { name: "Digitar texto" }).click()
  const text = page.getByLabel("Texto do documento")
  await expect(text).toBeEnabled()
  await text.fill("texto")
  await expect(
    page.getByRole("button", { name: "Adicionar texto" }),
  ).toBeEnabled()
})

test("11. voltar preserva documentos e atualiza etapa", async ({ page }) => {
  await input(page).setInputFiles(file("guia.md"))
  await next(page).click()
  await expect(page.getByText("ETAPA 2 DE 3")).toBeVisible()
  await expect(page.locator('[data-slot="card-title"]')).toHaveText("Perfil")
  await expect(steps(page).nth(1)).toHaveAttribute("aria-current", "step")
  await page.getByRole("button", { name: "Voltar" }).click()
  await expect(page.getByText("ETAPA 1 DE 3")).toBeVisible()
  await expect(page.getByText("guia.md")).toBeVisible()
  await expect(steps(page).first()).toHaveAttribute("aria-current", "step")
})

test("12. etapa concluída navega e futura não é botão", async ({ page }) => {
  await expect(steps(page).nth(1).getByRole("button")).toHaveCount(0)
  await steps(page).nth(1).click()
  await expect(page.getByText("ETAPA 1 DE 3")).toBeVisible()
  await input(page).setInputFiles(file("guia.md"))
  await next(page).click()
  await steps(page)
    .first()
    .getByRole("button", { name: /Documentos/ })
    .click()
  await expect(page.getByText("ETAPA 1 DE 3")).toBeVisible()
  await expect(page.getByText("guia.md")).toBeVisible()
})

test("13. aceita arquivo solto na área de envio", async ({ page }) => {
  const transfer = await page.evaluateHandle(() => {
    const data = new DataTransfer()
    data.items.add(new File(["conteúdo"], "guia.md", { type: "text/markdown" }))
    return data
  })
  const area = page.getByRole("region", { name: "Área de envio de arquivos" })
  await area.dispatchEvent("dragover", { dataTransfer: transfer })
  await area.dispatchEvent("drop", { dataTransfer: transfer })
  await expect(page.getByText("guia.md")).toBeVisible()
  await expect(next(page)).toBeEnabled()
  await transfer.dispose()
})
