import { Appearance } from "@/components/Common/Appearance"

interface AuthLayoutProps {
  children: React.ReactNode
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen w-full flex flex-col lg:flex-row bg-[#FFFFFF] dark:bg-[#11151C] text-[#11151C] dark:text-[#F6F7F4] font-sans antialiased">
      {/* LADO ESQUERDO: Minimalista, limpo e arejado (fiel ao protótipo da Sprint 1) */}
      <div className="flex-1 bg-[#F6F7F4] dark:bg-[#181E27] p-8 sm:p-12 lg:p-16 flex flex-col items-center justify-center gap-5 text-center min-h-[320px] lg:min-h-screen">
        <div className="flex items-center justify-center gap-4">
          {/* Ícone oficial NovaMente do protótipo */}
          <svg
            width="64"
            height="64"
            viewBox="0 0 28 28"
            aria-hidden="true"
            className="shrink-0"
          >
            <rect width="28" height="28" rx="6" fill="#11151C" className="dark:fill-[#0B0D11]" />
            <circle cx="9" cy="19" r="3" fill="#F26B21" />
            <circle cx="19" cy="9" r="3" fill="#FFFFFF" />
            <path
              d="M11 17l6-6"
              stroke="#FFFFFF"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
          <span className="font-heading text-4xl sm:text-5xl lg:text-[64px] leading-none font-bold text-[#11151C] dark:text-white tracking-tight select-none">
            NovaMente
          </span>
        </div>
        <p className="m-0 max-w-[420px] text-base sm:text-[17px] leading-relaxed text-[#3D434D] dark:text-[#A0A6B1] font-normal">
          Cursos personalizados a partir dos seus materiais, no nível que você escolher.
        </p>
      </div>

      {/* LADO DIREITO: Layout limpo sem cards pesados, focado no formulário */}
      <div className="flex-1 bg-[#FFFFFF] dark:bg-[#11151C] flex flex-col justify-between min-h-[580px] lg:min-h-screen">
        {/* Topo com o seletor discreto de tema */}
        <div className="flex justify-end p-4 sm:p-6">
          <Appearance />
        </div>

        {/* Centro com o formulário limpo max-w-[360px] */}
        <div className="flex flex-1 items-center justify-center px-6 sm:px-10 py-6 sm:py-12">
          <div className="w-full max-w-[360px] flex flex-col gap-5">
            {children}
          </div>
        </div>

        {/* Rodapé oficial limpo da Sprint 1 */}
        <footer className="mx-6 sm:mx-10 py-5 px-6 border-t border-[#D5D9D2] dark:border-zinc-800 text-sm text-[#555B66] dark:text-[#9DA3AE]">
          NovaMente · 2026
        </footer>
      </div>
    </div>
  )
}


