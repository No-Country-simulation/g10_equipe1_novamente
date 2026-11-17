import { FileText, Upload, X } from "lucide-react"
import { useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import {
  checkFile,
  checkTypedText,
  type DraftDocument,
  MAX_DOCUMENTS,
  typedTextFile,
} from "./documents"

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
          id: crypto.randomUUID(),
          name: file.name,
          error: message,
        })
      else accepted.push({ id: crypto.randomUUID(), file, source: "upload" })
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
          id: crypto.randomUUID(),
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
        <p className="font-semibold">Seus próprios materiais</p>
        <Tabs defaultValue="upload">
          <TabsList>
            <TabsTrigger value="upload">Enviar arquivo</TabsTrigger>
            <TabsTrigger value="typed">Digitar texto</TabsTrigger>
          </TabsList>
          <TabsContent value="upload">
            <section
              className="flex flex-wrap items-center gap-[14px] rounded-xl border-2 border-dashed border-border-strong bg-background px-6 py-5"
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault()
                if (!full) addFiles(event.dataTransfer.files)
              }}
              aria-label="Área de envio de arquivos"
              aria-disabled={full}
            >
              <Upload size={32} strokeWidth={1.75} />
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
                className="min-h-12 px-[22px]"
                disabled={full}
                onClick={() => input.current?.click()}
              >
                Escolher arquivos
              </Button>
            </section>
          </TabsContent>
          <TabsContent value="typed" className="space-y-3">
            <Label htmlFor="document-text">Texto do documento</Label>
            <Textarea
              id="document-text"
              value={text}
              disabled={full}
              onChange={(event) => setText(event.target.value)}
            />
            {error && <p className="text-destructive">{error}</p>}
            <Button disabled={full || !text} onClick={addText}>
              Adicionar texto
            </Button>
          </TabsContent>
        </Tabs>
        {full && <p>Limite de 3 documentos atingido.</p>}
        <div className="flex flex-col gap-3">
          {documents.map((document) => (
            <div
              key={document.id}
              className="flex min-h-[52px] items-center gap-3 rounded-lg border px-4"
            >
              <FileText size={20} strokeWidth={1.75} />
              <span className="flex-1 font-mono text-sm">
                {document.file.name}
              </span>
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
              className="flex min-h-[52px] items-center gap-3 rounded-lg border-[1.5px] border-destructive bg-card px-4"
            >
              <FileText size={20} className="text-destructive" />
              <div className="flex-1">
                <p className="font-mono text-sm">{item.name}</p>
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
      <div className="mt-auto flex justify-end border-t bg-muted/50 p-6">
        <Button
          className="min-h-12 rounded-md bg-foreground px-7 text-background disabled:bg-muted disabled:text-foreground-tertiary"
          disabled={!documents.length}
          onClick={onContinue}
        >
          Continuar
        </Button>
      </div>
    </>
  )
}
