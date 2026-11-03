import { createFileRoute } from "@tanstack/react-router"

import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Início - NovaMente",
      },
    ],
  }),
})

function Dashboard() {
  const { user: currentUser } = useAuth()

  return (
    <div>
      <div>
        <h1 className="text-2xl truncate max-w-sm">
          Olá, {currentUser?.full_name || currentUser?.email} 👋
        </h1>
        <p className="text-muted-foreground">Que bom ter você de volta!</p>
      </div>
    </div>
  )
}
