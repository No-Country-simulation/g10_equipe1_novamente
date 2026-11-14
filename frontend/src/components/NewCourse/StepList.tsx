import { Check } from "lucide-react"

import { cn } from "@/lib/utils"

export const STEPS = ["Documentos", "Perfil", "Formatos"] as const

interface StepListProps {
  /** Número da etapa atual, a partir de 1. */
  current: number
  /** Números das etapas concluídas. */
  completed: number[]
}

export function StepList({ current, completed }: StepListProps) {
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
            <span
              className={cn(
                "flex size-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
                isCompleted
                  ? "bg-success text-primary-foreground"
                  : isCurrent
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground",
              )}
            >
              {isCompleted ? (
                <Check className="size-4" aria-label={`${step}, concluída`} />
              ) : (
                step
              )}
            </span>
            <span
              className={cn(
                isCurrent && "font-semibold",
                !isCurrent && !isCompleted && "text-muted-foreground",
              )}
            >
              {name}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
