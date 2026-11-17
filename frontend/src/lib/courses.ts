import type {
  AudienceLevel,
  ClarityLevel,
  ContentFormat,
  CourseStatus,
  GenerationStatus,
} from "@/client"

export const POLL_INTERVAL_MS = 3000

export const coursesQueryKey = ["courses"] as const

export const courseQueryKey = (userId: string, courseId: string) =>
  [...coursesQueryKey, userId, courseId] as const

export const AUDIENCE_LABELS: Record<AudienceLevel, string> = {
  non_technical: "Não técnico",
  technical_basic: "Técnico básico",
  technical_advanced: "Técnico avançado",
}

export const COURSE_STATUS_LABELS: Record<CourseStatus, string> = {
  initializing: "Gerando",
  ready: "Pronto",
  failed: "Falhou",
}

export const CONTENT_STATUS_LABELS: Record<GenerationStatus, string> = {
  pending: "Na fila",
  running: "Gerando",
  succeeded: "Pronto",
  failed: "Falhou",
}

export const FORMAT_LABELS: Record<ContentFormat, string> = {
  tutorial: "Tutorial",
  flashcards: "Flashcards",
  quiz: "Quiz",
}

export const CLARITY_LABELS: Record<ClarityLevel, string> = {
  low: "Baixa",
  medium: "Média",
  high: "Alta",
}

export function hasActiveContent(
  contents: Array<{ status: GenerationStatus }>,
): boolean {
  return contents.some(
    (content) => content.status === "pending" || content.status === "running",
  )
}
