import type { CourseDetail } from "@/client"
import { Card } from "@/components/ui/card"
import { AUDIENCE_LABELS, FORMAT_LABELS, hasActiveContent } from "@/lib/courses"
import { DeleteCourse } from "./DeleteCourse"

export function CourseSummary({ course }: { course: CourseDetail }) {
  const formats = course.contents.map(({ format }, index) =>
    index === 0 ? FORMAT_LABELS[format] : FORMAT_LABELS[format].toLowerCase(),
  )
  const formatList =
    formats.length > 1
      ? `${formats.slice(0, -1).join(", ")} e ${formats[formats.length - 1]}`
      : formats.join("")
  const documents = course.documents.filter(
    (document) => document.status !== "failed",
  )

  return (
    <Card
      role="region"
      aria-labelledby="course-summary-title"
      className="gap-6 rounded-[12px] p-6 lg:grid lg:grid-cols-[240px_minmax(0,1fr)]"
    >
      <div className="space-y-3">
        <h2
          id="course-summary-title"
          className="font-heading text-2xl font-bold"
        >
          Resumo do curso
        </h2>
        <DeleteCourse
          courseId={course.id}
          active={hasActiveContent(course.contents)}
        />
      </div>
      <dl className="grid gap-4 text-[15px]/[21px] text-foreground lg:grid-cols-[auto_auto_minmax(0,max-content)_minmax(8rem,1fr)] lg:items-start lg:gap-x-10 [&_dd]:mt-1 lg:[&_dd]:flex lg:[&_dd]:min-h-9 lg:[&_dd]:items-center [&_dt]:text-xs [&_dt]:font-semibold [&_dt]:tracking-[0.08em] [&_dt]:text-foreground-tertiary">
        <div>
          <dt>SETOR</dt>
          <dd>{course.niche.name}</dd>
        </div>
        <div>
          <dt>NÍVEL</dt>
          <dd>{AUDIENCE_LABELS[course.audience_level]}</dd>
        </div>
        <div>
          <dt>FORMATOS</dt>
          <dd>{formatList}</dd>
        </div>
        {documents.length > 0 && (
          <div className="min-w-0">
            <dt>MATERIAIS</dt>
            <dd>
              <ul
                className="flex min-w-0 flex-wrap gap-2"
                aria-label="Materiais"
              >
                {documents.map((document) => (
                  <li
                    key={document.id}
                    className="min-w-0 wrap-anywhere rounded-sm border px-3 py-1.5 font-mono text-[13px]"
                  >
                    {document.original_filename}
                  </li>
                ))}
              </ul>
            </dd>
          </div>
        )}
      </dl>
    </Card>
  )
}
