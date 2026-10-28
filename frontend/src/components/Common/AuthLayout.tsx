import { Link } from "@tanstack/react-router"
import { Brain, Sparkles, BookOpen, Layers } from "lucide-react"

import { Appearance } from "@/components/Common/Appearance"
import { Footer } from "./Footer"

interface AuthLayoutProps {
  children: React.ReactNode
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="grid min-h-svh lg:grid-cols-12 bg-[#F6F7F4] dark:bg-zinc-950 font-sans">
      {/* LADO ESQUERDO: Hero escuro com a identidade visual oficial da NovaMente (Protótipo Karina) */}
      <div className="lg:col-span-6 xl:col-span-7 bg-[#11151C] text-white p-8 sm:p-12 lg:p-16 flex flex-col justify-between relative overflow-hidden">
        {/* Efeito de brilho de fundo sutil */}
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-[#F26B21]/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

        {/* Topo do Hero: Logo oficial */}
        <div className="relative z-10 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white text-[#11151C] shadow-md group-hover:scale-105 transition-transform">
              <Brain className="h-6 w-6 text-[#F26B21]" />
            </div>
            <div className="flex flex-col text-left">
              <div className="flex items-center text-2xl font-bold font-heading tracking-tight">
                <span className="text-white">Nova</span>
                <span className="text-[#F26B21]">Mente</span>
              </div>
              <span className="text-[11px] font-mono tracking-wider uppercase text-neutral-400 font-semibold">
                Hackathon ONE · Alura & Oracle OCI
              </span>
            </div>
          </Link>

          <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono font-medium bg-white/10 text-neutral-300 border border-white/10">
            <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A] animate-pulse"></span>
            Plataforma Ativa
          </span>
        </div>

        {/* Centro do Hero: Proposta de valor e textos da Karina */}
        <div className="relative z-10 my-auto py-10 flex flex-col gap-6 max-w-xl">
          <div className="inline-flex items-center gap-2 w-fit rounded-full bg-[#F26B21]/15 px-3.5 py-1.5 border border-[#F26B21]/30 text-xs font-mono font-semibold tracking-wider text-[#F26B21] uppercase">
            <Sparkles className="w-3.5 h-3.5" /> CURSOS PERSONALIZADOS COM IA
          </div>

          <h1 className="font-heading text-3xl sm:text-4xl xl:text-5xl font-bold leading-[1.08] text-white">
            Transforme documentação técnica em um curso sob medida.
          </h1>

          <p className="text-base sm:text-lg text-[#C3C8D0] leading-relaxed">
            O NovaMente cria uma trilha de estudo a partir dos seus materiais técnicos (PDF, Markdown e arquiteturas OCI), adaptada para o perfil e nível que você escolher.
          </p>

          {/* Destaques Didáticos */}
          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="flex items-center gap-2.5 rounded-lg bg-white/5 border border-white/10 p-3">
              <BookOpen className="w-4 h-4 text-[#F26B21]" />
              <span className="text-xs font-medium text-neutral-200">Tutoriais Práticos</span>
            </div>
            <div className="flex items-center gap-2.5 rounded-lg bg-white/5 border border-white/10 p-3">
              <Layers className="w-4 h-4 text-[#F26B21]" />
              <span className="text-xs font-medium text-neutral-200">Flashcards & Quizzes 3D</span>
            </div>
          </div>
        </div>

        {/* Rodapé do Hero */}
        <div className="relative z-10 pt-6 border-t border-white/10 flex items-center justify-between text-xs text-neutral-400 font-mono">
          <span>Oracle Cloud Always Free</span>
          <span>Pipeline RAG com Gemini</span>
        </div>
      </div>

      {/* LADO DIREITO: Card com os Formulários de Acesso (Login / Cadastro) */}
      <div className="lg:col-span-6 xl:col-span-5 flex flex-col justify-between p-6 sm:p-10 lg:p-12">
        <div className="flex justify-end">
          <Appearance />
        </div>

        <div className="flex flex-1 items-center justify-center py-6">
          <div className="w-full max-w-[440px] bg-white dark:bg-zinc-900 border border-[#D5D9D2] dark:border-zinc-800 rounded-2xl shadow-sm p-7 sm:p-8">
            {children}
          </div>
        </div>

        <Footer />
      </div>
    </div>
  )
}

