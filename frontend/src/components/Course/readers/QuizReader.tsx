import { ChevronLeft } from "lucide-react"
import { useState } from "react"
import { z } from "zod"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import type { ReaderProps } from "./types"

const text = z.string().trim().min(1)
const questionSchema = z
  .object({
    prompt: text,
    options: z
      .array(text)
      .length(4)
      .refine((options) => new Set(options).size === options.length),
    correct_index: z.int().min(0).max(3),
    explanation: text,
  })
  .transform(({ prompt, options, explanation }) => ({
    prompt,
    options,
    explanation,
  }))
const quizSchema = z.object({ questions: z.array(questionSchema).length(5) })
const optionLetters = ["A", "B", "C", "D"]

export function QuizReader({ content }: ReaderProps) {
  const quiz = quizSchema.safeParse(content)
  if (!quiz.success) {
    return (
      <Alert>
        <AlertDescription>
          Não foi possível mostrar este conteúdo, porque ele não está no formato
          esperado.
        </AlertDescription>
      </Alert>
    )
  }

  return <Quiz key={JSON.stringify(quiz.data.questions)} {...quiz.data} />
}

function Quiz({ questions }: z.infer<typeof quizSchema>) {
  const [index, setIndex] = useState(0)
  const [revealed, setRevealed] = useState(() => new Set<number>())
  const { prompt, options, explanation } = questions[index]
  const isRevealed = revealed.has(index)
  const position = index + 1
  const total = questions.length

  return (
    <Card className="mx-auto w-full max-w-[900px] gap-0 overflow-hidden rounded-[12px] py-0">
      <div className="p-6">
        <p className="mb-2 text-xs font-semibold tracking-[0.08em] text-foreground-tertiary">
          PERGUNTA {position} DE {total}
        </p>
        <div
          role="progressbar"
          aria-label="Posição no quiz"
          aria-valuemin={1}
          aria-valuemax={total}
          aria-valuenow={position}
          aria-valuetext={`Pergunta ${position} de ${total}`}
          className="h-1 overflow-hidden rounded-full bg-muted"
        >
          <div
            className="h-full bg-foreground"
            style={{ width: `${(position / total) * 100}%` }}
          />
        </div>
        <h3 className="my-6 wrap-anywhere font-heading text-[28px]/[1.25] font-bold">
          {prompt}
        </h3>
        <fieldset
          aria-label="Opções de resposta"
          className="grid min-w-0 gap-3"
        >
          {options.map((option, optionIndex) => (
            <Button
              key={option}
              type="button"
              variant="outline"
              disabled={isRevealed}
              onClick={() =>
                setRevealed((current) => new Set(current).add(index))
              }
              className="h-auto min-h-16 w-full justify-start gap-4 rounded-lg border-border-strong p-4 text-left text-lg font-normal whitespace-normal"
            >
              <span className="grid size-8 shrink-0 place-items-center rounded-[6px] border bg-muted/50 text-sm font-semibold">
                {optionLetters[optionIndex]}
              </span>{" "}
              <span className="wrap-anywhere">{option}</span>
            </Button>
          ))}
        </fieldset>
        <div role="status">
          {isRevealed && (
            <div className="mt-6 space-y-1 wrap-anywhere text-base/6">
              <p className="font-semibold">Justificativa</p>
              <p>{explanation}</p>
            </div>
          )}
        </div>
      </div>
      <nav
        aria-label="Navegação do quiz"
        className="flex flex-wrap justify-between gap-3 border-t bg-muted/50 p-6 [@media(max-width:360px)]:flex-col"
      >
        <Button
          type="button"
          variant="outline"
          disabled={position === 1}
          onClick={() => setIndex(index - 1)}
          className="min-h-12 border-border-strong"
        >
          <ChevronLeft aria-hidden="true" />
          Pergunta anterior
        </Button>
        {position < total && (
          <Button
            type="button"
            disabled={!isRevealed}
            onClick={() => setIndex(index + 1)}
            className="min-h-12 bg-foreground px-7 text-background hover:bg-foreground/90 disabled:bg-muted disabled:text-foreground-tertiary"
          >
            Próxima pergunta
          </Button>
        )}
      </nav>
    </Card>
  )
}
