import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { useState } from "react"
import { CoursesService } from "@/client"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  AUDIENCE_LABELS,
  CONTENT_STATUS_LABELS,
  COURSE_STATUS_LABELS,
  courseQueryKey,
  FORMAT_LABELS,
  hasActiveContent,
  POLL_INTERVAL_MS,
} from "@/lib/courses"
import { ContentView } from "./ContentView"

interface CoursePageProps {
  courseId: string
}

export function CoursePage({ courseId }: CoursePageProps) {
  const [selected, setSelected] = useState<string | undefined>()
  const query = useQuery({
    queryKey: courseQueryKey(courseId),
    queryFn: async () =>
      (await CoursesService.readCourse({ path: { course_id: courseId } })).data,
    retry: false,
    refetchInterval: (query) =>
      query.state.data && hasActiveContent(query.state.data.contents)
        ? POLL_INTERVAL_MS
        : false,
  })
  if (query.isPending)
    return (
      <div className="mx-auto max-w-[880px] space-y-6">
        <Skeleton className="h-16 w-2/3" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  if (query.isError) {
    if ((query.error as { status?: number }).status === 404)
      return (
        <div>
          Curso não encontrado. <Link to="/">Voltar para os cursos</Link>
        </div>
      )
    return (
      <Alert variant="destructive">
        <AlertDescription>Não foi possível carregar o curso.</AlertDescription>
        <Button onClick={() => query.refetch()}>Tentar novamente</Button>
      </Alert>
    )
  }
  const course = query.data
  const failed = course.documents.filter((doc) => doc.status === "failed")
  const documents = course.documents.filter((doc) => doc.status !== "failed")
  return (
    <main className="mx-auto max-w-[880px] space-y-8">
      <header className="space-y-4">
        <h1 className="font-heading text-[40px] font-bold">{course.title}</h1>
        <div className="flex flex-wrap gap-2">
          <Badge>{AUDIENCE_LABELS[course.audience_level]}</Badge>
          <Badge>{course.niche.name}</Badge>
          <Badge>{COURSE_STATUS_LABELS[course.status]}</Badge>
        </div>
      </header>
      {failed.length > 0 && (
        <Alert variant="destructive">
          <AlertTitle>Um documento falhou</AlertTitle>
          <AlertDescription>
            {failed.map((doc) => (
              <p key={doc.id}>
                {doc.original_filename}
                {doc.error_message && `: ${doc.error_message}`}
              </p>
            ))}
          </AlertDescription>
        </Alert>
      )}
      {course.contents.length === 1 && (
        <ContentView content={course.contents[0]} />
      )}
      {course.contents.length > 1 && (
        <Tabs
          value={selected ?? course.contents[0].id}
          onValueChange={setSelected}
        >
          <TabsList className="max-w-full overflow-x-auto">
            {course.contents.map((item) => (
              <TabsTrigger key={item.id} value={item.id}>
                {FORMAT_LABELS[item.format]}{" "}
                {CONTENT_STATUS_LABELS[item.status]}
              </TabsTrigger>
            ))}
          </TabsList>
          {course.contents.map((item) => (
            <TabsContent key={item.id} value={item.id}>
              <ContentView content={item} />
            </TabsContent>
          ))}
        </Tabs>
      )}
      {documents.length > 0 && (
        <section className="space-y-3 border-t border-muted pt-6">
          <h2 className="text-xs font-semibold tracking-[0.08em] text-foreground-tertiary">
            MATERIAIS USADOS
          </h2>
          <div className="flex flex-wrap gap-2">
            {documents.map((doc) => (
              <span
                key={doc.id}
                className="rounded-md border border-border px-3 py-1.5 font-mono text-[13px]"
              >
                {doc.original_filename}
              </span>
            ))}
          </div>
        </section>
      )}
    </main>
  )
}
