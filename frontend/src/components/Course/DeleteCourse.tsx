import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { AxiosError } from "axios"
import { useId } from "react"

import { CoursesService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { courseQueryKey, coursesQueryKey } from "@/lib/courses"
import { handleError } from "@/utils"

export function DeleteCourse({
  courseId,
  active,
}: {
  courseId: string
  active: boolean
}) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const hintId = useId()
  const mutation = useMutation({
    mutationFn: () =>
      CoursesService.deleteCourse({ path: { course_id: courseId } }),
    onSuccess: async () => {
      showSuccessToast("Curso excluído.")
      await navigate({ to: "/courses", replace: true })
      queryClient.removeQueries({
        queryKey: courseQueryKey(courseId),
        exact: true,
      })
      await queryClient.invalidateQueries({
        queryKey: coursesQueryKey,
        exact: true,
      })
    },
    onError: (error) => {
      const detail =
        error instanceof AxiosError ? error.response?.data?.detail : undefined
      if (typeof detail === "string") {
        showErrorToast(detail)
      } else {
        handleError.call(showErrorToast, error)
      }
    },
  })

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          disabled={active || mutation.isPending}
          aria-describedby={active ? hintId : undefined}
        >
          Excluir curso
        </Button>
      </DialogTrigger>
      {active && (
        <p id={hintId} className="text-sm text-foreground-tertiary">
          Espere a geração terminar para excluir o curso.
        </p>
      )}
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Excluir este curso?</DialogTitle>
          <DialogDescription>
            Esta ação apaga o curso, os documentos e os conteúdos de forma
            permanente.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" disabled={mutation.isPending}>
              Cancelar
            </Button>
          </DialogClose>
          <LoadingButton
            variant="destructive"
            loading={mutation.isPending}
            onClick={() => mutation.mutate()}
          >
            Excluir
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
