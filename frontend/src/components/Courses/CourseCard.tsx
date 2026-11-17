import { Link } from "@tanstack/react-router"
import type { CourseSummary } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { AUDIENCE_LABELS, COURSE_STATUS_LABELS } from "@/lib/courses"

export function CourseCard({ course }: { course: CourseSummary }) {
  const color =
    course.status === "ready"
      ? "bg-success text-white"
      : course.status === "failed"
        ? "bg-destructive-background text-destructive-foreground"
        : "bg-muted text-foreground"
  return (
    <Link
      to="/courses/$courseId"
      params={{ courseId: course.id }}
      aria-label={course.title}
    >
      <Card className="h-full">
        <CardHeader>
          <h2 className="line-clamp-2 font-heading text-xl font-bold">
            {course.title}
          </h2>
        </CardHeader>
        <CardContent className="flex items-center justify-between gap-2">
          <span>{AUDIENCE_LABELS[course.audience_level]}</span>
          <Badge className={color}>{COURSE_STATUS_LABELS[course.status]}</Badge>
        </CardContent>
      </Card>
    </Link>
  )
}
