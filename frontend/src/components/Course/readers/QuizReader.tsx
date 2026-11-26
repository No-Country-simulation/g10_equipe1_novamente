import { Check, ChevronLeft, CircleCheck, CircleX, X } from "lucide-react"
import { useLayoutEffect, useRef, useState } from "react"
import { z } from "zod"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { ReaderProps } from "./types"

const text = z.string().trim().min(1)
const questionSchema = z.object({
  prompt: text,
  options: z
    .array(text)
    .length(4)
    .refine((options) => new Set(options).size === options.length),
  correct_index: z.int().min(0).max(3),
  explanation: text,
})
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
  const [answers, setAnswers] = useState<Partial<Record<number, number>>>({})
  const navigationRef = useRef<HTMLButtonElement>(null)
  const {
    prompt,
    options,
    correct_index: correctIndex,
    explanation,
  } = questions[index]
  const answer = answers[index]
  const isAnswered = answer !== undefined
  const isAnswerCorrect = answer === correctIndex
  const ResultIcon = isAnswerCorrect ? CircleCheck : CircleX
  const resultTitle = isAnswerCorrect ? "Resposta correta" : "Não foi dessa vez"
  const correctOption = options[correctIndex]
  const correctSentence = isAnswerCorrect
    ? ""
    : `A resposta certa é ${optionLetters[correctIndex]}: ${correctOption}${/[.!?]$/.test(correctOption) ? "" : "."}`
  const position = index + 1
  const total = questions.length

  useLayoutEffect(() => {
    if (Object.keys(answers).length > 0) {
      navigationRef.current?.focus()
    }
  }, [answers])

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
          {options.map((option, optionIndex) => {
            const isSelected = optionIndex === answer
            const isCorrect = isAnswered && optionIndex === correctIndex
            const isIncorrect = isSelected && !isCorrect
            const label = isCorrect
              ? isSelected
                ? "Sua resposta · correta"
                : "Resposta correta"
              : isIncorrect
                ? "Sua resposta · incorreta"
                : null

            return (
              <Button
                key={option}
                type="button"
                variant="outline"
                disabled={isAnswered}
                onClick={() =>
                  setAnswers((current) => ({
                    ...current,
                    [index]: optionIndex,
                  }))
                }
                className={cn(
                  "h-auto min-h-16 w-full justify-start gap-4 rounded-md border-border-strong p-4 text-left text-lg font-normal whitespace-normal disabled:opacity-100",
                  isCorrect &&
                    "border-2 border-success-foreground bg-success-background font-semibold text-success-foreground dark:border-success-foreground dark:bg-success-background",
                  isIncorrect &&
                    "border-2 border-destructive bg-destructive-background font-semibold text-destructive-foreground dark:border-destructive dark:bg-destructive-background",
                  isAnswered &&
                    !label &&
                    "border-border bg-background text-foreground-tertiary dark:border-border dark:bg-background",
                )}
              >
                <span
                  className={cn(
                    "grid size-8 shrink-0 place-items-center rounded-[6px] border bg-muted/50 text-sm font-semibold",
                    isAnswered && "bg-card",
                    isCorrect && "border-0 bg-success-foreground text-card",
                    isIncorrect && "border-0 bg-destructive text-card",
                  )}
                >
                  {isCorrect ? (
                    <Check aria-hidden="true" className="size-[18px]" />
                  ) : isIncorrect ? (
                    <X aria-hidden="true" className="size-[18px]" />
                  ) : (
                    optionLetters[optionIndex]
                  )}
                </span>{" "}
                <span className="grid min-w-0 flex-1 items-center gap-x-4 gap-y-1 wrap-anywhere sm:grid-cols-[minmax(0,1fr)_auto]">
                  <span>{option}</span>
                  {label && (
                    <span className="text-sm font-semibold sm:text-right">
                      {label}
                    </span>
                  )}
                </span>
              </Button>
            )
          })}
        </fieldset>
        <p role="status" aria-atomic="true" className="sr-only">
          {isAnswered &&
            [`${resultTitle}.`, correctSentence, explanation]
              .filter(Boolean)
              .join(" ")}
        </p>
        {isAnswered && (
          <div
            aria-hidden="true"
            data-testid="quiz-result"
            className={cn(
              "mt-5 space-y-2.5 rounded-md border border-l-[6px] bg-card p-5 wrap-anywhere",
              isAnswerCorrect
                ? "border-success-foreground"
                : "border-destructive",
            )}
          >
            <p
              className={cn(
                "flex items-center gap-2 font-heading text-lg font-bold",
                isAnswerCorrect
                  ? "text-success-foreground"
                  : "text-destructive",
              )}
            >
              <ResultIcon aria-hidden="true" className="size-5 shrink-0" />
              {resultTitle}
            </p>
            {correctSentence && (
              <p className="text-[15px]/[1.6] font-semibold text-muted-foreground">
                {correctSentence}
              </p>
            )}
            <p className="text-base/[1.6] text-foreground">{explanation}</p>
          </div>
        )}
      </div>
      <nav
        aria-label="Navegação do quiz"
        className="flex flex-wrap justify-between gap-3 border-t bg-muted/50 p-6 [@media(max-width:360px)]:flex-col"
      >
        <Button
          ref={position === total ? navigationRef : undefined}
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
            ref={navigationRef}
            type="button"
            disabled={!isAnswered}
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
