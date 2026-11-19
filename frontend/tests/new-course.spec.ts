import { expect, type Page, test } from "@playwright/test"
import { createCourse } from "./utils/course"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

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

const titleInput = (page: Page) =>
  page.getByRole("textbox", { name: "Título do curso" })
const nicheSelect = (page: Page) =>
  page.getByRole("combobox", { name: "Setor" })
const basicAudience = (page: Page) =>
  page.getByRole("radio", { name: "Técnico básico" })
const formatCheckbox = (page: Page, name: string) =>
  page.getByRole("checkbox", { name, exact: true })
const back = (page: Page) => page.getByRole("button", { name: "Voltar" })
const submit = (page: Page) =>
  page.getByRole("button", { name: "Criar curso", exact: true })
const coursesEndpoint = "**/api/v1/courses/"
const storageError =
  "O armazenamento de arquivos não está disponível. Tente novamente mais tarde."

async function openProfile(page: Page, filename = "guia.md") {
  await input(page).setInputFiles(file(filename))
  await next(page).click()
}

async function chooseNiche(page: Page, name = "Fintech") {
  await nicheSelect(page).click()
  await page.getByRole("option", { name }).click()
}

async function fillProfile(page: Page, title = "Curso de teste") {
  await titleInput(page).fill(title)
  await chooseNiche(page)
  await basicAudience(page).check()
}

async function openFormats(page: Page, filename?: string) {
  await openProfile(page, filename)
  await fillProfile(page)
  await next(page).click()
}

test("mostra os campos do perfil e lista os setores da API", async ({
  page,
}) => {
  await openProfile(page)
  await expect(page.getByText("ETAPA 2 DE 3")).toBeVisible()
  await expect(titleInput(page)).toHaveValue("")
  await expect(
    page.getByRole("radiogroup", { name: "Nível de público" }),
  ).toBeVisible()
  await expect(next(page)).toBeDisabled()
  await nicheSelect(page).click()
  await expect(page.getByRole("option")).toHaveText([
    "Fintech",
    "Saúde",
    "E-commerce",
    "Geral",
  ])
})

test("confere título no blur e no clique e conta caracteres Unicode", async ({
  page,
}) => {
  await openProfile(page)
  const title = titleInput(page)
  await title.fill("   ")
  await title.press("Tab")
  const required = page.getByText("Informe um título.")
  await expect(required).toBeVisible()
  await expect(title).toHaveAttribute("aria-invalid", "true")
  await expect(title).toHaveAccessibleDescription("Informe um título.")
  await chooseNiche(page)
  await basicAudience(page).check()
  await next(page).click()
  await expect(page.getByText("ETAPA 2 DE 3")).toBeVisible()
  await expect(required).toBeVisible()
  await title.fill("📘".repeat(256))
  const tooLong = page.getByText("O título passa de 255 caracteres.")
  await expect(tooLong).toBeVisible()
  await title.fill(`  ${"📘".repeat(255)}  `)
  await expect(tooLong).toBeHidden()
  await expect(title).toHaveAttribute("aria-invalid", "false")
  await next(page).click()
  await expect(page.getByText("ETAPA 3 DE 3")).toBeVisible()
})

test("marca Formatos como etapa ativa e Documentos e Perfil como concluídas", async ({
  page,
}) => {
  await openFormats(page)
  await expect(steps(page).nth(2)).toHaveAttribute("aria-current", "step")
  await expect(
    steps(page)
      .first()
      .getByRole("button", { name: /Documentos/ }),
  ).toBeVisible()
  await expect(
    steps(page)
      .nth(1)
      .getByRole("button", { name: /Perfil/ }),
  ).toBeVisible()
})

test("mostra a ordem da escolha e atualiza as posições ao desmarcar", async ({
  page,
}) => {
  await openFormats(page)
  await expect(submit(page)).toBeDisabled()
  const quiz = formatCheckbox(page, "Quiz")
  const tutorial = formatCheckbox(page, "Tutorial")
  const flashcards = formatCheckbox(page, "Flashcards")
  await quiz.check()
  await tutorial.check()
  await flashcards.check()
  await expect(quiz).toHaveAccessibleDescription(/1º$/)
  await expect(tutorial).toHaveAccessibleDescription(/2º$/)
  await expect(flashcards).toHaveAccessibleDescription(/3º$/)
  await expect(page.getByText("3º", { exact: true })).toBeVisible()
  await quiz.uncheck()
  await expect(tutorial).toHaveAccessibleDescription(/1º$/)
  await expect(flashcards).toHaveAccessibleDescription(/2º$/)
  await expect(page.getByText("3º", { exact: true })).toBeHidden()
  await expect(submit(page)).toBeEnabled()
})

test("mantém documentos, perfil e formatos ao voltar", async ({ page }) => {
  await openFormats(page)
  await formatCheckbox(page, "Flashcards").check()
  await back(page).click()
  await expect(titleInput(page)).toHaveValue("Curso de teste")
  await expect(nicheSelect(page)).toHaveText("Fintech")
  await expect(basicAudience(page)).toBeChecked()
  await next(page).click()
  await expect(formatCheckbox(page, "Flashcards")).toBeChecked()
  await steps(page)
    .first()
    .getByRole("button", { name: /Documentos/ })
    .click()
  await expect(page.getByText("guia.md")).toBeVisible()
})

test.describe("envio bem-sucedido", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("envia um multipart em ordem e abre o curso criado", async ({
    page,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    const course = await createCourse({
      owner_email: email,
      title: "Curso de teste",
      niche_slug: "fintech",
      audience_level: "technical_basic",
      status: "initializing",
      documents: [
        { original_filename: "guia.md", status: "uploaded" },
        { original_filename: "texto-digitado.md", status: "uploaded" },
      ],
      contents: [
        { format: "quiz", status: "pending" },
        { format: "tutorial", status: "pending" },
      ],
    })
    await logInUser(page, email, password)
    await page.goto("/courses/new")

    const requests: FormData[] = []
    await page.route(coursesEndpoint, async (route) => {
      const request = route.request()
      if (request.method() !== "POST") return route.fallback()
      const body = request.postDataBuffer()
      const contentType = request.headers()["content-type"]
      expect(body).not.toBeNull()
      expect(contentType).toMatch(/^multipart\/form-data;\s*boundary=/i)
      const multipart = await new Response(new Uint8Array(body!), {
        headers: { "Content-Type": contentType },
      }).formData()
      requests.push(multipart)
      await route.fulfill({ status: 201, json: course })
    })

    await input(page).setInputFiles(file("guia.md"))
    await page.getByRole("tab", { name: "Digitar texto" }).click()
    await page
      .getByLabel("Texto do documento")
      .fill("Uma segunda fonte para o curso.")
    await page.getByRole("button", { name: "Adicionar texto" }).click()
    await next(page).click()
    await fillProfile(page, `  ${course.title}  `)
    await next(page).click()
    await formatCheckbox(page, "Quiz").check()
    await formatCheckbox(page, "Tutorial").check()
    await submit(page).click()

    await expect(page).toHaveURL(`/courses/${course.id}`)
    await expect(
      page.getByRole("heading", { name: course.title, level: 1 }),
    ).toBeVisible()
    await expect(page.getByText("Na fila", { exact: true })).toHaveCount(2)
    expect(requests).toHaveLength(1)
    const [multipart] = requests
    expect(multipart.getAll("title")).toEqual([course.title])
    expect(multipart.getAll("niche_id")).toEqual([String(course.niche.id)])
    expect(multipart.getAll("audience_level")).toEqual([course.audience_level])
    expect(multipart.getAll("formats")).toEqual(["quiz", "tutorial"])
    expect(
      multipart
        .getAll("files")
        .map((entry) => (typeof entry === "string" ? entry : entry.name)),
    ).toEqual(["guia.md", "texto-digitado.md"])
  })
})

test("mostra o erro de armazenamento e mantém o formato marcado", async ({
  page,
}) => {
  await openFormats(page)
  await page.route(coursesEndpoint, (route) =>
    route.fulfill({ status: 503, json: { detail: storageError } }),
  )
  await formatCheckbox(page, "Tutorial").check()
  await submit(page).click()
  const alert = page.getByRole("alert")
  await expect(alert).toContainText("Não foi possível criar o curso")
  await expect(alert).toContainText(storageError)
  await expect(page.getByText("ETAPA 3 DE 3")).toBeVisible()
  await expect(formatCheckbox(page, "Tutorial")).toBeChecked()
})

test("bloqueia outro envio e o retorno enquanto o POST está em andamento", async ({
  page,
}) => {
  await openFormats(page)
  let requests = 0
  let release!: () => void
  const held = new Promise<void>((resolve) => {
    release = resolve
  })
  await page.route(coursesEndpoint, async (route) => {
    requests += 1
    await held
    await route.fulfill({ status: 503, json: { detail: storageError } })
  })
  await formatCheckbox(page, "Tutorial").check()
  const sending = page.getByRole("button", { name: "Criando curso" })
  try {
    await submit(page).dblclick()
    await expect(sending).toBeDisabled()
    await expect(back(page)).toBeDisabled()
    for (const name of ["Tutorial", "Flashcards", "Quiz"]) {
      await expect(formatCheckbox(page, name)).toBeDisabled()
    }
    await expect(steps(page).getByRole("button")).toHaveCount(0)
    await expect.poll(() => requests).toBe(1)
  } finally {
    release()
  }
  await expect(page.getByRole("alert")).toContainText(storageError)
  expect(requests).toBe(1)
})

test("mostra a mensagem da API real para um PDF inválido", async ({ page }) => {
  await openFormats(page, "guia.pdf")
  await formatCheckbox(page, "Tutorial").check()
  const response = page.waitForResponse(
    (result) =>
      result.url().endsWith("/api/v1/courses/") &&
      result.request().method() === "POST",
  )
  await submit(page).click()
  expect((await response).status()).toBe(422)
  await expect(page.getByRole("alert")).toContainText(
    "guia.pdf: Não foi possível abrir o PDF. Envie um PDF sem senha.",
  )
  await expect(page.getByText("ETAPA 3 DE 3")).toBeVisible()
})

test("refaz a consulta de setores depois de uma falha", async ({ page }) => {
  await page.route("**/api/v1/niches/", (route) => route.abort(), { times: 1 })
  await openProfile(page)
  await titleInput(page).fill("Curso de teste")
  await basicAudience(page).check()
  await expect(
    page.getByText("Não foi possível carregar os setores."),
  ).toBeVisible()
  await expect(nicheSelect(page)).toBeDisabled()
  await expect(next(page)).toBeDisabled()
  await page.getByRole("button", { name: "Tentar novamente" }).click()
  await chooseNiche(page)
  await expect(next(page)).toBeEnabled()
})

test("mostra mensagens para validação em lista e falha de conexão", async ({
  page,
}) => {
  await openFormats(page)
  const tutorial = formatCheckbox(page, "Tutorial")
  const alert = page.getByRole("alert")
  await tutorial.check()
  await page.route(coursesEndpoint, (route) => route.abort(), { times: 1 })
  await page.route(
    coursesEndpoint,
    (route) =>
      route.fulfill({
        status: 422,
        json: { detail: [{ msg: "Invalid input" }] },
      }),
    { times: 1 },
  )

  for (const message of [
    "Verifique os dados informados e tente novamente.",
    "Não foi possível falar com o servidor. Tente novamente.",
  ]) {
    await submit(page).click()
    await expect(alert).toContainText(message)
    await back(page).click()
    await expect(titleInput(page)).toHaveValue("Curso de teste")
    await expect(nicheSelect(page)).toHaveText("Fintech")
    await expect(basicAudience(page)).toBeChecked()
    await next(page).click()
    await expect(tutorial).toBeChecked()
    await expect(alert).toBeHidden()
  }
})
