import { Check } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export const STEPS = ["Documentos", "Perfil", "Formatos"] as const

interface StepListProps {
  /** Número da etapa atual, a partir de 1. */
  current: number
  /** Números das etapas concluídas. */
  completed: number[]
  onSelect?: (step: number) => void
}

export function StepList({ current, completed, onSelect }: StepListProps) {
  return (
    <ol aria-label="Etapas" className="flex flex-col gap-4">
      {STEPS.map((name, index) => {
        const step = index + 1
        const isCurrent = step === current
        const isCompleted = completed.includes(step)

        return (
          <li
            key={name}
            aria-current={isCurrent ? "step" : undefined}
            className="flex items-center gap-3"
          >
            {isCompleted && onSelect ? (
              <Button
                variant="ghost"
                className="h-auto justify-start gap-3 p-0"
                onClick={() => onSelect(step)}
              >
                <Badge className="size-8 border-transparent bg-success p-0 text-primary-foreground">
                  {step}
                </Badge>
                <span>{name}</span>
              </Button>
            ) : (
              <>
                <Badge
                  className={cn(
                    "size-8 border-transparent p-0 text-sm font-semibold",
                    isCompleted
                      ? "bg-success text-primary-foreground"
                      : isCurrent
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground",
                  )}
                >
                  {isCompleted ? (
                    <Check
                      className="size-4"
                      aria-label={`${step}, concluída`}
                    />
                  ) : (
                    step
                  )}
                </Badge>
                <span
                  className={cn(
                    isCurrent && "font-semibold",
                    !isCurrent && !isCompleted && "text-muted-foreground",
                  )}
                >
                  {name}
                </span>
              </>
            )}
          </li>
        )
      })}
    </ol>
  )
}
