import DeleteConfirmation from "./DeleteConfirmation"

const DeleteAccount = () => {
  return (
    <div className="max-w-md mt-4 rounded-lg border border-destructive/50 p-4">
      <h3 className="font-semibold text-destructive">Excluir conta</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Exclua sua conta e todos os dados associados permanentemente.
      </p>
      <DeleteConfirmation />
    </div>
  )
}

export default DeleteAccount
