import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
  useNavigate,
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
      <div className="flex flex-col gap-5">
        <div className="text-center">
          <h1 className="m-0 mb-1 text-2xl leading-tight font-bold text-[#11151C] dark:text-white">
            Redefinir senha
          </h1>
          <p className="m-0 text-sm text-[#555B66] dark:text-zinc-400">
            Crie uma nova senha para proteger seu acesso.
          </p>
        </div>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="flex flex-col gap-4"
          >
            <FormField
              control={form.control}
              name="new_password"
              render={({ field }) => (
                <FormItem className="flex flex-col gap-1.5 space-y-0">
                  <label
                    htmlFor="n-pass"
                    className="text-sm font-semibold text-[#11151C] dark:text-zinc-200"
                  >
                    Nova senha
                  </label>
                  <FormControl>
                    <input
                      id="n-pass"
                      data-testid="new-password-input"
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
                    htmlFor="c-pass"
                    className="text-sm font-semibold text-[#11151C] dark:text-zinc-200"
                  >
                    Confirmar nova senha
                  </label>
                  <FormControl>
                    <input
                      id="c-pass"
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
              loading={mutation.isPending}
            >
              Salvar nova senha
            </LoadingButton>

            <p className="m-0 mt-1 text-center text-sm text-[#11151C] dark:text-zinc-300">
              <RouterLink
                to="/login"
                className="text-[#11151C] dark:text-white underline font-semibold hover:text-[#1F4FD8] dark:hover:text-[#3B82F6] inline-flex items-center min-h-[44px]"
              >
                Voltar ao Login
              </RouterLink>
            </p>
          </form>
        </Form>
      </div>
    </AuthLayout>
  )
}

