import { createFileRoute } from "@tanstack/react-router"

import { CoursePage } from "@/components/Course/CoursePage"

export const Route = createFileRoute("/_layout/courses/$courseId/")({
  component: CourseRoute,
})

function CourseRoute() {
  const { courseId } = Route.useParams()
  return <CoursePage courseId={courseId} />
}
