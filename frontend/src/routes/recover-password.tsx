import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { LoginService } from "@/client"
import { AuthLayout } from "@/components/Common/AuthLayout"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form"
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
      <div className="flex flex-col gap-5">
        <div className="text-center">
          <h1 className="m-0 mb-1 text-2xl leading-tight font-bold text-[#11151C] dark:text-white">
            Recuperar senha
          </h1>
          <p className="m-0 text-sm text-[#555B66] dark:text-zinc-400">
            Informe seu e-mail para receber as instruções de recuperação.
          </p>
        </div>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="flex flex-col gap-4"
          >
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem className="flex flex-col gap-1.5 space-y-0">
                  <label
                    htmlFor="r-email"
                    className="text-sm font-semibold text-[#11151C] dark:text-zinc-200"
                  >
                    E-mail
                  </label>
                  <FormControl>
                    <input
                      id="r-email"
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

            <LoadingButton
              type="submit"
              className="w-full min-h-[48px] border-none rounded-[6px] bg-[#F26B21] hover:bg-[#D95A12] text-[#11151C] font-semibold text-base cursor-pointer transition-colors shadow-none flex items-center justify-center mt-1 focus-visible:outline-3 focus-visible:outline-[#1F4FD8] focus-visible:outline-offset-2"
              loading={mutation.isPending}
            >
              Enviar link de recuperação
            </LoadingButton>

            <p className="m-0 mt-1 text-center text-sm text-[#11151C] dark:text-zinc-300">
              Lembrou da senha?{" "}
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


