export const MAX_DOCUMENTS = 3
export const MAX_FILE_BYTES = 5 * 1024 * 1024
export const MAX_TEXT_CHARS = 150_000
export const ACCEPTED_EXTENSIONS = [".md", ".pdf"] as const

export interface DraftDocument {
  id: string
  file: File
  source: "upload" | "typed"
}

export function checkFile(file: File): string | null {
  if (!ACCEPTED_EXTENSIONS.some((ext) => file.name.toLowerCase().endsWith(ext)))
    return "Envie um arquivo .md ou PDF, ou digite o texto."
  if (!file.size) return "O arquivo não tem texto."
  if (file.size > MAX_FILE_BYTES) return "O arquivo passa de 5 MiB."
  return null
}

export function checkTypedText(text: string): string | null {
  if (!text.trim()) return "O arquivo não tem texto."
  if (text.length > MAX_TEXT_CHARS)
    return "O documento é longo demais. Envie um documento menor ou divida o arquivo."
  return null
}

export function typedTextFile(text: string, documents: DraftDocument[]): File {
  let name = "texto-digitado.md"
  let number = 2
  while (documents.some((document) => document.file.name === name))
    name = `texto-digitado-${number++}.md`
  return new File([text], name, { type: "text/markdown" })
}
