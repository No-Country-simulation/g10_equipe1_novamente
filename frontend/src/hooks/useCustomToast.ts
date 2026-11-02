import { toast } from "sonner"

const useCustomToast = () => {
  const showSuccessToast = (description: string) => {
    toast.success("Sucesso!", {
      description,
    })
  }

  const showErrorToast = (description: string) => {
    toast.error("Algo deu errado!", {
      description,
    })
  }

  return { showSuccessToast, showErrorToast }
}

export default useCustomToast
