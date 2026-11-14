import { createFileRoute } from "@tanstack/react-router"

import { STEPS, StepList } from "@/components/NewCourse/StepList"

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
        <section className="min-h-[560px] rounded-[12px] border bg-card p-6 sm:p-8">
          <p className="text-sm font-semibold tracking-wide text-info">
            ETAPA {current} DE {STEPS.length}
          </p>
          <h2 className="mt-2 text-2xl">{STEPS[current - 1]}</h2>
        </section>
      </div>
    </div>
  )
}
