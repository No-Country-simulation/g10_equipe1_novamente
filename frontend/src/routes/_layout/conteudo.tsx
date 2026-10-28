import { useState } from "react"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import {
  BookOpen,
  Layers,
  HelpCircle,
  FileDown,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  RotateCw,
  Sparkles,
  Download,
  ThumbsUp,
  ThumbsDown,
  ArrowRight,
  Code2,
  FileText,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { mockCursos } from "@/data/mockCourses"
import {
  exportarElementoParaPdf,
  exportarFlashcardsParaAnki,
  exportarTutorialParaMarkdown,
} from "@/services/exportService"

export const Route = createFileRoute("/_layout/conteudo")({
  component: ConteudoPage,
  head: () => ({
    meta: [
      {
        title: "Ambiente de Estudo Interativo — NovaMente",
      },
    ],
  }),
})

function ConteudoPage() {
  const navigate = useNavigate()
  const curso = mockCursos[0]
  const etapa = curso.etapas[0] // Módulo com pacote multiformato completo
  const conteudo = etapa.conteudo!

  // Formato ativo na aba (Observação de Joel: Tutorial, Flashcard, Quiz)
  const [activeTab, setActiveTab] = useState<"tutorial" | "flashcards" | "quiz">("tutorial")

  // Estado dos Flashcards
  const [currentCardIdx, setCurrentCardIdx] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)

  // Estado do Quiz
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, number>>({})
  const [submittedQuiz, setSubmittedQuiz] = useState<Record<string, boolean>>({})

  // Estado de Avaliação da Etapa
  const [feedback, setFeedback] = useState<"util" | "pode_melhorar" | null>(null)
  const [etapaConcluida, setEtapaConcluida] = useState(false)

  const flashcards = conteudo.itens_flashcards || []
  const currentCard = flashcards[currentCardIdx]
  const quizQuestoes = conteudo.questoes_quiz || []
  const tutorialSecoes = conteudo.secoes_tutorial || []

  const handleSelectQuizOption = (questaoId: string, opcaoIdx: number) => {
    if (submittedQuiz[questaoId]) return
    setSelectedAnswers((prev) => ({ ...prev, [questaoId]: opcaoIdx }))
    setSubmittedQuiz((prev) => ({ ...prev, [questaoId]: true }))
  }

  const handleExportPdf = () => {
    exportarElementoParaPdf("printable-study-content", `${curso.titulo}_etapa_${etapa.numero}`)
  }

  const handleExportAnki = () => {
    exportarFlashcardsParaAnki(curso.titulo, flashcards)
  }

  const handleExportMarkdown = () => {
    exportarTutorialParaMarkdown(curso.titulo, tutorialSecoes)
  }

  const handleConcluirEtapa = () => {
    setEtapaConcluida(true)
    setTimeout(() => {
      navigate({ to: "/roadmap" as any })
    }, 800)
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-20">
      {/* 1. Barra Superior de Navegação & Exportação */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div className="flex items-center gap-3">
          <Link to={"/roadmap" as any}>
            <Button variant="ghost" size="sm" className="gap-1 text-xs">
              <ChevronLeft className="h-4 w-4" />
              <span>Voltar ao Roadmap</span>
            </Button>
          </Link>
          <span className="text-muted-foreground">·</span>
          <div>
            <span className="text-[10px] font-mono font-bold uppercase text-primary">
              Módulo {etapa.numero} de {curso.etapas.length}
            </span>
            <h1 className="text-lg font-bold font-heading text-foreground">
              {conteudo.titulo}
            </h1>
          </div>
        </div>

        {/* Utilitários de Exportação Didática */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportPdf}
            className="text-xs gap-1.5 hover:border-primary"
            title="Exportar conteúdo para PDF didático"
          >
            <FileDown className="h-3.5 w-3.5 text-primary" />
            <span>PDF</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleExportMarkdown}
            className="text-xs gap-1.5 hover:border-primary"
            title="Exportar tutorial em arquivo Markdown (.md)"
          >
            <FileText className="h-3.5 w-3.5 text-primary" />
            <span>Markdown</span>
          </Button>

          {flashcards.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportAnki}
              className="text-xs gap-1.5 hover:border-primary"
              title="Exportar flashcards compatíveis com Anki (CSV)"
            >
              <Download className="h-3.5 w-3.5 text-primary" />
              <span>Anki CSV</span>
            </Button>
          )}
        </div>
      </div>

      {/* Introdução Didática Contextualizada */}
      <div className="rounded-xl border border-border/80 bg-accent/20 p-4 text-xs text-foreground flex items-start gap-3">
        <Sparkles className="h-4 w-4 text-primary shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-bold text-primary font-heading text-sm">
            Contexto Adaptado para {curso.metadados.perfil_aplicado}:
          </p>
          <p className="text-muted-foreground leading-relaxed">
            {conteudo.introducao_contextualizada}
          </p>
        </div>
      </div>

      {/* 2. Abas Multiformato (Observação de Joel: Tutorial, Flashcard, Quiz) */}
      <div id="printable-study-content">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="space-y-6">
          <TabsList className="grid grid-cols-3 max-w-md mx-auto bg-muted/60 p-1 rounded-xl">
            <TabsTrigger value="tutorial" className="text-xs gap-1.5 py-2">
              <BookOpen className="h-3.5 w-3.5" />
              <span>Tutorial</span>
            </TabsTrigger>
            <TabsTrigger value="flashcards" className="text-xs gap-1.5 py-2">
              <Layers className="h-3.5 w-3.5" />
              <span>Flashcards 3D</span>
            </TabsTrigger>
            <TabsTrigger value="quiz" className="text-xs gap-1.5 py-2">
              <HelpCircle className="h-3.5 w-3.5" />
              <span>Quiz Interativo</span>
            </TabsTrigger>
          </TabsList>

          {/* TAB 1: Tutorial com react-markdown */}
          <TabsContent value="tutorial" className="space-y-6">
            <Card className="border-border bg-card">
              <CardContent className="p-6 space-y-8">
                {tutorialSecoes.map((sec) => (
                  <div key={sec.passo} className="space-y-3 pb-6 border-b border-border/60 last:border-none last:pb-0">
                    <div className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-mono font-bold">
                        {sec.passo}
                      </span>
                      <h3 className="text-base font-bold font-heading text-foreground">
                        {sec.titulo}
                      </h3>
                    </div>

                    <div className="text-sm text-foreground/90 leading-relaxed pl-8 prose dark:prose-invert max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {sec.conteudo_markdown}
                      </ReactMarkdown>
                    </div>

                    {sec.codigo_exemplo && (
                      <div className="pl-8 pt-2">
                        <div className="rounded-lg border border-border bg-muted/40 p-4 font-mono text-xs overflow-x-auto text-foreground">
                          <div className="flex items-center justify-between text-[11px] text-muted-foreground pb-2 border-b border-border/60 mb-2">
                            <span className="flex items-center gap-1">
                              <Code2 className="h-3 w-3 text-primary" />
                              Exemplo de Configuração ({sec.linguagem_codigo || "bash"})
                            </span>
                          </div>
                          <pre>{sec.codigo_exemplo}</pre>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* TAB 2: Flashcards 3D com Flip Interativo */}
          <TabsContent value="flashcards" className="space-y-6">
            {flashcards.length > 0 && currentCard ? (
              <div className="flex flex-col items-center space-y-6">
                <div className="flex items-center justify-between w-full max-w-md text-xs text-muted-foreground font-mono">
                  <span>Cartão {currentCardIdx + 1} de {flashcards.length}</span>
                  <span className="text-primary font-bold">Clique no cartão para girar ↺</span>
                </div>

                {/* Cartão 3D Interativo */}
                <div
                  onClick={() => setIsFlipped(!isFlipped)}
                  className="w-full max-w-md h-72 cursor-pointer perspective-1000 select-none"
                >
                  <div
                    className={`relative w-full h-full rounded-2xl border transition-all duration-500 shadow-md transform-style-3d ${
                      isFlipped
                        ? "border-primary/50 bg-accent/30 rotate-y-180"
                        : "border-border bg-card hover:border-primary/40"
                    }`}
                  >
                    {/* Frente do Card */}
                    <div className="absolute inset-0 p-8 flex flex-col justify-between backface-hidden">
                      <div className="flex items-center justify-between text-xs">
                        <Badge variant="outline" className="font-mono text-[10px] text-primary border-primary/30">
                          PERGUNTA
                        </Badge>
                        <RotateCw className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="text-center my-auto">
                        <p className="text-lg font-bold font-heading text-foreground leading-relaxed">
                          {currentCard.frente}
                        </p>
                      </div>
                      <p className="text-[11px] text-center text-muted-foreground">
                        Clique para virar e ver a resposta didática
                      </p>
                    </div>

                    {/* Verso do Card */}
                    <div className="absolute inset-0 p-8 flex flex-col justify-between rotate-y-180 backface-hidden">
                      <div className="flex items-center justify-between text-xs">
                        <Badge className="font-mono text-[10px] bg-primary text-primary-foreground">
                          RESPOSTA ANCORADA
                        </Badge>
                        <RotateCw className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="text-center my-auto space-y-3">
                        <p className="text-base text-foreground leading-relaxed font-medium">
                          {currentCard.verso}
                        </p>
                        {currentCard.dica_didatica && (
                          <div className="rounded-lg bg-background/80 p-2 text-xs text-primary border border-primary/20">
                            💡 <strong>Dica Mnemônica:</strong> {currentCard.dica_didatica}
                          </div>
                        )}
                      </div>
                      <p className="text-[11px] text-center text-muted-foreground">
                        Clique novamente para voltar à frente
                      </p>
                    </div>
                  </div>
                </div>

                {/* Controles de Navegação dos Flashcards */}
                <div className="flex items-center gap-3">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={currentCardIdx === 0}
                    onClick={() => {
                      setIsFlipped(false)
                      setCurrentCardIdx((i) => i - 1)
                    }}
                    className="gap-1"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    <span>Anterior</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={currentCardIdx === flashcards.length - 1}
                    onClick={() => {
                      setIsFlipped(false)
                      setCurrentCardIdx((i) => i + 1)
                    }}
                    className="gap-1"
                  >
                    <span>Próximo</span>
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ) : (
              <p className="text-center text-sm text-muted-foreground py-10">
                Nenhum flashcard disponível neste módulo.
              </p>
            )}
          </TabsContent>

          {/* TAB 3: Quiz Interativo com Avaliação em Tempo Real */}
          <TabsContent value="quiz" className="space-y-6">
            <div className="space-y-6">
              {quizQuestoes.map((q, qIdx) => {
                const userChoice = selectedAnswers[q.id]
                const isSubmetida = submittedQuiz[q.id]
                const acertou = isSubmetida && userChoice === q.resposta_correta_idx

                return (
                  <Card key={q.id} className="border-border bg-card">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <Badge variant="outline" className="font-mono text-[10px]">
                          QUESTÃO {qIdx + 1} DE {quizQuestoes.length}
                        </Badge>
                        {isSubmetida && (
                          <span
                            className={`font-bold font-mono text-xs ${
                              acertou ? "text-green-600" : "text-destructive"
                            }`}
                          >
                            {acertou ? "✓ RESPOSTA CORRETA" : "✗ RESPOSTA INCORRETA"}
                          </span>
                        )}
                      </div>
                      <CardTitle className="text-base font-heading">
                        {q.enunciado}
                      </CardTitle>
                    </CardHeader>

                    <CardContent className="space-y-2.5">
                      {q.opcoes.map((opcao, optIdx) => {
                        const isSelected = userChoice === optIdx
                        const isCorreta = q.resposta_correta_idx === optIdx

                        let buttonStyle = "border-border bg-card hover:border-primary/50 text-foreground"
                        if (isSubmetida) {
                          if (isCorreta) {
                            buttonStyle = "border-green-600 bg-green-500/10 text-green-700 font-semibold"
                          } else if (isSelected && !isCorreta) {
                            buttonStyle = "border-destructive bg-destructive/10 text-destructive font-semibold"
                          } else {
                            buttonStyle = "border-border/50 opacity-60 text-muted-foreground"
                          }
                        }

                        return (
                          <button
                            key={optIdx}
                            type="button"
                            onClick={() => handleSelectQuizOption(q.id, optIdx)}
                            className={`w-full p-3 rounded-xl border text-left text-xs transition-all flex items-center justify-between ${buttonStyle}`}
                          >
                            <span>{opcao}</span>
                            {isSubmetida && isCorreta && (
                              <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                            )}
                          </button>
                        )
                      })}

                      {/* Justificativa Técnica Oficial (Requisito Hackathon) */}
                      {isSubmetida && (
                        <div className="mt-3 rounded-lg border border-border/80 bg-muted/30 p-3 text-xs space-y-1">
                          <p className="font-bold text-foreground flex items-center gap-1.5">
                            <Sparkles className="h-3.5 w-3.5 text-primary" />
                            Justificativa Didática Fundamentada:
                          </p>
                          <p className="text-muted-foreground leading-relaxed">
                            {q.justificativa}
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* 3. Rodapé de Conclusão e Feedback da Etapa */}
      <div className="border-t border-border pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Feedback da Etapa */}
        <div className="flex items-center gap-3 text-xs">
          <span className="text-muted-foreground font-semibold">Este conteúdo foi didático?</span>
          <div className="flex items-center gap-1.5">
            <Button
              variant={feedback === "util" ? "default" : "outline"}
              size="sm"
              onClick={() => setFeedback("util")}
              className={`h-8 gap-1 text-xs ${feedback === "util" ? "bg-green-600 text-white" : ""}`}
            >
              <ThumbsUp className="h-3.5 w-3.5" />
              <span>Útil</span>
            </Button>
            <Button
              variant={feedback === "pode_melhorar" ? "default" : "outline"}
              size="sm"
              onClick={() => setFeedback("pode_melhorar")}
              className={`h-8 gap-1 text-xs ${feedback === "pode_melhorar" ? "bg-destructive text-white" : ""}`}
            >
              <ThumbsDown className="h-3.5 w-3.5" />
              <span>Pode melhorar</span>
            </Button>
          </div>
        </div>

        {/* Botão Concluir Etapa */}
        <Button
          onClick={handleConcluirEtapa}
          disabled={etapaConcluida}
          className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90 font-bold px-6 shadow-md"
        >
          <span>{etapaConcluida ? "Concluindo..." : "Concluir Etapa e Avançar"}</span>
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
