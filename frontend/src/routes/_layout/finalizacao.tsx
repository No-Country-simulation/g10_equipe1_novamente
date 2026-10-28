import { useState } from "react"
import { createFileRoute, Link } from "@tanstack/react-router"
import {
  Trophy,
  Star,
  CheckCircle2,
  Sparkles,
  Home,
  BarChart3,
  PlusCircle,
  Award,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { mockCursos } from "@/data/mockCourses"

export const Route = createFileRoute("/_layout/finalizacao")({
  component: FinalizacaoPage,
  head: () => ({
    meta: [
      {
        title: "Conclusão de Curso — Parabéns! | NovaMente",
      },
    ],
  }),
})

function FinalizacaoPage() {
  const curso = mockCursos[0]

  const [notaEstrelas, setNotaEstrelas] = useState(5)
  const [comentario, setComentario] = useState("")
  const [feedbackSalvo, setFeedbackSalvo] = useState(false)

  const handleSalvarFeedback = (e: React.FormEvent) => {
    e.preventDefault()
    setFeedbackSalvo(true)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8 pb-20 text-center">
      {/* 1. Celebração e Troféu */}
      <div className="space-y-4 pt-4">
        <div className="relative inline-flex items-center justify-center">
          <div className="h-24 w-24 rounded-full bg-primary/10 text-primary flex items-center justify-center shadow-lg ring-8 ring-primary/5 animate-bounce">
            <Trophy className="h-12 w-12 text-primary" />
          </div>
          <Sparkles className="h-6 w-6 text-primary absolute -top-1 -right-1" />
        </div>

        <div>
          <Badge variant="outline" className="font-mono text-xs text-green-700 border-green-600/30 bg-green-500/10 mb-2">
            TRILHA 100% CONCLUÍDA
          </Badge>
          <h1 className="text-3xl font-bold font-heading text-foreground">
            Parabéns! Você Concluiu o Treinamento!
          </h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-md mx-auto">
            Você dominou os conceitos de <strong className="text-foreground">{curso.titulo}</strong> com adaptação didática por IA.
          </p>
        </div>
      </div>

      {/* 2. Resumo das Conquistas */}
      <Card className="border-border bg-card text-left">
        <CardHeader className="pb-3 border-b border-border/60">
          <CardTitle className="text-base font-heading flex items-center gap-2">
            <Award className="h-4 w-4 text-primary" />
            Resumo do Pacote Didático Concluído
          </CardTitle>
        </CardHeader>
        <CardContent className="p-5 space-y-3 text-xs">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="p-3 rounded-lg bg-muted/30 border border-border/60">
              <span className="text-muted-foreground font-semibold">Módulos Concluídos</span>
              <p className="text-base font-bold font-mono text-foreground mt-0.5">4 de 4 (100%)</p>
            </div>
            <div className="p-3 rounded-lg bg-muted/30 border border-border/60">
              <span className="text-muted-foreground font-semibold">Perfil Aplicado</span>
              <p className="text-base font-bold font-heading text-foreground mt-0.5">{curso.metadados.perfil_aplicado}</p>
            </div>
            <div className="p-3 rounded-lg bg-muted/30 border border-border/60">
              <span className="text-muted-foreground font-semibold">Tempo Dedicado</span>
              <p className="text-base font-bold font-mono text-foreground mt-0.5">{curso.metadados.tempo_estimado_estudo_minutos} minutos</p>
            </div>
          </div>

          <div className="rounded-lg bg-accent/20 border border-primary/20 p-3 text-xs flex items-center gap-2 text-foreground">
            <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
            <span>
              Certificado e metadados persistidos no OCI Object Storage Always Free.
            </span>
          </div>
        </CardContent>
      </Card>

      {/* 3. Avaliação por Estrelas e Feedback da Trilha */}
      <Card className="border-border bg-card text-left">
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-heading">
            Avalie esta Trilha Didática
          </CardTitle>
          <CardDescription className="text-xs">
            Seu feedback ajuda a calibrar os prompts de RAG da equipe.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {feedbackSalvo ? (
            <div className="py-4 text-center space-y-1">
              <p className="text-sm font-bold text-green-600">✓ Obrigado pelo seu feedback!</p>
              <p className="text-xs text-muted-foreground">Avaliação registrada com sucesso.</p>
            </div>
          ) : (
            <form onSubmit={handleSalvarFeedback} className="space-y-4">
              <div className="flex items-center gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setNotaEstrelas(star)}
                    className="p-1 hover:scale-110 transition-transform"
                  >
                    <Star
                      className={`h-6 w-6 ${
                        star <= notaEstrelas
                          ? "fill-primary text-primary"
                          : "text-muted-foreground"
                      }`}
                    />
                  </button>
                ))}
                <span className="text-xs font-mono font-bold text-muted-foreground ml-2">
                  {notaEstrelas} de 5 estrelas
                </span>
              </div>

              <textarea
                value={comentario}
                onChange={(e) => setComentario(e.target.value)}
                placeholder="Comentário opcional (ex: As analogias facilitaram a compreensão de CIDR...)"
                rows={2}
                className="w-full rounded-md border border-input bg-background p-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              />

              <Button type="submit" size="sm" variant="outline" className="text-xs">
                Enviar Avaliação
              </Button>
            </form>
          )}
        </CardContent>
      </Card>

      {/* 4. Os 3 CTAs Finais de Saída (Requisito Oficial) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
        <Link to="/" className="w-full">
          <Button variant="outline" className="w-full gap-2 text-xs py-5">
            <Home className="h-4 w-4" />
            <span>Voltar ao Início</span>
          </Button>
        </Link>
        <Link to={"/dashboard" as any} className="w-full">
          <Button variant="outline" className="w-full gap-2 text-xs py-5">
            <BarChart3 className="h-4 w-4" />
            <span>Ver no Dashboard</span>
          </Button>
        </Link>
        <Link to={"/novo-curso" as any} className="w-full">
          <Button className="w-full gap-2 text-xs py-5 bg-primary text-primary-foreground hover:bg-primary/90 font-bold shadow-md">
            <PlusCircle className="h-4 w-4" />
            <span>Novo Treinamento</span>
          </Button>
        </Link>
      </div>
    </div>
  )
}
