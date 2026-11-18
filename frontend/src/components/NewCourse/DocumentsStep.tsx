import {
  ArrowRight,
  Check,
  FileText,
  PenLine,
  Plus,
  Upload,
  X,
} from "lucide-react"
import { useRef, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import {
  checkFile,
  checkTypedText,
  type DraftDocument,
  MAX_DOCUMENTS,
  MAX_TEXT_CHARS,
  typedTextFile,
} from "./documents"

function documentId(): string {
  if (crypto.randomUUID) return crypto.randomUUID()
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = Array.from(bytes, (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("")
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

interface DocumentsStepProps {
  documents: DraftDocument[]
  onChange: (documents: DraftDocument[]) => void
  onContinue: () => void
}

export function DocumentsStep({
  documents,
  onChange,
  onContinue,
}: DocumentsStepProps) {
  const [rejected, setRejected] = useState<
    { id: string; name: string; error: string }[]
  >([])
  const [dragging, setDragging] = useState(false)
  const [text, setText] = useState("")
  const [error, setError] = useState<string | null>(null)
  const input = useRef<HTMLInputElement>(null)
  const full = documents.length >= MAX_DOCUMENTS
  function addFiles(files: FileList) {
    const accepted = [...documents]
    const failures: typeof rejected = []
    for (const file of Array.from(files)) {
      const message =
        accepted.length >= MAX_DOCUMENTS
          ? "Envie até 3 documentos."
          : checkFile(file)
      if (message)
        failures.push({
          id: documentId(),
          name: file.name,
          error: message,
        })
      else accepted.push({ id: documentId(), file, source: "upload" })
    }
    onChange(accepted)
    setRejected((previous) => [...previous, ...failures])
  }
  function addText() {
    const message = checkTypedText(text)
    setError(message)
    if (!message && !full) {
      onChange([
        ...documents,
        {
          id: documentId(),
          file: typedTextFile(text, documents),
          source: "typed",
        },
      ])
      setText("")
    }
  }
  return (
    <>
      <div className="flex flex-col gap-3 px-6">
        <div className="flex items-center justify-between gap-3">
          <p className="font-semibold">Seus próprios materiais</p>
          <Badge
            variant="outline"
            className="border-primary/20 bg-primary/5 px-3 py-1 text-foreground"
            aria-live="polite"
          >
            {documents.length} de {MAX_DOCUMENTS} documentos
          </Badge>
        </div>
        <Tabs defaultValue="upload">
          <TabsList className="h-11 w-full bg-muted/40 p-1 sm:w-fit">
            <TabsTrigger value="upload" className="gap-2 px-4">
              <Upload aria-hidden="true" />
              Enviar arquivo
            </TabsTrigger>
            <TabsTrigger value="typed" className="gap-2 px-4">
              <PenLine aria-hidden="true" />
              Digitar texto
            </TabsTrigger>
          </TabsList>
          <TabsContent value="upload">
            <section
              className={cn(
                "flex flex-col items-center gap-3.5 rounded-[12px] border-2 border-dashed bg-background px-6 py-5 text-center transition-colors motion-reduce:transition-none sm:flex-row sm:text-left",
                full && "opacity-60",
                !full && !dragging && "hover:border-border-strong",
                dragging && !full && "border-primary bg-primary/5",
              )}
              onDragOver={(event) => {
                event.preventDefault()
                if (!full) setDragging(true)
              }}
              onDragLeave={(event) => {
                if (
                  !event.currentTarget.contains(
                    event.relatedTarget as Node | null,
                  )
                )
                  setDragging(false)
              }}
              onDrop={(event) => {
                event.preventDefault()
                setDragging(false)
                if (!full) addFiles(event.dataTransfer.files)
              }}
              aria-label="Área de envio de arquivos"
              aria-disabled={full}
            >
              <Upload
                className="size-8 shrink-0 text-muted-foreground"
                strokeWidth={1.75}
                aria-hidden="true"
              />
              <div className="flex-1">
                <p className="font-semibold">Arraste os arquivos até aqui</p>
                <p className="text-sm text-muted-foreground">
                  MD ou PDF, até 5 MiB
                </p>
              </div>
              <Input
                ref={input}
                aria-label="Arquivos"
                type="file"
                accept=".md,.pdf"
                multiple
                className="hidden"
                disabled={full}
                onChange={(event) => {
                  if (event.target.files) addFiles(event.target.files)
                  event.target.value = ""
                }}
              />
              <Button
                variant="outline"
                className="min-h-12 bg-card px-[22px]"
                disabled={full}
                onClick={() => input.current?.click()}
              >
                Escolher arquivos
              </Button>
            </section>
          </TabsContent>
          <TabsContent
            value="typed"
            className="space-y-3 rounded-xl border bg-background/50 p-5"
          >
            <Label htmlFor="document-text">Texto do documento</Label>
            <Textarea
              id="document-text"
              className="min-h-44 resize-y bg-card leading-relaxed"
              placeholder="Cole ou escreva aqui o conteúdo que vai servir de base para o curso."
              aria-invalid={!!error}
              aria-describedby={error ? "document-text-error" : undefined}
              value={text}
              disabled={full}
              onChange={(event) => {
                setText(event.target.value)
                setError(null)
              }}
            />
            {error && (
              <p
                id="document-text-error"
                role="alert"
                className="text-sm text-destructive"
              >
                {error}
              </p>
            )}
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span className="text-xs text-foreground-tertiary">
                {text.length.toLocaleString("pt-BR")} /{" "}
                {MAX_TEXT_CHARS.toLocaleString("pt-BR")} caracteres
              </span>
              <Button disabled={full || !text} onClick={addText}>
                <Plus aria-hidden="true" />
                Adicionar texto
              </Button>
            </div>
          </TabsContent>
        </Tabs>
        {full && (
          <p
            className="flex items-center gap-2 text-sm text-muted-foreground"
            role="status"
          >
            <Check className="size-4" aria-hidden="true" />
            Limite de 3 documentos atingido.
          </p>
        )}
        <div className="flex flex-col gap-3">
          {documents.map((document) => (
            <div
              key={document.id}
              className="flex min-h-[72px] items-center gap-3 rounded-lg border bg-card px-4 py-2"
            >
              <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-foreground">
                <FileText size={20} strokeWidth={1.75} aria-hidden="true" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="break-all font-mono text-sm">
                  {document.file.name}
                </p>
                <p className="mt-1 text-xs text-foreground-tertiary">
                  {document.source === "typed"
                    ? "Texto digitado"
                    : document.file.name.toLowerCase().endsWith(".pdf")
                      ? "PDF"
                      : "Markdown"}{" "}
                  ·{" "}
                  {document.file.size < 1024 * 1024
                    ? `${Math.max(1, Math.ceil(document.file.size / 1024))} KiB`
                    : `${(document.file.size / (1024 * 1024)).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} MiB`}
                </p>
              </div>
              <Check
                className="size-4 shrink-0 text-success"
                aria-label="Documento adicionado"
              />
              <Button
                variant="ghost"
                size="icon"
                className="size-11"
                aria-label={`Remover ${document.file.name}`}
                onClick={() =>
                  onChange(documents.filter((item) => item.id !== document.id))
                }
              >
                <X size={18} strokeWidth={1.75} />
              </Button>
            </div>
          ))}
          {rejected.map((item) => (
            <div
              key={item.id}
              className="flex min-h-[72px] items-center gap-3 rounded-lg border-[1.5px] border-destructive bg-destructive-background/30 px-4 py-2"
            >
              <FileText size={20} className="text-destructive" />
              <div className="min-w-0 flex-1">
                <p className="break-all font-mono text-sm">{item.name}</p>
                <p className="text-[13px] font-semibold text-destructive">
                  {item.error}
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="size-11"
                aria-label={`Remover ${item.name}`}
                onClick={() =>
                  setRejected(rejected.filter((entry) => entry.id !== item.id))
                }
              >
                <X size={18} strokeWidth={1.75} />
              </Button>
            </div>
          ))}
        </div>
      </div>
      <div className="mt-auto flex flex-wrap items-center justify-between gap-4 border-t bg-muted/30 p-6">
        <p className="text-sm text-foreground-tertiary">
          {documents.length
            ? "Tudo pronto para definir o perfil do curso."
            : "Adicione um documento para continuar."}
        </p>
        <Button
          className="min-h-12 rounded-md bg-foreground px-7 text-background hover:bg-foreground/90 disabled:bg-muted disabled:text-foreground-tertiary"
          disabled={!documents.length}
          onClick={onContinue}
        >
          Continuar <ArrowRight aria-hidden="true" />
        </Button>
      </div>
    </>
  )
}
