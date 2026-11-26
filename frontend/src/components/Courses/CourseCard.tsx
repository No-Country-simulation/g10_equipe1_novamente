import { Link } from "@tanstack/react-router"
import type { AudienceLevel, CourseSummary } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { AUDIENCE_LABELS, COURSE_STATUS_LABELS } from "@/lib/courses"

const audienceBarCounts = {
  non_technical: 1,
  technical_basic: 2,
  technical_advanced: 3,
} satisfies Record<AudienceLevel, number>

const barHeights = ["h-1.5", "h-2.5", "h-4"]

export function CourseCard({ course }: { course: CourseSummary }) {
  const activeBars = audienceBarCounts[course.audience_level]
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
        <CardContent className="mt-auto flex items-center justify-between gap-2">
          <span className="inline-flex items-center gap-2 text-muted-foreground">
            <span
              aria-hidden="true"
              className="inline-flex shrink-0 items-end gap-0.5"
            >
              {barHeights.map((height, index) => (
                <span
                  key={height}
                  data-active={index < activeBars ? true : undefined}
                  className={`w-1 bg-border-strong data-active:bg-foreground ${height}`}
                />
              ))}
            </span>
            {AUDIENCE_LABELS[course.audience_level]}
          </span>
          <Badge className={color}>{COURSE_STATUS_LABELS[course.status]}</Badge>
        </CardContent>
      </Card>
    </Link>
  )
}
