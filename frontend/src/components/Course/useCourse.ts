import { useQuery } from "@tanstack/react-query"
import { CoursesService } from "@/client"
import {
  courseQueryKey,
  hasActiveContent,
  POLL_INTERVAL_MS,
} from "@/lib/courses"

export function useCourse(courseId: string) {
  return useQuery({
    queryKey: courseQueryKey(courseId),
    queryFn: async () =>
      (await CoursesService.readCourse({ path: { course_id: courseId } })).data,
    retry: false,
    refetchInterval: ({ state }) =>
      state.data && hasActiveContent(state.data.contents)
        ? POLL_INTERVAL_MS
        : false,
  })
}
