import { useId, useState } from "react"
import type { CitationPublic, ContentPublic } from "@/client"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { CLARITY_LABELS } from "@/lib/courses"

interface ContentEvaluationProps {
  content: ContentPublic
}

const CITATION_PREVIEW_LENGTH = 600

function CitationItem({ citation }: { citation: CitationPublic }) {
  const [expanded, setExpanded] = useState(false)
  const textId = useId()
  const characters = Array.from(citation.text)
  const canExpand = characters.length > CITATION_PREVIEW_LENGTH
  const text =
    canExpand && !expanded
      ? `${characters.slice(0, CITATION_PREVIEW_LENGTH).join("")}…`
      : citation.text

  return (
    <li className="rounded-lg border-l-[3px] border-info bg-muted/50 p-4">
      <p className="wrap-anywhere text-[13px] text-foreground-tertiary">
        <span className="font-mono">{citation.document_title}</span>
        {citation.page_number !== null && ` · página ${citation.page_number}`}
        {citation.similarity !== null &&
          ` · similaridade ${citation.similarity.toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}`}
      </p>
      <p
        id={textId}
        className="mt-2 wrap-anywhere whitespace-pre-wrap text-[15px]/[1.5] text-foreground"
      >
        {text}
      </p>
      {canExpand && (
        <Button
          type="button"
          variant="link"
          className="px-0"
          aria-controls={textId}
          aria-expanded={expanded}
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "Mostrar menos" : "Mostrar trecho inteiro"}
        </Button>
      )}
    </li>
  )
}

export function ContentEvaluation({ content }: ContentEvaluationProps) {
  const labelId = useId()
  const citationsHeadingId = useId()
  const { grounding_score, clarity, review_notes, citations } = content
  const hasReviewNotes = Boolean(review_notes?.trim())
  const hasReview =
    grounding_score !== null || clarity !== null || hasReviewNotes

  if (!hasReview && citations.length === 0) return null

  return (
    <Card
      role="region"
      aria-labelledby={labelId}
      className="rounded-[12px] p-6"
    >
      <div className="space-y-4">
        <div>
          <p
            id={labelId}
            className="mb-1 text-sm font-semibold text-foreground-tertiary"
          >
            Avaliação
          </p>
          <h2 className="font-heading text-2xl font-bold">
            Fidelidade e clareza
          </h2>
        </div>
        {hasReview && (
          <dl className="grid gap-4 text-[15px]/[21px] text-foreground sm:grid-cols-3 [&_dt]:text-xs [&_dt]:font-semibold [&_dt]:tracking-[0.08em] [&_dt]:text-foreground-tertiary">
            {grounding_score !== null && (
              <div>
                <dt>FIDELIDADE AO DOCUMENTO</dt>
                <dd>
                  <span className="block font-heading text-[28px] font-bold leading-tight">
                    {Math.round(grounding_score * 100)}%
                  </span>
                  <p className="text-sm text-muted-foreground">
                    Afirmações técnicas do conteúdo de estudo com apoio nos
                    trechos do documento.
                  </p>
                </dd>
              </div>
            )}
            {clarity !== null && (
              <div>
                <dt>CLAREZA</dt>
                <dd>
                  {CLARITY_LABELS[clarity]}
                  <p className="text-sm text-muted-foreground">
                    Para o nível de público do curso.
                  </p>
                </dd>
              </div>
            )}
            {hasReviewNotes && (
              <div>
                <dt>OBSERVAÇÕES DA REVISÃO</dt>
                <dd className="wrap-anywhere whitespace-pre-line">
                  {review_notes}
                </dd>
              </div>
            )}
          </dl>
        )}
      </div>
      <div className="space-y-2">
        <h3 id={citationsHeadingId} className="font-heading text-lg font-bold">
          Trechos citados
        </h3>
        {citations.length > 0 ? (
          <ul aria-labelledby={citationsHeadingId} className="space-y-3">
            {citations.map((citation) => (
              <CitationItem key={citation.chunk_id} citation={citation} />
            ))}
          </ul>
        ) : (
          <p className="text-[15px] text-muted-foreground">
            Nenhum trecho citado.
          </p>
        )}
      </div>
    </Card>
  )
}
