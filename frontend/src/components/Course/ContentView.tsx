import type { ContentPublic } from "@/client"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { FORMAT_LABELS } from "@/lib/courses"
import { ContentEvaluation } from "./ContentEvaluation"
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
        <>
          <Card
            role="region"
            aria-labelledby="content-metadata"
            className="gap-4 rounded-[12px] p-6"
          >
            <div>
              <p
                id="content-metadata"
                className="mb-1 text-sm font-semibold text-foreground-tertiary"
              >
                Sobre este conteúdo
              </p>
              <h2 className="break-words font-heading text-2xl font-bold">
                {content.title || FORMAT_LABELS[content.format]}
              </h2>
            </div>
            <dl className="grid gap-4 text-[15px]/[21px] text-foreground sm:grid-cols-3 [&_dt]:text-xs [&_dt]:font-semibold [&_dt]:tracking-[0.08em] [&_dt]:text-foreground-tertiary">
              {content.estimated_minutes !== null && (
                <div>
                  <dt>TEMPO DE ESTUDO</dt>
                  <dd>cerca de {content.estimated_minutes} min</dd>
                </div>
              )}
              {!!content.key_concepts?.length && (
                <div>
                  <dt>CONCEITOS-CHAVE</dt>
                  <dd className="mt-1 flex flex-wrap gap-2">
                    {content.key_concepts.map((concept) => (
                      <Badge
                        key={concept}
                        variant="outline"
                        className="max-w-full whitespace-normal break-all"
                      >
                        {concept}
                      </Badge>
                    ))}
                  </dd>
                </div>
              )}
              <div>
                <dt>PRÉ-REQUISITOS</dt>
                <dd>
                  {content.prerequisites?.length ? (
                    <ul className="list-disc pl-5">
                      {content.prerequisites.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    "Nenhum"
                  )}
                </dd>
              </div>
            </dl>
          </Card>
          <ContentReader format={content.format} content={content.content} />
          <ContentEvaluation content={content} />
        </>
      )}
    </div>
  )
}
