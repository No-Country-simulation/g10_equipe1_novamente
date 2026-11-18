import type { CourseDetail } from "@/client"
import { Card } from "@/components/ui/card"
import { AUDIENCE_LABELS, FORMAT_LABELS } from "@/lib/courses"

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
      <h2 id="course-summary-title" className="font-heading text-2xl font-bold">
        Resumo do curso
      </h2>
      <dl className="flex flex-col gap-4 text-[15px]/[21px] text-foreground lg:flex-row lg:flex-wrap lg:gap-x-10 [&_dt]:text-xs [&_dt]:font-semibold [&_dt]:tracking-[0.08em] [&_dt]:text-foreground-tertiary">
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
              <ul className="mt-1 flex flex-wrap gap-2" aria-label="Materiais">
                {documents.map((document) => (
                  <li
                    key={document.id}
                    className="min-w-0 break-all rounded-sm border px-3 py-1.5 font-mono text-[13px]"
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
