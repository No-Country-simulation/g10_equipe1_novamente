import type { ContentFormat } from "@/client"
import { FlashcardsReader } from "./readers/FlashcardsReader"
import { QuizReader } from "./readers/QuizReader"
import { TutorialReader } from "./readers/TutorialReader"

interface ContentReaderProps {
  format: ContentFormat
  content: { [key: string]: unknown }
}

export function ContentReader({ format, content }: ContentReaderProps) {
  switch (format) {
    case "tutorial":
      return <TutorialReader content={content} />
    case "flashcards":
      return <FlashcardsReader content={content} />
    case "quiz":
      return <QuizReader content={content} />
  }
}
