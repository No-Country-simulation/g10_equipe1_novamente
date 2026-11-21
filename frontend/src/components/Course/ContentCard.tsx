import { Link } from "@tanstack/react-router"
import type { ContentPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { CONTENT_STATUS_LABELS, FORMAT_LABELS } from "@/lib/courses"
import { cn } from "@/lib/utils"
import { formatIcons } from "./formatIcons"
import { RetryButton } from "./RetryButton"

interface ContentCardProps {
  courseId: string
  content: ContentPublic
  number: number
}

const statusColors = {
  succeeded: "bg-success text-white",
  failed: "bg-destructive-background text-destructive-foreground",
  pending: "bg-muted text-foreground",
  running: "bg-muted text-foreground",
} satisfies Record<ContentPublic["status"], string>

export function ContentCard({ courseId, content, number }: ContentCardProps) {
  const Icon = formatIcons[content.format]
  const format = FORMAT_LABELS[content.format]
  const title = content.title || format
  const failed = content.status === "failed"
  const statusText = {
    pending: "Este conteúdo espera a vez de ser gerado.",
    running: "A tela se atualiza sozinha.",
    failed: content.error_message || "Não foi possível gerar este conteúdo.",
    succeeded: null,
  }[content.status]
  const actionClass = "h-12 w-full text-base font-semibold"
  const actionLabel = `Abrir ${title}`

  return (
    <Card
      className={cn(
        "gap-3.5 rounded-[12px] p-5",
        failed && "border-destructive-foreground",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="grid size-11 place-items-center rounded-lg bg-info/10 text-info">
          <Icon aria-hidden="true" className="size-[22px]" />
        </span>
        <Badge
          variant="outline"
          className={`border-transparent px-2.5 ${statusColors[content.status]}`}
        >
          {CONTENT_STATUS_LABELS[content.status]}
        </Badge>
      </div>
      <div className="space-y-1.5">
        <p className="text-xs font-semibold tracking-[0.08em] text-foreground-tertiary">
          CONTEÚDO {number} · {format.toUpperCase()}
        </p>
        <h2 className="break-words font-heading text-[21px]/[1.2] font-bold">
          {title}
        </h2>
      </div>
      {statusText && (
        <p
          className={`break-words text-[15px]/[1.5] ${failed ? "whitespace-pre-line text-destructive-foreground" : "text-muted-foreground"}`}
        >
          {statusText}
        </p>
      )}
      <div className="mt-auto space-y-3.5">
        {content.estimated_minutes !== null && (
          <p className="text-sm text-foreground-tertiary">
            cerca de {content.estimated_minutes} min
          </p>
        )}
        {content.content !== null ? (
          <Button asChild variant="outline" className={actionClass}>
            <Link
              to="/courses/$courseId/contents/$contentId"
              params={{ courseId, contentId: content.id }}
              aria-label={actionLabel}
            >
              Abrir
            </Link>
          </Button>
        ) : (
          <Button
            variant="outline"
            className={actionClass}
            aria-label={actionLabel}
            disabled
          >
            Abrir
          </Button>
        )}
        {failed && (
          <RetryButton
            courseId={courseId}
            contentId={content.id}
            className={actionClass}
          />
        )}
      </div>
    </Card>
  )
}
