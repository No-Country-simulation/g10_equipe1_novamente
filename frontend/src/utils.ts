import { AxiosError } from "axios"

const apiErrorMessages: Record<string, string> = {
  "Incorrect email or password": "E-mail ou senha incorretos",
  "Inactive user": "Esta conta está inativa",
  "Could not validate credentials": "Não foi possível validar suas credenciais",
  "User not found": "Usuário não encontrado",
  "User with this email already exists": "Já existe uma conta com este e-mail",
  "The user with this email already exists in the system":
    "Já existe uma conta com este e-mail",
  "Incorrect password": "Senha incorreta",
  "New password cannot be the same as the current one":
    "A nova senha deve ser diferente da senha atual",
}

function extractErrorMessage(err: Error): string {
  if (err instanceof AxiosError) {
    const errDetail = (err.response?.data as { detail?: unknown })?.detail
    if (typeof errDetail === "string") {
      return (
        apiErrorMessages[errDetail] ??
        "Não foi possível concluir a solicitação."
      )
    }
    if (Array.isArray(errDetail) && errDetail.length > 0) {
      return "Verifique os dados informados e tente novamente."
    }
    return "Não foi possível concluir a solicitação. Tente novamente."
  }
  return "Algo deu errado."
}

export const handleError = function (this: (msg: string) => void, err: Error) {
  const errorMessage = extractErrorMessage(err)
  this(errorMessage)
}

export const getInitials = (name: string): string => {
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}
