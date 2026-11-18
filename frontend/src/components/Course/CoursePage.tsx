import { Link } from "@tanstack/react-router"
import { ChevronLeft } from "lucide-react"
import { ContentCard } from "./ContentCard"
import { ContentScreen, FailedDocumentsAlert } from "./ContentPage"
import { CourseFallback } from "./CourseFallback"
import { CourseSummary } from "./CourseSummary"
import { useCourse } from "./useCourse"

interface CoursePageProps {
  courseId: string
}

export function CoursePage({ courseId }: CoursePageProps) {
  const query = useCourse(courseId)
  if (query.isPending || query.isError) return <CourseFallback query={query} />

  const course = query.data
  if (course.contents.length === 1) {
    return (
      <div className="space-y-8">
        <ContentScreen course={course} content={course.contents[0]} />
        <CourseSummary course={course} />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <Link
          to="/courses"
          className="inline-flex min-h-11 items-center gap-1 text-[15px] text-info hover:underline"
        >
          <ChevronLeft aria-hidden="true" className="size-[18px]" />
          Todos os cursos
        </Link>
        <p className="text-xs font-semibold tracking-[0.08em] text-foreground-tertiary">
          CURSO
        </p>
        <h1 className="break-words font-heading text-[40px]/[42px] font-bold">
          {course.title}
        </h1>
      </header>
      <FailedDocumentsAlert documents={course.documents} />
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {course.contents.map((content, index) => (
          <ContentCard
            key={content.id}
            courseId={course.id}
            content={content}
            number={index + 1}
          />
        ))}
      </div>
      <CourseSummary course={course} />
    </div>
  )
}
