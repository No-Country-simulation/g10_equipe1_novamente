import type { ContentPublic } from "@/client"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { FORMAT_LABELS } from "@/lib/courses"
import { ContentReader } from "./ContentReader"

interface ContentViewProps {
  content: ContentPublic
}

export function ContentView({ content }: ContentViewProps) {
  return (
    <div className="space-y-6">
      {content.status === "pending" && (
        <Alert>
          <AlertDescription>
            Na fila. Este conteúdo espera a vez de ser gerado.
          </AlertDescription>
        </Alert>
      )}
      {content.status === "running" && (
        <Alert>
          <AlertDescription>
            Gerando. A tela se atualiza sozinha.
          </AlertDescription>
        </Alert>
      )}
      {content.status === "failed" && (
        <Alert variant="destructive">
          <AlertTitle>A geração falhou</AlertTitle>
          <AlertDescription className="whitespace-pre-wrap">
            {content.error_message || "Não foi possível gerar este conteúdo."}
          </AlertDescription>
        </Alert>
      )}
      {content.content !== null && (
        <div className="space-y-4">
          <h2 className="font-heading text-2xl font-bold">
            {content.title || FORMAT_LABELS[content.format]}
          </h2>
          {content.estimated_minutes !== null && (
            <p>{content.estimated_minutes} min de estudo</p>
          )}
          {!!content.key_concepts?.length && (
            <section>
              <h3>Conceitos-chave</h3>
              <div className="flex flex-wrap gap-2">
                {content.key_concepts.map((concept) => (
                  <Badge key={concept}>{concept}</Badge>
                ))}
              </div>
            </section>
          )}
          <section>
            <h3>Pré-requisitos</h3>
            {content.prerequisites?.length ? (
              <ul className="list-disc pl-5">
                {content.prerequisites.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : (
              <p>Nenhum</p>
            )}
          </section>
          <ContentReader format={content.format} content={content.content} />
        </div>
      )}
    </div>
  )
}
