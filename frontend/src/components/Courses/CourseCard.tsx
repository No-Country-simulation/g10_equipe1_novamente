import { Link } from "@tanstack/react-router"
import { SignalHigh, SignalLow, SignalMedium } from "lucide-react"
import type { AudienceLevel, CourseSummary } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { AUDIENCE_LABELS, COURSE_STATUS_LABELS } from "@/lib/courses"

const audienceIcons = {
  non_technical: SignalLow,
  technical_basic: SignalMedium,
  technical_advanced: SignalHigh,
} satisfies Record<AudienceLevel, typeof SignalLow>

export function CourseCard({ course }: { course: CourseSummary }) {
  const AudienceIcon = audienceIcons[course.audience_level]
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
          <span className="inline-flex items-center gap-2">
            <AudienceIcon
              aria-hidden="true"
              className="size-4 shrink-0 text-muted-foreground"
            />
            {AUDIENCE_LABELS[course.audience_level]}
          </span>
          <Badge className={color}>{COURSE_STATUS_LABELS[course.status]}</Badge>
        </CardContent>
      </Card>
    </Link>
  )
}
