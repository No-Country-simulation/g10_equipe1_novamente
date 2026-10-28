import { createFileRoute, Link } from "@tanstack/react-router"
import {
  PlusCircle,
  Play,
  Clock,
  Sparkles,
  ArrowRight,
  BarChart3,
  BookOpen,
  ChevronRight,
} from "lucide-react"

import useAuth from "@/hooks/useAuth"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { mockCursos, mockTemasSugeridos, mockDashboardData } from "@/data/mockCourses"

export const Route = createFileRoute("/_layout/")({
  component: HomePage,
  head: () => ({
    meta: [
      {
        title: "Início — NovaMente (RAG Educacional OCI)",
      },
    ],
  }),
})

function HomePage() {
  const { user: currentUser } = useAuth()
  const nomeExibicao = currentUser?.full_name?.split(" ")[0] || "Karina"
  const cursoAtivo = mockCursos.find((c) => c.status === "em_andamento") || mockCursos[0]

  return (
    <div className="space-y-8 pb-12">
      {/* 1. Hero Section & Boas-Vindas */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-accent/60 text-primary text-xs font-semibold mb-2">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Sistema Adaptativo de Aprendizagem Técnica</span>
          </div>
          <h1 className="text-3xl font-bold font-heading tracking-tight text-foreground">
            Olá, {nomeExibicao}! 👋
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Qual documentação ou tecnologia você deseja dominar hoje?
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link to={"/dashboard" as any}>
            <Button variant="outline" className="gap-2">
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
              <span>Ver Desempenho</span>
            </Button>
          </Link>
          <Link to={"/novo-curso" as any}>
            <Button className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90 shadow-md">
              <PlusCircle className="h-4 w-4" />
              <span>Gerar Novo Curso</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* 2. Card de Treinamento Recente / Em Andamento */}
      {cursoAtivo && (
        <Card className="border-border bg-card shadow-sm overflow-hidden">
          <div className="h-1.5 w-full bg-primary" />
          <CardHeader className="pb-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="border-primary/30 text-primary font-mono text-xs">
                  EM ANDAMENTO
                </Badge>
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {cursoAtivo.metadados.tempo_estimado_estudo_minutos} min estimados
                </span>
                <span className="text-xs text-muted-foreground">·</span>
                <span className="text-xs text-muted-foreground">
                  Perfil: <strong>{cursoAtivo.metadados.perfil_aplicado}</strong>
                </span>
              </div>
              <span className="text-xs font-mono font-bold text-primary">
                {cursoAtivo.progresso_percentual}% CONCLUÍDO
              </span>
            </div>

            <CardTitle className="text-xl font-heading mt-2">
              {cursoAtivo.titulo}
            </CardTitle>
            <CardDescription className="text-sm">
              {cursoAtivo.descricao}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {/* Barra de Progresso */}
            <div className="w-full bg-secondary rounded-full h-2.5 overflow-hidden">
              <div
                className="bg-primary h-2.5 rounded-full transition-all duration-500"
                style={{ width: `${cursoAtivo.progresso_percentual}%` }}
              />
            </div>

            {/* Próxima etapa destacada */}
            <div className="rounded-xl border border-border/80 bg-muted/30 p-3.5 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold font-mono text-sm">
                  2
                </div>
                <div>
                  <p className="text-xs text-muted-foreground font-semibold">PRÓXIMA ETAPA DISPONÍVEL</p>
                  <p className="text-sm font-semibold text-foreground">
                    Etapa 2: Sub-redes e Roteamento Seguro
                  </p>
                </div>
              </div>
              <Link to={"/roadmap" as any}>
                <Button size="sm" className="gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90">
                  <Play className="h-3.5 w-3.5 fill-current" />
                  <span>Continuar</span>
                </Button>
              </Link>
            </div>
          </CardContent>

          <CardFooter className="border-t border-border/60 bg-muted/10 pt-3 flex items-center justify-between text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <BookOpen className="h-3.5 w-3.5 text-primary" />
              Documento base: <code className="font-mono text-foreground">{cursoAtivo.documento_origem}</code>
            </span>
            <Link to={"/roadmap" as any} className="text-primary hover:underline font-semibold flex items-center gap-1">
              Ver trilha completa <ChevronRight className="h-3.5 w-3.5" />
            </Link>
          </CardFooter>
        </Card>
      )}

      {/* 3. Métricas Rápidas de Desempenho (Mini KPIs) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4 border-border bg-card">
          <p className="text-xs font-semibold text-muted-foreground">Cursos Gerados</p>
          <p className="text-2xl font-bold font-heading mt-1 text-foreground">
            {mockDashboardData.cursos_gerados}
          </p>
          <p className="text-[11px] text-muted-foreground mt-0.5">Adaptados via RAG</p>
        </Card>
        <Card className="p-4 border-border bg-card">
          <p className="text-xs font-semibold text-muted-foreground">Cursos Concluídos</p>
          <p className="text-2xl font-bold font-heading mt-1 text-green-600">
            {mockDashboardData.cursos_concluidos}
          </p>
          <p className="text-[11px] text-muted-foreground mt-0.5">100% de aproveitamento</p>
        </Card>
        <Card className="p-4 border-border bg-card">
          <p className="text-xs font-semibold text-muted-foreground">Taxa de Finalização</p>
          <p className="text-2xl font-bold font-heading mt-1 text-primary">
            {mockDashboardData.taxa_finalizacao_percentual}%
          </p>
          <p className="text-[11px] text-muted-foreground mt-0.5">+15% essa semana</p>
        </Card>
        <Card className="p-4 border-border bg-card">
          <p className="text-xs font-semibold text-muted-foreground">Tempo Dedicado</p>
          <p className="text-2xl font-bold font-heading mt-1 text-foreground">
            {mockDashboardData.tempo_total_estudo_minutos} min
          </p>
          <p className="text-[11px] text-muted-foreground mt-0.5">Estudo ativo e quizzes</p>
        </Card>
      </div>

      {/* 4. Sugestões de Temas Prontos para Iniciar */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold font-heading text-foreground">
              Temas Técnicos em Destaque
            </h2>
            <p className="text-xs text-muted-foreground">
              Selecione uma documentação pré-processada para gerar uma trilha instantânea
            </p>
          </div>
          <Link to={"/novo-curso" as any} className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
            Enviar arquivo próprio <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {mockTemasSugeridos.map((tema) => (
            <Card key={tema.id} className="border-border hover:border-primary/50 transition-all hover:shadow-md flex flex-col justify-between">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between text-xs mb-1">
                  <Badge variant="secondary" className="text-[10px] font-mono">
                    {tema.categoria}
                  </Badge>
                  <span className="text-muted-foreground font-mono text-[11px]">
                    {tema.duracao_estimada}
                  </span>
                </div>
                <CardTitle className="text-base font-heading">
                  {tema.titulo}
                </CardTitle>
                <CardDescription className="text-xs line-clamp-2 mt-1">
                  {tema.descricao}
                </CardDescription>
              </CardHeader>
              <CardFooter className="pt-0">
                <Link to={"/novo-curso" as any} className="w-full">
                  <Button variant="outline" size="sm" className="w-full text-xs gap-1.5 hover:bg-primary hover:text-primary-foreground group">
                    <span>Estudar este tema</span>
                    <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-1" />
                  </Button>
                </Link>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
