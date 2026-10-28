import { createFileRoute, Link } from "@tanstack/react-router"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts"
import {
  TrendingUp,
  Clock,
  BookOpen,
  CheckCircle2,
  RotateCcw,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { mockDashboardData } from "@/data/mockCourses"

export const Route = createFileRoute("/_layout/dashboard")({
  component: DashboardPage,
  head: () => ({
    meta: [
      {
        title: "Dashboard de Desempenho — NovaMente (RAG OCI)",
      },
    ],
  }),
})

function DashboardPage() {
  const data = mockDashboardData

  return (
    <div className="space-y-8 pb-16">
      {/* 1. Header do Dashboard */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline" className="font-mono text-xs text-primary border-primary/30">
              MÉTRICAS & EVOLUÇÃO
            </Badge>
          </div>
          <h1 className="text-3xl font-bold font-heading text-foreground">
            Painel de Desempenho do Estudante
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Acompanhe o ritmo de aprendizagem, retenção e histórico dos cursos adaptados por IA.
          </p>
        </div>

        <Link to={"/novo-curso" as any}>
          <Button className="bg-primary text-primary-foreground hover:bg-primary/90 text-xs shadow-md">
            Gerar Mais Conteúdo
          </Button>
        </Link>
      </div>

      {/* 2. Top KPIs Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-5 border-border bg-card">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold">Taxa de Finalização</span>
            <TrendingUp className="h-4 w-4 text-primary" />
          </div>
          <p className="text-3xl font-bold font-heading text-primary mt-2">
            {data.taxa_finalizacao_percentual}%
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">
            +15% em relação à semana passada
          </p>
        </Card>

        <Card className="p-5 border-border bg-card">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold">Cursos Gerados</span>
            <BookOpen className="h-4 w-4 text-foreground" />
          </div>
          <p className="text-3xl font-bold font-heading text-foreground mt-2">
            {data.cursos_gerados}
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">
            Adaptados a partir de documentações
          </p>
        </Card>

        <Card className="p-5 border-border bg-card">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold">Cursos Concluídos</span>
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          </div>
          <p className="text-3xl font-bold font-heading text-green-600 mt-2">
            {data.cursos_concluidos}
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">
            Trilhas finalizadas com aproveitamento
          </p>
        </Card>

        <Card className="p-5 border-border bg-card">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold">Tempo de Estudo</span>
            <Clock className="h-4 w-4 text-foreground" />
          </div>
          <p className="text-3xl font-bold font-heading text-foreground mt-2">
            {data.tempo_total_estudo_minutos} min
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">
            Média de 16 min por trilha didática
          </p>
        </Card>
      </div>

      {/* 3. Gráficos Analíticos com Recharts (Observação de Joel) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico 1: Evolução Semanal */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-heading">
              Evolução Semanal de Estudos
            </CardTitle>
            <CardDescription className="text-xs">
              Módulos lidos e respostas a quizzes nos últimos 30 dias
            </CardDescription>
          </CardHeader>
          <CardContent className="h-64 pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.evolucao_semanal}>
                <defs>
                  <linearGradient id="colorEstudos" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F26B21" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#F26B21" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#D5D9D2" opacity={0.5} />
                <XAxis dataKey="semana" stroke="#555B66" fontSize={11} />
                <YAxis stroke="#555B66" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#FFFFFF",
                    borderColor: "#D5D9D2",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="quizzes_respondidos"
                  name="Quizzes Respondidos"
                  stroke="#F26B21"
                  fillOpacity={1}
                  fill="url(#colorEstudos)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Gráfico 2: Distribuição por Temas Técnicos */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-heading">
              Distribuição por Tema Técnico
            </CardTitle>
            <CardDescription className="text-xs">
              Quantidade de trilhas criadas por categoria de tecnologia
            </CardDescription>
          </CardHeader>
          <CardContent className="h-64 pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.distribuicao_temas}>
                <CartesianGrid strokeDasharray="3 3" stroke="#D5D9D2" opacity={0.5} />
                <XAxis dataKey="tema" stroke="#555B66" fontSize={11} />
                <YAxis stroke="#555B66" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#FFFFFF",
                    borderColor: "#D5D9D2",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="quantidade" name="Trilhas Geradas" fill="#11151C" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 4. Tabela de Histórico de Cursos */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-3 border-b border-border/60">
          <CardTitle className="text-base font-heading">
            Histórico Completo de Cursos
          </CardTitle>
          <CardDescription className="text-xs">
            Todos os treinamentos gerados pela IA e seus respectivos resultados
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-muted/40 border-b border-border text-muted-foreground uppercase font-mono text-[10px]">
                <tr>
                  <th className="px-5 py-3 font-semibold">Curso / Trilha</th>
                  <th className="px-4 py-3 font-semibold">Formato Principal</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold">Score / Aproveitamento</th>
                  <th className="px-5 py-3 font-semibold text-right">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.historico_recente.map((item) => (
                  <tr key={item.id} className="hover:bg-muted/20 transition-colors">
                    <td className="px-5 py-3.5 font-semibold text-foreground">
                      {item.curso_titulo}
                    </td>
                    <td className="px-4 py-3.5 text-muted-foreground">
                      {item.formato}
                    </td>
                    <td className="px-4 py-3.5">
                      <Badge
                        variant={item.status === "Concluído" ? "outline" : "secondary"}
                        className={`text-[10px] ${
                          item.status === "Concluído"
                            ? "text-green-700 border-green-600/30 bg-green-500/10"
                            : "text-primary border-primary/30"
                        }`}
                      >
                        {item.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3.5 font-mono font-bold text-foreground">
                      {item.score ? `${item.score}%` : "Em progresso"}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <Link to={"/roadmap" as any}>
                        <Button variant="ghost" size="sm" className="h-7 text-xs gap-1 text-primary hover:text-primary">
                          <RotateCcw className="h-3 w-3" />
                          <span>Rever</span>
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
