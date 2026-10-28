import { createFileRoute, Link } from "@tanstack/react-router"
import {
  CheckCircle2,
  Lock,
  Play,
  RotateCcw,
  ArrowRight,
  BookOpen,
  Trophy,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { mockCursos } from "@/data/mockCourses"

export const Route = createFileRoute("/_layout/roadmap")({
  component: RoadmapPage,
  head: () => ({
    meta: [
      {
        title: "Roadmap da Trilha — NovaMente (RAG OCI)",
      },
    ],
  }),
})

function RoadmapPage() {
  const curso = mockCursos[0] // Curso VCN da OCI

  const etapasConcluidas = curso.etapas.filter((e) => e.status === "concluido").length
  const totalEtapas = curso.etapas.length
  const todosConcluidos = etapasConcluidas === totalEtapas

  return (
    <div className="space-y-8 pb-16">
      {/* 1. Header do Roadmap */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link to="/" className="text-xs text-muted-foreground hover:text-foreground">
              Início
            </Link>
            <span className="text-xs text-muted-foreground">/</span>
            <Badge variant="outline" className="text-xs font-mono text-primary border-primary/30">
              TRILHA ATIVA
            </Badge>
          </div>
          <h1 className="text-3xl font-bold font-heading text-foreground">
            {curso.titulo}
          </h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            {curso.descricao}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link to={"/finalizacao" as any}>
            <Button
              variant={todosConcluidos ? "default" : "outline"}
              className={todosConcluidos ? "bg-green-600 hover:bg-green-700 text-white gap-2" : "gap-2"}
            >
              <Trophy className="h-4 w-4" />
              <span>{todosConcluidos ? "Ver Conclusão" : "Resumo da Trilha"}</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Grid Principal: Timeline de Módulos (2 colunas no desktop) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Coluna da Esquerda: Timeline dos Módulos */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold font-heading text-foreground flex items-center gap-2">
              <span>Etapas do Aprendizado</span>
              <span className="text-xs font-mono font-normal text-muted-foreground">
                ({etapasConcluidas} de {totalEtapas} concluídas)
              </span>
            </h2>
            <span className="text-xs font-mono font-bold text-primary">
              {curso.progresso_percentual}% PROGRESSO
            </span>
          </div>

          <div className="space-y-4 relative before:absolute before:inset-0 before:left-5 before:w-0.5 before:bg-border before:z-0">
            {curso.etapas.map((etapa) => {
              const isConcluido = etapa.status === "concluido"
              const isDisponivel = etapa.status === "disponivel"
              const isBloqueado = etapa.status === "bloqueado"

              return (
                <div
                  key={etapa.id}
                  className={`relative z-10 rounded-xl border transition-all ${
                    isDisponivel
                      ? "border-primary bg-card shadow-md ring-1 ring-primary/20"
                      : isConcluido
                      ? "border-green-600/30 bg-card"
                      : "border-border bg-card/60 opacity-70"
                  }`}
                >
                  <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-start gap-4">
                      {/* Indicador de Número / Status */}
                      <div
                        className={`h-10 w-10 shrink-0 rounded-xl flex items-center justify-center font-bold font-mono text-sm shadow-sm ${
                          isConcluido
                            ? "bg-green-600 text-white"
                            : isDisponivel
                            ? "bg-primary text-primary-foreground animate-pulse"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {isConcluido ? (
                          <CheckCircle2 className="h-5 w-5" />
                        ) : isBloqueado ? (
                          <Lock className="h-4 w-4" />
                        ) : (
                          etapa.numero
                        )}
                      </div>

                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono text-muted-foreground uppercase font-semibold">
                            Módulo {etapa.numero}
                          </span>
                          {isConcluido && (
                            <Badge className="bg-green-600/10 text-green-700 text-[10px] py-0 border-green-600/20">
                              CONCLUÍDO
                            </Badge>
                          )}
                          {isDisponivel && (
                            <Badge className="bg-primary/10 text-primary text-[10px] py-0 border-primary/20">
                              PRÓXIMO A ESTUDAR
                            </Badge>
                          )}
                        </div>

                        <h3 className="text-base font-bold font-heading text-foreground">
                          {etapa.titulo}
                        </h3>

                        {/* Detalhes de Performance pós-conclusão (Requisito Oficial) */}
                        {isConcluido && etapa.resultado && (
                          <div className="flex items-center gap-3 text-xs text-muted-foreground pt-1">
                            <span className="font-semibold text-foreground">
                              Acertos: {etapa.resultado.acertos} de {etapa.resultado.total}
                            </span>
                            <span>·</span>
                            <span className="text-green-600 font-semibold">
                              Feedback: {etapa.resultado.feedback === "util" ? "Útil 👍" : "Pode melhorar"}
                            </span>
                          </div>
                        )}

                        {isDisponivel && (
                          <p className="text-xs text-muted-foreground">
                            Formatos disponíveis nesta etapa: <strong>Tutorial</strong>, <strong>Flashcards 3D</strong> e <strong>Quiz Interativo</strong>.
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Botões de Ação */}
                    <div className="shrink-0 flex items-center gap-2">
                      {isConcluido && (
                        <Link to={"/conteudo" as any}>
                          <Button variant="outline" size="sm" className="gap-1.5 text-xs">
                            <RotateCcw className="h-3.5 w-3.5" />
                            <span>Rever</span>
                          </Button>
                        </Link>
                      )}
                      {isDisponivel && (
                        <Link to={"/conteudo" as any}>
                          <Button size="sm" className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90 text-xs shadow-md font-bold px-4">
                            <Play className="h-3.5 w-3.5 fill-current" />
                            <span>Estudar Agora</span>
                          </Button>
                        </Link>
                      )}
                      {isBloqueado && (
                        <Button variant="ghost" size="sm" disabled className="text-xs text-muted-foreground gap-1">
                          <Lock className="h-3.5 w-3.5" />
                          <span>Bloqueado</span>
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Coluna da Direita: Painel Lateral de Progresso e Metadados */}
        <div className="space-y-6">
          <Card className="border-border bg-card shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-heading">
                Status da Sua Trilha
              </CardTitle>
              <CardDescription className="text-xs">
                Resumo pedagógico e ancoragem técnica
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Progresso do Curso</span>
                  <span className="font-mono font-bold text-primary">{curso.progresso_percentual}%</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-500"
                    style={{ width: `${curso.progresso_percentual}%` }}
                  />
                </div>
              </div>

              {/* Conceitos Chave */}
              <div className="space-y-2 pt-2 border-t border-border/60">
                <p className="text-xs font-semibold text-foreground">Conceitos-Chave Deste Curso:</p>
                <div className="flex flex-wrap gap-1.5">
                  {curso.metadados.conceitos_chave.map((c) => (
                    <Badge key={c} variant="secondary" className="text-[11px] font-mono">
                      {c}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Informações de Documento & OCI */}
              <div className="rounded-lg border border-border/80 bg-muted/20 p-3 space-y-1.5 text-xs">
                <div className="flex items-center gap-1.5 text-primary font-bold">
                  <BookOpen className="h-3.5 w-3.5" />
                  <span>Documento Fonte:</span>
                </div>
                <p className="font-mono text-muted-foreground truncate">
                  {curso.documento_origem}
                </p>
                <p className="text-[10px] text-muted-foreground">
                  Persistido no bucket <code>novamente-conteudos-educativos</code> (OCI Always Free).
                </p>
              </div>
            </CardContent>

            <CardFooter className="border-t border-border pt-4">
              <Link to={"/conteudo" as any} className="w-full">
                <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90 gap-2">
                  <span>Ir para Conteúdo Ativo</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  )
}
