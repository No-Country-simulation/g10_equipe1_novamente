import { Lightbulb, RefreshCw } from "lucide-react"
import { useCallback, useId, useState } from "react"
import { z } from "zod"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { ReaderProps } from "./types"

const text = z.string().trim().min(1)
const flashcardsSchema = z.object({
  introduction: text,
  cards: z
    .array(
      z.object({
        front: text,
        back: text,
        hint: text.nullable().default(null),
      }),
    )
    .min(8)
    .max(12),
})

export function FlashcardsReader({ content }: ReaderProps) {
  const parsed = flashcardsSchema.safeParse(content)
  if (!parsed.success) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Não foi possível mostrar este conteúdo, porque ele não está no formato
          esperado.
        </AlertDescription>
      </Alert>
    )
  }

  // A consulta periódica preserva o estado enquanto o conteúdo validado for igual.
  return <FlashcardSet key={JSON.stringify(parsed.data)} {...parsed.data} />
}

function FlashcardSet({
  introduction,
  cards,
}: z.infer<typeof flashcardsSchema>) {
  const [index, setIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [showHint, setShowHint] = useState(false)
  const cardTextId = useId()
  const focusHint = useCallback((element: HTMLParagraphElement | null) => {
    element?.focus()
  }, [])

  const card = cards[index]
  const position = index + 1
  const side = flipped ? "Resposta" : "Pergunta"
  const cardText = flipped ? card.back : card.front

  function moveTo(index: number) {
    setIndex(index)
    setFlipped(false)
    setShowHint(false)
  }

  return (
    <div className="mx-auto max-w-[900px]">
      <p className="mb-6 wrap-anywhere text-base/6 text-muted-foreground">
        {introduction}
      </p>
      <Card className="gap-0 overflow-hidden rounded-[12px] p-0">
        <CardContent className="p-6">
          <p className="text-xs font-semibold tracking-[0.08em] text-foreground-tertiary">
            CARTÃO {position} DE {cards.length}
          </p>
          <div
            role="progressbar"
            aria-label="Posição no conjunto"
            aria-valuemin={1}
            aria-valuemax={cards.length}
            aria-valuenow={position}
            aria-valuetext={`Cartão ${position} de ${cards.length}`}
            className="mt-2 mb-6 h-1 overflow-hidden rounded-full bg-muted"
          >
            <div
              className="h-full bg-foreground"
              style={{ width: `${(position / cards.length) * 100}%` }}
            />
          </div>
          <Button
            type="button"
            variant="outline"
            aria-label="Virar cartão"
            aria-describedby={cardTextId}
            aria-pressed={flipped}
            onClick={() => {
              setFlipped(!flipped)
              setShowHint(false)
            }}
            className="h-auto min-h-[280px] w-full flex-col items-start justify-between gap-6 rounded-[12px] bg-card p-8 text-left whitespace-normal dark:bg-card"
          >
            <Badge className="bg-info/10 font-semibold text-info uppercase">
              {side.toUpperCase()}
            </Badge>
            <span
              id={cardTextId}
              className={cn(
                "w-full wrap-anywhere whitespace-pre-wrap",
                flipped
                  ? "text-lg/[1.5] font-normal text-foreground"
                  : "font-heading text-[26px] font-bold",
              )}
            >
              {cardText}
            </span>
            <span className="flex items-center gap-2 text-[15px] font-semibold text-info">
              <RefreshCw aria-hidden="true" className="size-[18px]" />
              Clique no cartão para ver {flipped ? "a pergunta" : "a resposta"}
            </span>
          </Button>
          <span aria-live="polite" aria-atomic="true" className="sr-only">
            {`${side}: ${cardText}`}
          </span>
          {!flipped &&
            card.hint &&
            (showHint ? (
              <p
                ref={focusHint}
                tabIndex={-1}
                className="mt-2 wrap-anywhere text-[15px] text-muted-foreground"
              >
                Dica: {card.hint}
              </p>
            ) : (
              <Button
                type="button"
                variant="ghost"
                className="mt-2"
                onClick={() => setShowHint(true)}
              >
                <Lightbulb aria-hidden="true" />
                Mostrar dica
              </Button>
            ))}
        </CardContent>
        <CardFooter className="justify-between gap-2 border-t bg-muted/50 p-6">
          <Button
            type="button"
            variant="outline"
            className="min-h-12 font-semibold"
            disabled={index === 0}
            onClick={() => moveTo(index - 1)}
          >
            Anterior
          </Button>
          <Button
            type="button"
            variant="outline"
            className="min-h-12 font-semibold"
            disabled={position === cards.length}
            onClick={() => moveTo(index + 1)}
          >
            Próximo
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
