import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { CoursesService } from "@/client"
import { CourseCard } from "@/components/Courses/CourseCard"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  coursesQueryKey,
  hasActiveContent,
  POLL_INTERVAL_MS,
} from "@/lib/courses"

export const Route = createFileRoute("/_layout/courses/")({
  component: Courses,
  head: () => ({ meta: [{ title: "Cursos - NovaMente" }] }),
})
function Courses() {
  const query = useQuery({
    queryKey: coursesQueryKey,
    queryFn: async () => (await CoursesService.readCourses()).data,
    refetchInterval: (query) =>
      query.state.data?.data.some((course) => hasActiveContent(course.contents))
        ? POLL_INTERVAL_MS
        : false,
  })
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between gap-4">
        <h1 className="font-heading text-[40px] font-bold">Cursos</h1>
        <Button asChild>
          <Link to="/courses/new">Novo curso</Link>
        </Button>
      </div>
      {query.isPending ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      ) : query.isLoadingError ? (
        <Alert variant="destructive">
          <AlertTitle>Não foi possível carregar os cursos.</AlertTitle>
          <AlertDescription>
            <Button onClick={() => query.refetch()}>Tentar novamente</Button>
          </AlertDescription>
        </Alert>
      ) : query.data?.data.length ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {query.data.data.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-start gap-4">
          <p>Você ainda não tem cursos.</p>
          <Button asChild>
            <Link to="/courses/new">Criar o primeiro curso</Link>
          </Button>
        </div>
      )}
    </div>
  )
}
