import { CircleAlert, Loader2 } from "lucide-react"
import type { ContentFormat } from "@/client"
import { formatIcons } from "@/components/Course/formatIcons"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { FORMAT_LABELS } from "@/lib/courses"

interface FormatsStepProps {
  formats: ContentFormat[]
  onChange: (formats: ContentFormat[]) => void
  onBack: () => void
  onSubmit: () => void
  submitting: boolean
  error: string | null
}

const formatOptions = [
  ["tutorial", "Um guia passo a passo, com resumo e seções."],
  ["flashcards", "De 8 a 12 cartões para memorizar, com frente e verso."],
  ["quiz", "5 perguntas de múltipla escolha, com justificativa."],
] as const satisfies ReadonlyArray<readonly [ContentFormat, string]>

export function FormatsStep({
  formats,
  onChange,
  onBack,
  onSubmit,
  submitting,
  error,
}: FormatsStepProps) {
  return (
    <>
      <div className="grid gap-3 px-6">
        <p className="text-sm text-muted-foreground">
          O curso gera os formatos na ordem em que você marca.
        </p>
        {formatOptions.map(([format, description]) => {
          const position = formats.indexOf(format) + 1
          const Icon = formatIcons[format]
          return (
            <Label
              key={format}
              htmlFor={format}
              className="cursor-pointer gap-3 rounded-md border p-4 has-[[data-state=checked]]:border-info has-disabled:cursor-not-allowed"
            >
              <Checkbox
                id={format}
                checked={position > 0}
                disabled={submitting}
                aria-labelledby={`${format}-label`}
                aria-describedby={`${format}-description${position ? ` ${format}-position` : ""}`}
                onCheckedChange={(checked) =>
                  onChange(
                    checked === true
                      ? [...formats, format]
                      : formats.filter((value) => value !== format),
                  )
                }
              />
              <Icon className="size-5 shrink-0" aria-hidden="true" />
              <span className="grid flex-1 gap-1">
                <span id={`${format}-label`}>{FORMAT_LABELS[format]}</span>
                <span
                  id={`${format}-description`}
                  className="text-sm font-normal text-muted-foreground"
                >
                  {description}
                </span>
              </span>
              {position > 0 && (
                <span
                  id={`${format}-position`}
                  className="shrink-0 text-sm font-semibold text-info"
                >
                  {position}º
                </span>
              )}
            </Label>
          )
        })}
      </div>
      {error && (
        <div className="px-6">
          <Alert variant="destructive">
            <CircleAlert aria-hidden="true" />
            <AlertTitle>Não foi possível criar o curso</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      )}
      <div className="mt-auto flex flex-wrap items-center justify-between gap-4 border-t bg-muted/30 p-6">
        <Button
          variant="outline"
          className="min-h-12 px-[22px]"
          disabled={submitting}
          onClick={onBack}
        >
          Voltar
        </Button>
        <Button
          className="min-h-12 rounded-sm bg-foreground px-7 text-background hover:bg-foreground/90 disabled:bg-muted disabled:text-foreground-tertiary has-[>svg]:px-7"
          disabled={!formats.length || submitting}
          onClick={onSubmit}
        >
          {submitting && (
            <Loader2
              className="animate-spin motion-reduce:animate-none"
              aria-hidden="true"
            />
          )}
          {submitting ? "Criando curso" : "Criar curso"}
        </Button>
      </div>
    </>
  )
}
