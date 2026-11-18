import { CircleQuestionMark, Layers, SquareCheckBig } from "lucide-react"
import type { ContentFormat } from "@/client"

export const formatIcons = {
  tutorial: SquareCheckBig,
  quiz: CircleQuestionMark,
  flashcards: Layers,
} satisfies Record<ContentFormat, typeof SquareCheckBig>
