import { zodResolver } from "@hookform/resolvers/zod"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { ArrowRight, CheckCircle2 } from "lucide-react"
import { useForm } from "react-hook-form"
import { z } from "zod"
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

const formSchema = z
  .object({
    email: z
      .string()
      .min(1, { message: "O e-mail é obrigatório" })
      .email({ message: "Insira um endereço de e-mail válido" }),
    full_name: z
      .string()
      .min(1, { message: "O nome completo é obrigatório" })
      .min(2, { message: "O nome deve ter no mínimo 2 caracteres" }),
    password: z
      .string()
      .min(1, { message: "A senha é obrigatória" })
      .min(8, { message: "A senha deve conter pelo menos 8 caracteres" }),
    confirm_password: z
      .string()
      .min(1, { message: "A confirmação de senha é obrigatória" }),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "As senhas não coincidem",
    path: ["confirm_password"],
  })

type FormData = z.infer<typeof formSchema>

export const Route = createFileRoute("/signup")({
  component: SignUp,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Criar Conta — NovaMente · IA Educacional OCI",
      },
    ],
  }),
})

function SignUp() {
  const { signUpMutation } = useAuth()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      email: "",
      full_name: "",
      password: "",
      confirm_password: "",
    },
  })

  const onSubmit = (data: FormData) => {
    if (signUpMutation.isPending) return

    // exclude confirm_password from submission data
    const { confirm_password: _confirm_password, ...submitData } = data
    signUpMutation.mutate(submitData)
  }

  return (
    <AuthLayout>
      <div className="flex flex-col gap-6">
        {/* Abas Superiores no estilo do protótipo da Karina */}
        <div className="flex rounded-lg border border-[#D5D9D2] dark:border-zinc-800 p-1 bg-muted/60">
          <RouterLink
            to="/login"
            className="flex-1 py-2 text-center text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Entrar
          </RouterLink>
          <div className="flex-1 py-2 text-center text-sm font-semibold rounded-md bg-[#F26B21] text-white shadow-sm">
            Criar conta
          </div>
        </div>

        {/* Cabeçalho do Card */}
        <div className="flex flex-col gap-1.5 text-left">
          <h2 className="text-2xl font-bold font-heading text-foreground tracking-tight">
            Crie sua conta
          </h2>
          <p className="text-xs text-muted-foreground">
            Comece a transformar suas documentações técnicas em cursos didáticos.
          </p>
        </div>

        {/* Formulário de Cadastro */}
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="flex flex-col gap-4"
          >
            <div className="grid gap-3.5">
              <FormField
                control={form.control}
                name="full_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-xs font-semibold text-foreground">
                      Nome Completo
                    </FormLabel>
                    <FormControl>
                      <Input
                        data-testid="full-name-input"
                        placeholder="Ex: Carlos Eduardo"
                        type="text"
                        className="h-10 bg-background"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage className="text-xs" />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-xs font-semibold text-foreground">
                      E-mail Corporativo ou Pessoal
                    </FormLabel>
                    <FormControl>
                      <Input
                        data-testid="email-input"
                        placeholder="voce@empresa.com"
                        type="email"
                        className="h-10 bg-background"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage className="text-xs" />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs font-semibold text-foreground">
                        Senha
                      </FormLabel>
                      <FormControl>
                        <PasswordInput
                          data-testid="password-input"
                          placeholder="••••••••"
                          className="h-10 bg-background"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage className="text-xs" />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="confirm_password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs font-semibold text-foreground">
                        Confirmar Senha
                      </FormLabel>
                      <FormControl>
                        <PasswordInput
                          data-testid="confirm-password-input"
                          placeholder="••••••••"
                          className="h-10 bg-background"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage className="text-xs" />
                    </FormItem>
                  )}
                />
              </div>

              {/* Destaque de Benefícios rápidos */}
              <div className="rounded-lg bg-primary/5 border border-primary/20 p-2.5 flex items-center gap-2 text-[11px] text-muted-foreground font-medium">
                <CheckCircle2 className="w-4 h-4 text-primary shrink-0" />
                <span>Acesso gratuito ao gerador de flashcards, quizzes e tutoriais RAG</span>
              </div>

              <LoadingButton
                type="submit"
                className="h-11 w-full bg-[#F26B21] hover:bg-[#d95b18] text-white font-semibold text-sm shadow-sm flex items-center justify-center gap-2 mt-1"
                loading={signUpMutation.isPending}
              >
                <span>Finalizar Cadastro</span>
                <ArrowRight className="w-4 h-4" />
              </LoadingButton>
            </div>

            <div className="pt-2 border-t border-border/60 text-center text-xs text-muted-foreground">
              Já possui uma conta ativa?{" "}
              <RouterLink
                to="/login"
                className="font-semibold text-primary underline underline-offset-4 hover:text-primary/90"
              >
                Fazer Login
              </RouterLink>
            </div>
          </form>
        </Form>
      </div>
    </AuthLayout>
  )
}

