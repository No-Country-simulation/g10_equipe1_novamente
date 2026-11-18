import { createFileRoute } from "@tanstack/react-router"

import { ContentPage } from "@/components/Course/ContentPage"

export const Route = createFileRoute(
  "/_layout/courses/$courseId/contents/$contentId",
)({
  component: ContentRoute,
})

function ContentRoute() {
  const { courseId, contentId } = Route.useParams()
  return <ContentPage courseId={courseId} contentId={contentId} />
}
