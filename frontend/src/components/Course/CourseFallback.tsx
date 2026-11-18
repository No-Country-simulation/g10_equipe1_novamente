import { Link } from "@tanstack/react-router"
import { isAxiosError } from "axios"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import type { useCourse } from "./useCourse"

export function CourseFallback({
  query,
}: {
  query: ReturnType<typeof useCourse>
}) {
  if (query.isPending) {
    return (
      <div className="space-y-8">
        <Skeleton className="h-32" />
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      </div>
    )
  }

  if (isAxiosError(query.error) && query.error.response?.status === 404) {
    return (
      <div className="space-y-2">
        <p>Curso não encontrado.</p>
        <Link to="/courses" className="text-info hover:underline">
          Voltar para os cursos
        </Link>
      </div>
    )
  }

  return (
    <Alert variant="destructive">
      <AlertTitle>Não foi possível carregar o curso.</AlertTitle>
      <AlertDescription>
        <Button onClick={() => query.refetch()}>Tentar novamente</Button>
      </AlertDescription>
    </Alert>
  )
}
