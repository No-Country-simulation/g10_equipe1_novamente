import { zodResolver } from "@hookform/resolvers/zod"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { Sparkles } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { Body_login_login_access_token as AccessToken } from "@/client"
import { AuthLayout } from "@/components/Common/AuthLayout"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form"
import { LoadingButton } from "@/components/ui/loading-button"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"

const formSchema = z.object({
  username: z
    .string()
    .min(1, { message: "O e-mail é obrigatório" })
    .email({ message: "Insira um endereço de e-mail válido" }),
  password: z
    .string()
    .min(1, { message: "A senha é obrigatória" })
    .min(8, { message: "A senha deve conter pelo menos 8 caracteres" }),
}) satisfies z.ZodType<AccessToken>

type FormData = z.infer<typeof formSchema>

export const Route = createFileRoute("/login")({
  component: Login,
  beforeLoad: async () => {
    if (typeof window !== "undefined" && window.location.search.includes("logout")) {
      localStorage.removeItem("access_token")
      return
    }
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Login — NovaMente",
      },
    ],
  }),
})

function Login() {
  const { loginMutation } = useAuth()
  const [showPw, setShowPw] = useState(false)

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      username: "",
      password: "",
    },
  })

  const onSubmit = (data: FormData) => {
    if (loginMutation.isPending) return
    loginMutation.mutate(data)
  }

  return (
    <AuthLayout>
      <div className="flex flex-col gap-5">
        <h1 className="m-0 mb-1 text-center text-2xl leading-tight font-bold text-[#11151C] dark:text-white">
          Acesse sua conta
        </h1>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="flex flex-col gap-4"
          >
            {/* Campo E-mail */}
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem className="flex flex-col gap-1.5 space-y-0">
                  <label
                    htmlFor="l-email"
                    className="text-sm font-semibold text-[#11151C] dark:text-zinc-200"
                  >
                    E-mail
                  </label>
                  <FormControl>
                    <input
                      id="l-email"
                      data-testid="email-input"
                      type="email"
                      className="w-full min-h-[48px] px-3.5 py-2.5 rounded-[6px] border border-[#8A919C] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#11151C] dark:text-white text-base outline-none focus-visible:outline-3 focus-visible:outline-[#1F4FD8] focus-visible:outline-offset-2 transition-all box-border"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage className="text-xs text-destructive" />
                </FormItem>
              )}
            />

            {/* Campo Senha com botão de mostrar/ocultar senha */}
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem className="flex flex-col gap-1.5 space-y-0">
                  <div className="flex justify-between items-baseline">
                    <label
                      htmlFor="l-senha"
                      className="text-sm font-semibold text-[#11151C] dark:text-zinc-200"
                    >
                      Senha
                    </label>
                    <RouterLink
                      to="/recover-password"
                      className="text-sm text-[#11151C] dark:text-zinc-300 underline hover:text-[#1F4FD8] dark:hover:text-[#3B82F6] transition-colors"
                    >
                      Esqueceu a senha?
                    </RouterLink>
                  </div>
                  <FormControl>
                    <div className="relative">
                      <input
                        id="l-senha"
                        data-testid="password-input"
                        type={showPw ? "text" : "password"}
                        className="w-full min-h-[48px] pl-3.5 pr-12 py-2.5 rounded-[6px] border border-[#8A919C] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#11151C] dark:text-white text-base outline-none focus-visible:outline-3 focus-visible:outline-[#1F4FD8] focus-visible:outline-offset-2 transition-all box-border"
                        {...field}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPw(!showPw)}
                        aria-label={showPw ? "Ocultar senha" : "Mostrar senha"}
                        className="absolute right-1 top-1 w-11 h-11 border-none bg-transparent text-[#3D434D] dark:text-zinc-400 hover:text-[#11151C] dark:hover:text-white flex items-center justify-center cursor-pointer rounded transition-colors focus-visible:outline-3 focus-visible:outline-[#1F4FD8] focus-visible:outline-offset-2"
                      >
                        <svg
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.75"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          aria-hidden="true"
                        >
                          <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
                          <circle cx="12" cy="12" r="3" />
                          {showPw && <path d="M4 4l16 16" />}
                        </svg>
                      </button>
                    </div>
                  </FormControl>
                  <FormMessage className="text-xs text-destructive" />
                </FormItem>
              )}
            />

            {/* Botão Entrar Oficial Laranja com texto escuro */}
            <LoadingButton
              type="submit"
              loading={loginMutation.isPending}
              className="w-full min-h-[48px] border-none rounded-[6px] bg-[#F26B21] hover:bg-[#D95A12] text-[#11151C] font-semibold text-base cursor-pointer transition-colors shadow-none flex items-center justify-center mt-1 focus-visible:outline-3 focus-visible:outline-[#1F4FD8] focus-visible:outline-offset-2"
            >
              Entrar
            </LoadingButton>

            {/* Link para Criar conta */}
            <p className="m-0 mt-1 text-center text-sm text-[#11151C] dark:text-zinc-300">
              Ainda não tem conta?{" "}
              <RouterLink
                to="/signup"
                className="text-[#11151C] dark:text-white underline font-semibold hover:text-[#1F4FD8] dark:hover:text-[#3B82F6] inline-flex items-center min-h-[44px]"
              >
                Criar conta
              </RouterLink>
            </p>

            {/* Botão sutil de Demonstração para a Banca Avaliadora */}
            <div className="pt-3 border-t border-[#D5D9D2] dark:border-zinc-800">
              <button
                type="button"
                onClick={() => {
                  localStorage.setItem("access_token", "demo-token-novamente")
                  window.location.href = "/"
                }}
                className="w-full min-h-[38px] rounded-[6px] border border-[#D5D9D2] dark:border-zinc-800 bg-[#F6F7F4] dark:bg-zinc-900/60 hover:bg-[#EBECE8] dark:hover:bg-zinc-800 text-xs font-semibold text-[#3D434D] dark:text-zinc-300 transition-colors flex items-center justify-center gap-2 cursor-pointer focus-visible:outline-3 focus-visible:outline-[#1F4FD8] focus-visible:outline-offset-2"
              >
                <Sparkles className="w-3.5 h-3.5 text-[#F26B21]" />
                <span>Modo Demonstração (Banca Hackathon)</span>
              </button>
            </div>
          </form>
        </Form>
      </div>
    </AuthLayout>
  )
}


