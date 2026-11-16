import { createFileRoute } from "@tanstack/react-router"
import { STEPS, StepList } from "@/components/NewCourse/StepList"
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
  const current = 1

  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-[40px] leading-tight">Novo curso</h1>
      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <StepList current={current} completed={[]} />
        <Card className="min-h-[560px] rounded-[12px]">
          <CardHeader>
            <CardDescription className="text-sm font-semibold tracking-wide text-info">
              ETAPA {current} DE {STEPS.length}
            </CardDescription>
            <CardTitle className="font-heading text-2xl leading-tight font-bold">
              {STEPS[current - 1]}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>
    </div>
  )
}
