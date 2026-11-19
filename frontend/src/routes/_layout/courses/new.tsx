import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { isAxiosError } from "axios"
import { useRef, useState } from "react"
import {
  type Body_courses_create_course,
  type ContentFormat,
  CoursesService,
} from "@/client"
import { DocumentsStep } from "@/components/NewCourse/DocumentsStep"
import type { DraftDocument } from "@/components/NewCourse/documents"
import { FormatsStep } from "@/components/NewCourse/FormatsStep"
import {
  type ProfileDraft,
  ProfileStep,
} from "@/components/NewCourse/ProfileStep"
import { STEPS, StepList } from "@/components/NewCourse/StepList"
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { coursesQueryKey } from "@/lib/courses"

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

const stepDescriptions = [
  "Envie os seus materiais. Todos entram no curso.",
  "Diga para quem é o curso.",
  "Escolha o que o curso vai gerar.",
]

function createCourseError(error: unknown) {
  if (isAxiosError<{ detail?: unknown }>(error) && error.response) {
    const { data, status } = error.response
    const detail = data?.detail
    if ([404, 422, 503].includes(status) && typeof detail === "string")
      return detail
    if (status === 422 && Array.isArray(detail))
      return "Verifique os dados informados e tente novamente."
  }
  return "Não foi possível falar com o servidor. Tente novamente."
}

function NewCourse() {
  const [step, setStep] = useState(1)
  const [documents, setDocuments] = useState<DraftDocument[]>([])
  const [profile, setProfile] = useState<ProfileDraft>({
    title: "",
    nicheId: null,
    audienceLevel: null,
  })
  const [formats, setFormats] = useState<ContentFormat[]>([])
  const submitting = useRef(false)
  const navigate = Route.useNavigate()
  const queryClient = useQueryClient()
  const course = useMutation({
    mutationFn: (body: Body_courses_create_course) =>
      CoursesService.createCourse({ body }),
    onSuccess: ({ data }) => {
      void queryClient.invalidateQueries({ queryKey: coursesQueryKey })
      return navigate({
        to: "/courses/$courseId",
        params: { courseId: data.id },
      })
    },
    onSettled: () => {
      submitting.current = false
    },
  })

  function goToStep(next: number) {
    if (submitting.current) return
    course.reset()
    setStep(next)
  }

  function submitCourse() {
    const { title, nicheId, audienceLevel } = profile
    if (
      submitting.current ||
      nicheId === null ||
      !audienceLevel ||
      !formats.length
    )
      return
    submitting.current = true
    course.mutate({
      title: title.trim(),
      niche_id: nicheId,
      audience_level: audienceLevel,
      formats,
      files: documents.map((document) => document.file),
    })
  }

  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-[40px] leading-tight">Novo curso</h1>
      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <StepList
          current={step}
          completed={[1, 2].slice(0, step - 1)}
          onSelect={course.isPending ? undefined : goToStep}
        />
        <Card className="min-h-[560px] overflow-hidden rounded-[12px] pb-0">
          <CardHeader>
            <CardDescription className="text-xs font-semibold tracking-[0.08em] text-foreground-tertiary">
              ETAPA {step} DE {STEPS.length}
            </CardDescription>
            <CardTitle className="font-heading text-[30px] leading-tight font-bold">
              {STEPS[step - 1]}
            </CardTitle>
            <CardDescription className="text-base leading-normal">
              {stepDescriptions[step - 1]}
            </CardDescription>
          </CardHeader>
          {step === 1 && (
            <DocumentsStep
              documents={documents}
              onChange={setDocuments}
              onContinue={() => setStep(2)}
            />
          )}
          {step === 2 && (
            <ProfileStep
              profile={profile}
              onChange={setProfile}
              onBack={() => goToStep(1)}
              onContinue={() => setStep(3)}
            />
          )}
          {step === 3 && (
            <FormatsStep
              formats={formats}
              onChange={setFormats}
              onBack={() => goToStep(2)}
              onSubmit={submitCourse}
              submitting={course.isPending}
              error={course.isError ? createCourseError(course.error) : null}
            />
          )}
        </Card>
      </div>
    </div>
  )
}
