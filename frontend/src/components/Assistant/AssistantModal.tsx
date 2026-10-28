import { useState } from "react"
import {
  Brain,
  Send,
  X,
  AlertCircle,
  BookOpen,
  CheckCircle2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { mockAssistantFaqs } from "@/data/mockAssistantFaq"
import type { AssistantMessage } from "@/types/studyContent"

export function AssistantModal() {
  const [isOpen, setIsOpen] = useState(false)
  const [inputValue, setInputValue] = useState("")
  const [reportModalOpen, setReportModalOpen] = useState(false)
  const [reportSuccess, setReportSuccess] = useState(false)
  const [reportReason, setReportReason] = useState("")

  const [messages, setMessages] = useState<AssistantMessage[]>([
    {
      id: "msg-welcome",
      remetente: "assistente",
      texto: "Olá! Sou o Assistente NovaMente. Posso tirar dúvidas sobre os conteúdos técnicos, explicar conceitos de OCI e nuvem, ou ajudar com o uso da plataforma. Todas as minhas respostas são ancoradas com RAG nas fontes oficiais.",
      data_hora: "Agora",
      fontes: ["Base de Conhecimento NovaMente (RAG OCI)"],
    },
  ])

  const handleSendMessage = (textToSend?: string) => {
    const text = textToSend || inputValue
    if (!text.trim()) return

    const userMsg: AssistantMessage = {
      id: `user-${Date.now()}`,
      remetente: "usuario",
      texto: text,
      data_hora: "Agora",
    }

    setMessages((prev) => [...prev, userMsg])
    if (!textToSend) setInputValue("")

    // Simulação inteligente de resposta ancorada via RAG
    setTimeout(() => {
      const lower = text.toLowerCase()
      let resposta = "Com base na documentação técnica indexada, este tópico envolve a configuração e governança da infraestrutura em nuvem, garantindo segurança e aderência às melhores práticas."
      let fonte = "Documentação Técnica Oficial (OCI Always Free & NovaMente)"

      const matchedFaq = mockAssistantFaqs.find(
        (f) =>
          lower.includes(f.pergunta.toLowerCase().slice(0, 10)) ||
          lower.includes(f.categoria) ||
          (lower.includes("always free") && f.id === "faq-1") ||
          (lower.includes("alucina") && f.id === "faq-2") ||
          (lower.includes("anki") && f.id === "faq-3") ||
          (lower.includes("upload") && f.id === "faq-4")
      )

      if (matchedFaq) {
        resposta = matchedFaq.resposta
        fonte = matchedFaq.fonte_citada
      } else if (lower.includes("vcn") || lower.includes("rede")) {
        resposta = "A Virtual Cloud Network (VCN) é a rede virtual privada da OCI. Ela isola recursos através de sub-redes públicas e privadas, usando Security Lists para controlar regras de entrada e saída."
        fonte = "Oracle Cloud Infrastructure — Manual de Arquitetura de Redes VCN"
      } else if (lower.includes("kubernetes") || lower.includes("k8s")) {
        resposta = "O Kubernetes orquestra contêineres gerenciando o Control Plane (apiserver, etcd, scheduler) e os nós de trabalho que executam Kubelet e os Pods."
        fonte = "Kubernetes Core Concepts & Production Guide"
      }

      const botMsg: AssistantMessage = {
        id: `bot-${Date.now()}`,
        remetente: "assistente",
        texto: resposta,
        data_hora: "Agora",
        fontes: [fonte],
      }

      setMessages((prev) => [...prev, botMsg])
    }, 450)
  }

  const handleReportError = (e: React.FormEvent) => {
    e.preventDefault()
    if (!reportReason.trim()) return
    setReportSuccess(true)
    setTimeout(() => {
      setReportSuccess(false)
      setReportModalOpen(false)
      setReportReason("")
    }, 1500)
  }

  return (
    <>
      {/* Botão Flutuante (Tela 8 Trigger) */}
      <div className="fixed bottom-6 right-6 z-40">
        {!isOpen && (
          <Button
            onClick={() => setIsOpen(true)}
            size="lg"
            className="flex items-center gap-2.5 rounded-full bg-primary px-5 py-6 text-white shadow-xl hover:bg-primary/90 transition-all duration-300 hover:scale-105"
          >
            <Brain className="h-5 w-5 animate-pulse" />
            <span className="font-semibold text-sm">Assistente IA (RAG)</span>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
            </span>
          </Button>
        )}
      </div>

      {/* Janela Retrátil do Assistente */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 flex h-[580px] w-[390px] max-w-[calc(100vw-2rem)] flex-col rounded-2xl border border-border bg-card shadow-2xl transition-all duration-300 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border bg-muted/40 px-4 py-3.5">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-white">
                <Brain className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold font-heading leading-tight flex items-center gap-1.5">
                  Assistente NovaMente
                  <Badge variant="outline" className="text-[9px] py-0 px-1 font-mono bg-accent/50 text-primary border-primary/20">
                    RAG · OCI
                  </Badge>
                </h3>
                <p className="text-[11px] text-muted-foreground flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-500 inline-block"></span>
                  Ancoragem de Fontes Ativa
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-muted-foreground hover:text-foreground"
                onClick={() => setReportModalOpen(true)}
                title="Reportar Erro / Alucinação"
              >
                <AlertCircle className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-muted-foreground hover:text-foreground"
                onClick={() => setIsOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* FAQ Chips Sugeridos */}
          <div className="border-b border-border bg-muted/20 px-3 py-2 overflow-x-auto flex gap-1.5 text-xs no-scrollbar">
            {mockAssistantFaqs.map((faq) => (
              <button
                key={faq.id}
                onClick={() => handleSendMessage(faq.pergunta)}
                className="whitespace-nowrap rounded-full border border-border bg-background px-2.5 py-1 text-[11px] text-foreground hover:border-primary/50 hover:bg-accent/40 transition-colors"
              >
                {faq.pergunta}
              </button>
            ))}
          </div>

          {/* Mensagens */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${
                  msg.remetente === "usuario" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed ${
                    msg.remetente === "usuario"
                      ? "bg-primary text-primary-foreground rounded-br-xs"
                      : "bg-muted/70 text-foreground rounded-bl-xs border border-border/50"
                  }`}
                >
                  <p>{msg.texto}</p>

                  {/* Citação de Fontes RAG */}
                  {msg.fontes && msg.fontes.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-border/40 text-[10px] text-muted-foreground">
                      <div className="flex items-center gap-1 font-semibold text-primary">
                        <BookOpen className="h-3 w-3" />
                        <span>Fonte Ancorada:</span>
                      </div>
                      <p className="italic mt-0.5">{msg.fontes[0]}</p>
                    </div>
                  )}
                </div>
                <span className="text-[10px] text-muted-foreground mt-1 px-1">
                  {msg.data_hora}
                </span>
              </div>
            ))}
          </div>

          {/* Input Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSendMessage()
            }}
            className="border-t border-border bg-background p-3 flex gap-2"
          >
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Tire dúvidas sobre a documentação..."
              className="text-xs h-9 bg-muted/30 focus-visible:ring-primary"
            />
            <Button
              type="submit"
              size="icon"
              disabled={!inputValue.trim()}
              className="h-9 w-9 bg-primary text-primary-foreground hover:bg-primary/90 shrink-0"
            >
              <Send className="h-3.5 w-3.5" />
            </Button>
          </form>
        </div>
      )}

      {/* Modal Reportar Erro (Requisito Tela 8) */}
      {reportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-sm rounded-xl border border-border bg-card p-5 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h4 className="text-sm font-bold flex items-center gap-1.5 text-foreground">
                <AlertCircle className="h-4 w-4 text-destructive" />
                Reportar Erro / Alucinação
              </h4>
              <button
                onClick={() => setReportModalOpen(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {reportSuccess ? (
              <div className="py-6 text-center text-xs text-green-600 space-y-2">
                <CheckCircle2 className="h-8 w-8 mx-auto text-green-600 animate-bounce" />
                <p className="font-semibold">Relatório enviado com sucesso!</p>
                <p className="text-muted-foreground">
                  A equipe técnica e o avaliador de RAG irão revisar a ancoragem.
                </p>
              </div>
            ) : (
              <form onSubmit={handleReportError} className="space-y-3 pt-3">
                <p className="text-xs text-muted-foreground">
                  Identificou uma resposta imprecisa ou divergente do documento
                  original? Descreva abaixo para refinamento do prompt:
                </p>
                <textarea
                  value={reportReason}
                  onChange={(e) => setReportReason(e.target.value)}
                  placeholder="Ex: A explicação sobre sub-redes citou CIDR incorreto..."
                  rows={3}
                  required
                  className="w-full rounded-md border border-input bg-background p-2 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setReportModalOpen(false)}
                  >
                    Cancelar
                  </Button>
                  <Button
                    type="submit"
                    size="sm"
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    Enviar Reporte
                  </Button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  )
}
