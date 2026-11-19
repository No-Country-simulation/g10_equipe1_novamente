import type { ComponentProps } from "react"
import Markdown, { type Components } from "react-markdown"
import remarkGfm from "remark-gfm"
import { z } from "zod"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Card } from "@/components/ui/card"
import type { ReaderProps } from "./types"

const nonBlankText = z.string().refine((text) => text.trim().length > 0)
const tutorialSchema = z.object({
  summary: nonBlankText,
  sections: z
    .array(z.object({ title: nonBlankText, body: nonBlankText }))
    .min(1)
    .max(8),
  takeaways: z.array(nonBlankText).min(1).max(5),
})

const sectionHeading = "mb-4 font-heading text-[22px] font-bold text-foreground"

function MarkdownHeading({ children }: ComponentProps<"h4">) {
  return <h4 className="mb-2 text-[17px] font-semibold">{children}</h4>
}

const markdownComponents: Components = {
  p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="mb-4 list-disc pl-5">{children}</ul>,
  ol: ({ children, start }) => (
    <ol className="mb-4 list-decimal pl-5" start={start}>
      {children}
    </ol>
  ),
  code: ({ children }) => (
    <code className="font-mono text-sm not-in-[pre]:rounded not-in-[pre]:bg-muted not-in-[pre]:px-1.5 not-in-[pre]:py-0.5">
      {children}
    </code>
  ),
  pre: ({ children }) => (
    <pre className="mb-4 overflow-x-auto rounded-lg bg-muted p-4 font-mono text-sm">
      {children}
    </pre>
  ),
  table: ({ children }) => (
    <div className="mb-4 overflow-x-auto wrap-normal">
      <table className="w-full border-collapse text-left">{children}</table>
    </div>
  ),
  th: ({ children, style }) => (
    <th className="border p-2 font-semibold" style={style}>
      {children}
    </th>
  ),
  td: ({ children, style }) => (
    <td className="border p-2" style={style}>
      {children}
    </td>
  ),
  h1: MarkdownHeading,
  h2: MarkdownHeading,
  h3: MarkdownHeading,
  h4: MarkdownHeading,
  h5: MarkdownHeading,
  h6: MarkdownHeading,
  a: ({ children, href, title }) => (
    <a
      className="text-info underline"
      href={href}
      title={title}
      target="_blank"
      rel="noreferrer"
    >
      {children}
    </a>
  ),
}

export function TutorialReader({ content }: ReaderProps) {
  const tutorial = tutorialSchema.safeParse(content)

  if (!tutorial.success) {
    return (
      <Alert>
        <AlertDescription>
          Não foi possível mostrar este conteúdo, porque ele não está no formato
          esperado.
        </AlertDescription>
      </Alert>
    )
  }

  const { summary, sections, takeaways } = tutorial.data

  return (
    <Card className="mx-auto w-full max-w-[800px] gap-0 rounded-[12px] p-6 wrap-anywhere shadow-none sm:p-10">
      <p className="text-[17px]/[1.6] text-foreground">{summary}</p>
      {sections.map(({ title, body }, index) => (
        <section key={index} className="mt-8">
          <h3 className={sectionHeading}>{title}</h3>
          <div className="text-base/[1.6] text-muted-foreground">
            <Markdown
              components={markdownComponents}
              remarkPlugins={[remarkGfm]}
              skipHtml
            >
              {body}
            </Markdown>
          </div>
        </section>
      ))}
      <section className="mt-8">
        <h3 className={sectionHeading}>Para levar</h3>
        <ul className="list-disc space-y-2 pl-5 text-base/[1.6] text-muted-foreground">
          {takeaways.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </section>
    </Card>
  )
}
