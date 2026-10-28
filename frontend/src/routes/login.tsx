import { zodResolver } from "@hookform/resolvers/zod"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { Sparkles, ArrowRight, HelpCircle } from "lucide-react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { Body_login_login_access_token as AccessToken } from "@/client"
import { AuthLayout } from "@/components/Common/AuthLayout"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"

const formSchema = z.object({
  username: z.string().min(1, { message: "O e-mail é obrigatório" }).email({ message: "Insira um endereço de e-mail válido" }),
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
        title: "Entrar — NovaMente · IA Educacional OCI",
      },
    ],
  }),
})

function Login() {
  const { loginMutation } = useAuth()
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
      <div className="flex flex-col gap-6">
        {/* Abas Superiores no estilo do protótipo da Karina */}
        <div className="flex rounded-lg border border-[#D5D9D2] dark:border-zinc-800 p-1 bg-muted/60">
          <div className="flex-1 py-2 text-center text-sm font-semibold rounded-md bg-[#11151C] text-white dark:bg-primary dark:text-primary-foreground shadow-sm">
            Entrar
          </div>
          <RouterLink
            to="/signup"
            className="flex-1 py-2 text-center text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Criar conta
          </RouterLink>
        </div>

        {/* Cabeçalho do Card */}
        <div className="flex flex-col gap-1.5 text-left">
          <h2 className="text-2xl font-bold font-heading text-foreground tracking-tight">
            Que bom ver você de novo
          </h2>
          <p className="text-xs text-muted-foreground">
            Acesse sua conta para continuar sua trilha de aprendizagem.
          </p>
        </div>

        {/* Formulário */}
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="flex flex-col gap-5"
          >
            <div className="grid gap-4">
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-xs font-semibold text-foreground">
                      E-mail corporativo ou pessoal
                    </FormLabel>
                    <FormControl>
                      <Input
                        data-testid="email-input"
                        placeholder="voce@empresa.com"
                        type="email"
                        className="h-11 bg-background"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage className="text-xs" />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <div className="flex items-center justify-between">
                      <FormLabel className="text-xs font-semibold text-foreground">
                        Senha de acesso
                      </FormLabel>
                      <RouterLink
                        to="/recover-password"
                        className="text-xs text-primary hover:underline font-medium"
                      >
                        Esqueceu a senha?
                      </RouterLink>
                    </div>
                    <FormControl>
                      <PasswordInput
                        data-testid="password-input"
                        placeholder="••••••••"
                        className="h-11 bg-background"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage className="text-xs" />
                  </FormItem>
                )}
              />

              <LoadingButton
                type="submit"
                loading={loginMutation.isPending}
                className="h-11 w-full bg-[#11151C] hover:bg-[#1f2530] text-white dark:bg-primary dark:hover:bg-primary/90 font-semibold text-sm shadow-sm flex items-center justify-center gap-2 mt-1"
              >
                <span>Entrar na Plataforma</span>
                <ArrowRight className="w-4 h-4" />
              </LoadingButton>

              <div className="relative flex py-1 items-center">
                <div className="flex-grow border-t border-border"></div>
                <span className="flex-shrink mx-2 text-[10px] text-muted-foreground uppercase font-mono tracking-widest">
                  ou
                </span>
                <div className="flex-grow border-t border-border"></div>
              </div>

              {/* Botão de Demonstração para a Banca de Avaliação */}
              <button
                type="button"
                onClick={() => {
                  localStorage.setItem("access_token", "demo-token-novamente")
                  window.location.href = "/"
                }}
                className="w-full rounded-lg border border-primary/40 bg-primary/5 hover:bg-primary/10 p-2.5 text-xs font-semibold text-primary transition-all flex items-center justify-center gap-2 group"
              >
                <Sparkles className="w-3.5 h-3.5 text-primary group-hover:rotate-12 transition-transform" />
                <span>Acessar Modo Demonstração (Banca Hackathon)</span>
              </button>
            </div>

            <div className="pt-2 border-t border-border/60 flex items-center justify-center gap-1.5 text-xs text-muted-foreground">
              <HelpCircle className="w-3.5 h-3.5 text-muted-foreground" />
              <span>Dúvidas sobre o acesso?</span>
              <a
                href="#duvidas"
                onClick={(e) => {
                  e.preventDefault()
                  alert("Para dúvidas durante a banca do Hackathon ONE, use o Modo Demonstração ou crie uma conta gratuita.")
                }}
                className="text-primary hover:underline font-medium"
              >
                Ver suporte
              </a>
            </div>
          </form>
        </Form>
      </div>
    </AuthLayout>
  )
}

