import { zodResolver } from "@hookform/resolvers/zod"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { z } from "zod"
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
      <div className="flex flex-col gap-5">
        <h1 className="m-0 mb-1 text-center text-2xl leading-tight font-bold text-[#11151C] dark:text-white">
          Criar conta
        </h1>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="flex flex-col gap-4"
          >
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem className="flex flex-col gap-1.5 space-y-0">
                  <label
                    htmlFor="s-name"
                    className="text-sm font-semibold text-[#11151C] dark:text-zinc-200"
                  >
                    Nome completo
                  </label>
                  <FormControl>
                    <input
                      id="s-name"
                      data-testid="full-name-input"
                      placeholder="Seu nome"
                      type="text"
                      className="w-full min-h-[48px] px-3.5 py-2.5 rounded-[6px] border border-[#8A919C] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#11151C] dark:text-white text-base outline-none focus-visible:outline-3 focus-visible:outline-[#1F4FD8] focus-visible:outline-offset-2 transition-all placeholder:text-muted-foreground box-border"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage className="text-xs text-destructive" />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem className="flex flex-col gap-1.5 space-y-0">
                  <label
                    htmlFor="s-email"
                    className="text-sm font-semibold text-[#11151C] dark:text-zinc-200"
                  >
                    E-mail
                  </label>
                  <FormControl>
                    <input
                      id="s-email"
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

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem className="flex flex-col gap-1.5 space-y-0">
                  <label
                    htmlFor="s-password"
                    className="text-sm font-semibold text-[#11151C] dark:text-zinc-200"
                  >
                    Senha
                  </label>
                  <FormControl>
                    <input
                      id="s-password"
                      data-testid="password-input"
                      type="password"
                      placeholder="••••••••"
                      className="w-full min-h-[48px] px-3.5 py-2.5 rounded-[6px] border border-[#8A919C] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#11151C] dark:text-white text-base outline-none focus-visible:outline-3 focus-visible:outline-[#1F4FD8] focus-visible:outline-offset-2 transition-all box-border"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage className="text-xs text-destructive" />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="confirm_password"
              render={({ field }) => (
                <FormItem className="flex flex-col gap-1.5 space-y-0">
                  <label
                    htmlFor="s-confirm-password"
                    className="text-sm font-semibold text-[#11151C] dark:text-zinc-200"
                  >
                    Confirmar senha
                  </label>
                  <FormControl>
                    <input
                      id="s-confirm-password"
                      data-testid="confirm-password-input"
                      type="password"
                      placeholder="••••••••"
                      className="w-full min-h-[48px] px-3.5 py-2.5 rounded-[6px] border border-[#8A919C] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#11151C] dark:text-white text-base outline-none focus-visible:outline-3 focus-visible:outline-[#1F4FD8] focus-visible:outline-offset-2 transition-all box-border"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage className="text-xs text-destructive" />
                </FormItem>
              )}
            />

            <LoadingButton
              type="submit"
              className="w-full min-h-[48px] border-none rounded-[6px] bg-[#F26B21] hover:bg-[#D95A12] text-[#11151C] font-semibold text-base cursor-pointer transition-colors shadow-none flex items-center justify-center mt-1 focus-visible:outline-3 focus-visible:outline-[#1F4FD8] focus-visible:outline-offset-2"
              loading={signUpMutation.isPending}
            >
              Criar conta
            </LoadingButton>

            <p className="m-0 mt-1 text-center text-sm text-[#11151C] dark:text-zinc-300">
              Já tem conta?{" "}
              <RouterLink
                to="/login"
                className="text-[#11151C] dark:text-white underline font-semibold hover:text-[#1F4FD8] dark:hover:text-[#3B82F6] inline-flex items-center min-h-[44px]"
              >
                Entrar
              </RouterLink>
            </p>
          </form>
        </Form>
      </div>
    </AuthLayout>
  )
}


