import { useMutation, useQueryClient } from "@tanstack/react-query"
import { isAxiosError } from "axios"
import { CoursesService } from "@/client"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { courseQueryKey, coursesQueryKey } from "@/lib/courses"
import { handleError } from "@/utils"

export function RetryButton({
  courseId,
  contentId,
  className,
}: {
  courseId: string
  contentId: string
  className?: string
}) {
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()
  const retry = useMutation({
    mutationFn: () =>
      CoursesService.retryContent({
        path: { course_id: courseId, content_id: contentId },
      }),
    onSuccess: async ({ data }) => {
      const queryKey = courseQueryKey(courseId)
      await queryClient.cancelQueries({ queryKey })
      queryClient.setQueryData(queryKey, data)
      await queryClient.invalidateQueries({
        queryKey: coursesQueryKey,
        exact: true,
      })
    },
    onError: (error) => {
      const detail = isAxiosError<{ detail?: unknown }>(error)
        ? error.response?.data?.detail
        : undefined
      if (typeof detail === "string") {
        showErrorToast(detail)
      } else {
        handleError.call(showErrorToast, error)
      }
    },
  })

  return (
    <LoadingButton
      type="button"
      className={className}
      loading={retry.isPending}
      onClick={() => retry.mutate()}
    >
      Tentar novamente
    </LoadingButton>
  )
}
