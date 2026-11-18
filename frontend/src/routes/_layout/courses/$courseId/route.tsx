import { createFileRoute, Outlet } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/courses/$courseId")({
  component: Outlet,
  head: () => ({
    meta: [
      {
        title: "Curso - NovaMente",
      },
    ],
  }),
})
