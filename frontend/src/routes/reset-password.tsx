import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
  useNavigate,
} from "@tanstack/react-router"
import { LockKeyhole, ArrowRight, ArrowLeft } from "lucide-react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { LoginService } from "@/client"
import { AuthLayout } from "@/components/Common/AuthLayout"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import { isLoggedIn } from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const searchSchema = z.object({
  token: z.string().catch(""),
})

const formSchema = z
  .object({
    new_password: z
      .string()
      .min(1, { message: "A nova senha é obrigatória" })
      .min(8, { message: "A senha deve conter no mínimo 8 caracteres" }),
    confirm_password: z
      .string()
      .min(1, { message: "A confirmação da nova senha é obrigatória" }),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "As senhas não coincidem",
    path: ["confirm_password"],
  })

type FormData = z.infer<typeof formSchema>

export const Route = createFileRoute("/reset-password")({
  component: ResetPassword,
  validateSearch: searchSchema,
  beforeLoad: async ({ search }) => {
    if (isLoggedIn()) {
      throw redirect({ to: "/" })
    }
    if (!search.token) {
      throw redirect({ to: "/login" })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Redefinir Senha — NovaMente · IA Educacional OCI",
      },
    ],
  }),
})

function ResetPassword() {
  const { token } = Route.useSearch()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const navigate = useNavigate()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      new_password: "",
      confirm_password: "",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: { new_password: string; token: string }) =>
      LoginService.resetPassword({ body: data }),
    onSuccess: () => {
      showSuccessToast("Senha alterada com sucesso! Você já pode entrar com sua nova senha.")
      form.reset()
      navigate({ to: "/login" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate({ new_password: data.new_password, token })
  }

  return (
    <AuthLayout>
      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <LockKeyhole className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-2xl font-bold font-heading text-foreground tracking-tight">
              Nova Senha
            </h2>
            <p className="text-xs text-muted-foreground">
              Crie uma senha segura para proteger o seu acesso.
            </p>
          </div>
        </div>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="flex flex-col gap-5"
          >
            <div className="grid gap-4">
              <FormField
                control={form.control}
                name="new_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-xs font-semibold text-foreground">
                      Nova Senha
                    </FormLabel>
                    <FormControl>
                      <PasswordInput
                        data-testid="new-password-input"
                        placeholder="••••••••"
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
                name="confirm_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-xs font-semibold text-foreground">
                      Confirmar Nova Senha
                    </FormLabel>
                    <FormControl>
                      <PasswordInput
                        data-testid="confirm-password-input"
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
                className="h-11 w-full bg-[#11151C] hover:bg-[#1f2530] text-white dark:bg-primary dark:hover:bg-primary/90 font-semibold text-sm shadow-sm flex items-center justify-center gap-2 mt-1"
                loading={mutation.isPending}
              >
                <span>Salvar Nova Senha</span>
                <ArrowRight className="w-4 h-4" />
              </LoadingButton>
            </div>

            <div className="pt-2 border-t border-border/60 text-center text-xs text-muted-foreground">
              Lembrou da sua senha?{" "}
              <RouterLink
                to="/login"
                className="font-semibold text-primary underline underline-offset-4 hover:text-primary/90 inline-flex items-center gap-1 ml-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Voltar ao Login
              </RouterLink>
            </div>
          </form>
        </Form>
      </div>
    </AuthLayout>
  )
}

