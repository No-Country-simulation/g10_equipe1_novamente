import { Link } from "@tanstack/react-router"
import { ChevronLeft, CircleAlert } from "lucide-react"
import type { ContentPublic, CourseDetail, DocumentPublic } from "@/client"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { AUDIENCE_LABELS, FORMAT_LABELS } from "@/lib/courses"
import { ContentView } from "./ContentView"
import { CourseFallback } from "./CourseFallback"
import { formatIcons } from "./formatIcons"
import { useCourse } from "./useCourse"

export function FailedDocumentsAlert({
  documents,
}: {
  documents: DocumentPublic[]
}) {
  const failedDocuments = documents.filter(({ status }) => status === "failed")
  if (!failedDocuments.length) return null

  return (
    <Alert className="border-[1.5px] border-destructive bg-destructive-background/30 text-destructive-foreground">
      <CircleAlert aria-hidden="true" />
      <AlertTitle>Um documento falhou</AlertTitle>
      <AlertDescription className="text-destructive-foreground">
        {failedDocuments.map((document) => (
          <p key={document.id}>
            <span className="break-all font-mono">
              {document.original_filename}
            </span>
            {document.error_message && `: ${document.error_message}`}
          </p>
        ))}
      </AlertDescription>
    </Alert>
  )
}

export function ContentScreen({
  course,
  content,
  standalone = false,
}: {
  course: CourseDetail
  content: ContentPublic
  standalone?: boolean
}) {
  const Icon = formatIcons[content.format]

  return (
    <div className="space-y-8">
      <header className="space-y-2 rounded-[12px] bg-foreground px-8 py-5 text-background dark:bg-card dark:text-card-foreground">
        <Link
          to={standalone ? "/courses/$courseId" : "/courses"}
          params={standalone ? { courseId: course.id } : undefined}
          className="inline-flex min-h-11 items-center gap-1 text-[15px] text-background/80 hover:underline dark:text-muted-foreground"
        >
          <ChevronLeft aria-hidden="true" className="size-[18px]" />
          {standalone ? "Voltar ao curso" : "Todos os cursos"}
        </Link>
        <div className="flex flex-col items-start gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
          <h1 className="min-w-0 break-words font-heading text-[32px]/[1.1] font-bold">
            {course.title}
          </h1>
          <Badge
            variant="outline"
            className="max-w-full gap-2 whitespace-normal border-background/30 px-3.5 py-2 text-sm text-inherit dark:border-card-foreground/30"
          >
            <Icon aria-hidden="true" className="size-4! shrink-0" />
            {FORMAT_LABELS[content.format]} ·{" "}
            {AUDIENCE_LABELS[course.audience_level]} · {course.niche.name}
          </Badge>
        </div>
      </header>
      <FailedDocumentsAlert documents={course.documents} />
      <ContentView courseId={course.id} content={content} />
    </div>
  )
}

export function ContentPage({
  courseId,
  contentId,
}: {
  courseId: string
  contentId: string
}) {
  const query = useCourse(courseId)
  if (query.isPending || query.isLoadingError) {
    return <CourseFallback query={query} />
  }

  const content = query.data.contents.find(({ id }) => id === contentId)
  if (!content) {
    return (
      <div className="space-y-2">
        <p>Conteúdo não encontrado.</p>
        <Link
          to="/courses/$courseId"
          params={{ courseId }}
          className="text-info hover:underline"
        >
          Voltar ao curso
        </Link>
      </div>
    )
  }

  return <ContentScreen course={query.data} content={content} standalone />
}
