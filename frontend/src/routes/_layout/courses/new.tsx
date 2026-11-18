import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { DocumentsStep } from "@/components/NewCourse/DocumentsStep"
import type { DraftDocument } from "@/components/NewCourse/documents"
import { STEPS, StepList } from "@/components/NewCourse/StepList"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export const Route = createFileRoute("/_layout/courses/new")({
  component: NewCourse,
  head: () => ({
    meta: [
      {
        title: "Novo curso - NovaMente",
      },
    ],
  }),
})

function NewCourse() {
  const [current, setStep] = useState(1)
  const [documents, setDocuments] = useState<DraftDocument[]>([])

  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-[40px] leading-tight">Novo curso</h1>
      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <StepList
          current={current}
          completed={current > 1 ? [1] : []}
          onSelect={setStep}
        />
        <Card className="min-h-[560px] overflow-hidden rounded-[12px] border-t-4 border-t-primary pb-0 shadow-sm">
          <CardHeader>
            <CardDescription className="text-xs font-semibold tracking-[0.08em] text-foreground-tertiary">
              ETAPA {current} DE {STEPS.length}
            </CardDescription>
            <CardTitle className="font-heading text-[30px] leading-tight font-bold">
              {STEPS[current - 1]}
            </CardTitle>
            {current === 1 && (
              <CardDescription className="text-base leading-normal">
                Envie os seus materiais. Todos entram no curso.
              </CardDescription>
            )}
          </CardHeader>
          {current === 1 ? (
            <DocumentsStep
              documents={documents}
              onChange={setDocuments}
              onContinue={() => setStep(2)}
            />
          ) : (
            <div className="mt-auto border-t bg-muted/50 p-6">
              <Button
                variant="outline"
                className="min-h-12 px-[22px]"
                onClick={() => setStep(1)}
              >
                Voltar
              </Button>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
