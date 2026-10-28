import { useState } from "react"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import {
  FileText,
  CheckCircle2,
  ChevronRight,
  ChevronLeft,
  Sparkles,
  Brain,
  HelpCircle,
  FileUp,
  ShieldCheck,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import type { FormatoPedagogico, NichoSetor, PerfilDestinatario } from "@/types/course"
import { mockTemasSugeridos } from "@/data/mockCourses"

export const Route = createFileRoute("/_layout/novo-curso")({
  component: NovoCursoWizard,
  head: () => ({
    meta: [
      {
        title: "Novo Curso — Wizard em 4 Etapas | NovaMente",
      },
    ],
  }),
})

const passosWizard = [
  { numero: 1, titulo: "Materiais Base", subtitulo: "Documentos e referências" },
  { numero: 2, titulo: "Nivelamento", subtitulo: "Conhecimento prévio" },
  { numero: 3, titulo: "Público & Nicho", subtitulo: "Perfil e contexto" },
  { numero: 4, titulo: "Formato & Gerar", subtitulo: "Didática da trilha" },
]

function NovoCursoWizard() {
  const navigate = useNavigate()
  const [passoAtual, setPassoAtual] = useState(1)

  // Estado do formulário
  const [titulo, setTitulo] = useState("")
  const [arquivo, setArquivo] = useState<File | null>(null)
  const [temaSelecionadoId, setTemaSelecionadoId] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)

  // Passo 2: Nivelamento
  const [nivelamentoExp, setNivelamentoExp] = useState<"nenhuma" | "basica" | "avancada">("basica")

  // Passo 3: Perfil e Nicho
  const [perfil, setPerfil] = useState<PerfilDestinatario>("Iniciante")
  const [nicho, setNicho] = useState<NichoSetor>("Geral")

  // Passo 4: Formato e Geração
  const [formato, setFormato] = useState<FormatoPedagogico>("Tutorial")
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationStep, setGenerationStep] = useState("")

  // Drag and drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      setArquivo(file)
      if (!titulo) setTitulo(file.name.replace(/\.[^/.]+$/, ""))
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      setArquivo(file)
      if (!titulo) setTitulo(file.name.replace(/\.[^/.]+$/, ""))
    }
  }

  // Envio via FormData (Observação de Joel)
  const handleGerarCurso = async () => {
    setIsGenerating(true)
    setGenerationStep("1/4: Ingerindo e validando documento técnico...")

    // Simulação do pipeline assíncrono do RAG integrado à OCI
    await new Promise((r) => setTimeout(r, 700))
    setGenerationStep("2/4: Chunking e geração de embeddings vetoriais...")

    await new Promise((r) => setTimeout(r, 800))
    setGenerationStep("3/4: Orquestrando agentes de IA para adaptação didática...")

    await new Promise((r) => setTimeout(r, 700))
    setGenerationStep("4/4: Persistindo pacote educacional no OCI Object Storage...")

    await new Promise((r) => setTimeout(r, 600))
    setIsGenerating(false)

    // Redireciona para o Roadmap da trilha gerada
    navigate({ to: "/roadmap" as any })
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Cabeçalho do Wizard */}
      <div className="text-center space-y-2">
        <Badge variant="outline" className="border-primary/30 text-primary font-mono text-xs">
          CRIAÇÃO ASSISTIDA POR IA · OCI ALWAYS FREE
        </Badge>
        <h1 className="text-3xl font-bold font-heading tracking-tight text-foreground">
          Gerar Novo Curso Personalizado
        </h1>
        <p className="text-sm text-muted-foreground max-w-xl mx-auto">
          Ingira manuais, documentações ou selecione um tema técnico. Nossa IA adaptará o conteúdo ao seu nível.
        </p>
      </div>

      {/* Stepper Visual (Passos 1 a 4) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {passosWizard.map((passo) => {
          const isAtivo = passo.numero === passoAtual
          const isConcluido = passo.numero < passoAtual
          return (
            <div
              key={passo.numero}
              className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${
                isAtivo
                  ? "border-primary bg-accent/40 shadow-sm"
                  : isConcluido
                  ? "border-green-600/30 bg-muted/40"
                  : "border-border bg-card opacity-60"
              }`}
            >
              <div
                className={`h-8 w-8 rounded-lg flex items-center justify-center font-bold font-mono text-xs ${
                  isAtivo
                    ? "bg-primary text-primary-foreground"
                    : isConcluido
                    ? "bg-green-600 text-white"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {isConcluido ? <CheckCircle2 className="h-4 w-4" /> : passo.numero}
              </div>
              <div className="leading-tight overflow-hidden text-left">
                <p className="text-xs font-bold text-foreground truncate">{passo.titulo}</p>
                <p className="text-[10px] text-muted-foreground truncate">{passo.subtitulo}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Conteúdo do Passo Ativo */}
      <Card className="border-border shadow-sm">
        {/* PASSO 1: Materiais Base & Upload FormData */}
        {passoAtual === 1 && (
          <>
            <CardHeader>
              <CardTitle className="text-lg font-heading">
                Etapa 1: Forneça a Documentação Técnica
              </CardTitle>
              <CardDescription className="text-xs">
                Faça upload de manuais em PDF, arquivos Markdown ou selecione um tema pronto.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* Título do Curso */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Título da Trilha ou Tecnologia
                </label>
                <Input
                  value={titulo}
                  onChange={(e) => setTitulo(e.target.value)}
                  placeholder="Ex: Introdução à Arquitetura de Redes VCN na OCI"
                  className="text-sm"
                />
              </div>

              {/* Área Drag-and-Drop (Upload FormData) */}
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
                  dragActive
                    ? "border-primary bg-accent/30"
                    : arquivo
                    ? "border-green-600/50 bg-green-50/10"
                    : "border-border hover:border-primary/50 bg-muted/20"
                }`}
                onClick={() => document.getElementById("file-upload")?.click()}
              >
                <input
                  id="file-upload"
                  type="file"
                  accept=".pdf,.md,.txt"
                  className="hidden"
                  onChange={handleFileInput}
                />

                {arquivo ? (
                  <div className="flex flex-col items-center justify-center space-y-2">
                    <div className="h-12 w-12 rounded-full bg-green-600/10 text-green-600 flex items-center justify-center">
                      <FileText className="h-6 w-6" />
                    </div>
                    <p className="text-sm font-bold text-foreground">{arquivo.name}</p>
                    <p className="text-xs text-muted-foreground font-mono">
                      {(arquivo.size / 1024).toFixed(1)} KB · Arquivo pronto para upload multipart
                    </p>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs text-destructive hover:bg-destructive/10 h-7"
                      onClick={(e) => {
                        e.stopPropagation()
                        setArquivo(null)
                      }}
                    >
                      Remover arquivo
                    </Button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center space-y-2">
                    <div className="h-12 w-12 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                      <FileUp className="h-6 w-6" />
                    </div>
                    <p className="text-sm font-semibold text-foreground">
                      Arraste e solte o documento técnico aqui
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Suporta arquivos <strong>PDF (.pdf)</strong>, <strong>Markdown (.md)</strong> ou texto puro
                    </p>
                    <Button variant="outline" size="sm" className="mt-2 text-xs">
                      Procurar arquivo no computador
                    </Button>
                  </div>
                )}
              </div>

              {/* Temas Sugeridos Alternativos */}
              <div className="space-y-2">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider font-mono">
                  Ou selecione um tema técnico pré-indexado:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
                  {mockTemasSugeridos.map((tema) => (
                    <button
                      key={tema.id}
                      type="button"
                      onClick={() => {
                        setTemaSelecionadoId(tema.id)
                        setTitulo(tema.titulo)
                        setArquivo(null)
                      }}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        temaSelecionadoId === tema.id
                          ? "border-primary bg-accent/40 ring-1 ring-primary"
                          : "border-border bg-card hover:border-primary/40"
                      }`}
                    >
                      <p className="text-xs font-bold text-foreground leading-tight">{tema.titulo}</p>
                      <p className="text-[10px] text-muted-foreground font-mono mt-1">{tema.categoria}</p>
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </>
        )}

        {/* PASSO 2: Nivelamento Opcional */}
        {passoAtual === 2 && (
          <>
            <CardHeader>
              <CardTitle className="text-lg font-heading">
                Etapa 2: Diagnóstico de Conhecimento Prévio
              </CardTitle>
              <CardDescription className="text-xs">
                Ajude nossa IA a calibrar a profundidade dos conceitos e evitar redundâncias. Esta etapa é opcional.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground">
                  Qual o seu nível de contato com este assunto?
                </label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {[
                    { id: "nenhuma", titulo: "Primeiro Contato", desc: "Nunca trabalhei com essa tecnologia; preciso de analogias didáticas do zero." },
                    { id: "basica", titulo: "Conhecimento Básico", desc: "Já li sobre ou executei comandos básicos, mas quero dominar a arquitetura." },
                    { id: "avancada", titulo: "Experiência Prática", desc: "Já utilizo em produção; foco em boas práticas, troubleshooting e otimização." },
                  ].map((opt) => (
                    <div
                      key={opt.id}
                      onClick={() => setNivelamentoExp(opt.id as any)}
                      className={`p-4 rounded-xl border cursor-pointer transition-all ${
                        nivelamentoExp === opt.id
                          ? "border-primary bg-accent/30 ring-1 ring-primary"
                          : "border-border hover:border-border/80 bg-card"
                      }`}
                    >
                      <p className="text-sm font-bold text-foreground">{opt.titulo}</p>
                      <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{opt.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-lg border border-border/60 bg-muted/20 p-3 text-xs text-muted-foreground flex items-center gap-2">
                <HelpCircle className="h-4 w-4 text-primary shrink-0" />
                <span>
                  Você pode pular esta etapa clicando em Continuar; o sistema usará a calibração padrão.
                </span>
              </div>
            </CardContent>
          </>
        )}

        {/* PASSO 3: Perfil do Destinatário & Nicho */}
        {passoAtual === 3 && (
          <>
            <CardHeader>
              <CardTitle className="text-lg font-heading">
                Etapa 3: Definição de Perfil e Contexto de Aplicação
              </CardTitle>
              <CardDescription className="text-xs">
                A IA reescreverá jargões técnicos para a linguagem ideal do seu perfil profissional.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-5">
              {/* Seleção de Perfil */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground">
                  Perfil do Destinatário
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {[
                    { id: "Iniciante", rotulo: "Iniciante / Transição de Carreira", desc: "Linguagem acolhedora com analogias do cotidiano e sem jargões desnecessários." },
                    { id: "Desenvolvedor Júnior", rotulo: "Desenvolvedor Júnior", desc: "Foco prático com exemplos de sintaxe e conceitos básicos de engenharia." },
                    { id: "Desenvolvedor Pleno", rotulo: "Desenvolvedor Pleno", desc: "Direto ao ponto com arquitetura interna, comandos e manifestos." },
                    { id: "Líder Técnico / Arquiteto", rotulo: "Líder Técnico / Arquiteto", desc: "Foco em trade-offs de desempenho, alta disponibilidade, custos e segurança." },
                    { id: "Gestor / Executivo (Não Técnico)", rotulo: "Gestor / Executivo (Não Técnico)", desc: "Visão executiva (TL;DR), impactos de negócio e governança." },
                  ].map((p) => (
                    <div
                      key={p.id}
                      onClick={() => setPerfil(p.id as PerfilDestinatario)}
                      className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                        perfil === p.id
                          ? "border-primary bg-accent/30 ring-1 ring-primary"
                          : "border-border bg-card hover:border-border/80"
                      }`}
                    >
                      <p className="text-xs font-bold text-foreground">{p.rotulo}</p>
                      <p className="text-[11px] text-muted-foreground mt-0.5">{p.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Nicho / Indústria */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground">
                  Nicho de Aplicação (Exemplos Contextualizados)
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {(["Geral", "Fintech", "Saúde", "E-commerce"] as NichoSetor[]).map((n) => (
                    <button
                      key={n}
                      type="button"
                      onClick={() => setNicho(n)}
                      className={`py-2 px-3 rounded-lg border text-xs font-semibold transition-all ${
                        nicho === n
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border bg-card text-foreground hover:bg-muted"
                      }`}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </>
        )}

        {/* PASSO 4: Formato Pedagógico e Disparo da IA */}
        {passoAtual === 4 && (
          <>
            <CardHeader>
              <CardTitle className="text-lg font-heading">
                Etapa 4: Formato Pedagógico & Geração da Trilha
              </CardTitle>
              <CardDescription className="text-xs">
                Escolha o formato principal de saída (na Tela 5 você poderá alternar entre eles dinamicamente).
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {[
                  {
                    id: "Tutorial",
                    titulo: "Guia Prático (Tutorial)",
                    desc: "Passo a passo didático com formatação Markdown e blocos de código.",
                  },
                  {
                    id: "Flashcards",
                    titulo: "Flashcards 3D de Memorização",
                    desc: "Cartões interativos com frente, verso e dicas mnemônicas para repetição espaçada.",
                  },
                  {
                    id: "Quiz",
                    titulo: "Quiz Interativo Avaliativo",
                    desc: "Questões com score em tempo real e justificativa técnica baseada na documentação.",
                  },
                ].map((f) => (
                  <div
                    key={f.id}
                    onClick={() => setFormato(f.id as FormatoPedagogico)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      formato === f.id
                        ? "border-primary bg-accent/30 ring-1 ring-primary"
                        : "border-border bg-card hover:border-border/80"
                    }`}
                  >
                    <p className="text-sm font-bold text-foreground">{f.titulo}</p>
                    <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{f.desc}</p>
                  </div>
                ))}
              </div>

              {/* Card Resumo do que será gerado */}
              <div className="rounded-xl border border-border bg-muted/20 p-4 space-y-2 text-xs">
                <p className="font-bold text-foreground flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-green-600" />
                  Garantias de Qualidade & OCI Always Free:
                </p>
                <ul className="list-disc list-inside text-muted-foreground space-y-1">
                  <li>Pipeline de RAG ancorada em Vector Store com mitigação ativa de alucinações;</li>
                  <li>Persistência automática do pacote didático em bucket Always Free do OCI Object Storage;</li>
                  <li>Geração simultânea do pacote multiformato (Tutorial + Flashcards + Quiz).</li>
                </ul>
              </div>

              {/* Loading State durante geração */}
              {isGenerating && (
                <div className="rounded-xl border border-primary/40 bg-accent/40 p-5 text-center space-y-3 animate-pulse">
                  <Brain className="h-8 w-8 mx-auto text-primary animate-spin" />
                  <p className="font-bold text-sm text-foreground">
                    Gerando Trilha Inteligente com RAG & LLM
                  </p>
                  <p className="text-xs text-muted-foreground font-mono">
                    {generationStep}
                  </p>
                </div>
              )}
            </CardContent>
          </>
        )}

        {/* Rodapé com Navegação Voltar / Continuar */}
        <CardFooter className="border-t border-border bg-muted/10 p-4 flex items-center justify-between">
          <Button
            variant="ghost"
            disabled={passoAtual === 1 || isGenerating}
            onClick={() => setPassoAtual((p) => p - 1)}
            className="gap-1.5 text-xs"
          >
            <ChevronLeft className="h-4 w-4" />
            <span>Voltar</span>
          </Button>

          {passoAtual < 4 ? (
            <Button
              onClick={() => setPassoAtual((p) => p + 1)}
              disabled={passoAtual === 1 && !titulo && !arquivo}
              className="gap-1.5 text-xs bg-primary text-primary-foreground hover:bg-primary/90"
            >
              <span>Continuar</span>
              <ChevronRight className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              onClick={handleGerarCurso}
              disabled={isGenerating}
              className="gap-2 text-xs bg-primary text-primary-foreground hover:bg-primary/90 shadow-md font-bold px-6"
            >
              <Sparkles className="h-4 w-4" />
              <span>{isGenerating ? "Processando..." : "Gerar Curso com IA"}</span>
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  )
}
