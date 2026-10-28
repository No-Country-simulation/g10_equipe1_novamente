import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { KeyRound, ArrowLeft, Mail } from "lucide-react"
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
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { isLoggedIn } from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z.object({
  email: z
    .string()
    .min(1, { message: "O e-mail é obrigatório" })
    .email({ message: "Insira um endereço de e-mail válido" }),
})

type FormData = z.infer<typeof formSchema>

export const Route = createFileRoute("/recover-password")({
  component: RecoverPassword,
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
        title: "Recuperar Senha — NovaMente · IA Educacional OCI",
      },
    ],
  }),
})

function RecoverPassword() {
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
    },
  })
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const recoverPassword = async (data: FormData) => {
    await LoginService.recoverPassword({
      path: { email: data.email },
    })
  }

  const mutation = useMutation({
    mutationFn: recoverPassword,
    onSuccess: () => {
      showSuccessToast("E-mail de recuperação enviado com sucesso! Verifique sua caixa de entrada.")
      form.reset()
    },
    onError: handleError.bind(showErrorToast),
  })

  const onSubmit = async (data: FormData) => {
    if (mutation.isPending) return
    mutation.mutate(data)
  }

  return (
    <AuthLayout>
      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <KeyRound className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-2xl font-bold font-heading text-foreground tracking-tight">
              Recuperar Senha
            </h2>
            <p className="text-xs text-muted-foreground">
              Insira seu e-mail para receber as instruções de redefinição.
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
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-xs font-semibold text-foreground">
                      E-mail cadastrado
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

              <LoadingButton
                type="submit"
                className="h-11 w-full bg-[#11151C] hover:bg-[#1f2530] text-white dark:bg-primary dark:hover:bg-primary/90 font-semibold text-sm shadow-sm flex items-center justify-center gap-2 mt-1"
                loading={mutation.isPending}
              >
                <Mail className="w-4 h-4" />
                <span>Enviar Instruções</span>
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

