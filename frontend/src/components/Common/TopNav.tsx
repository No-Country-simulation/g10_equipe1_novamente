import { Link } from "@tanstack/react-router"

import { Appearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import { UserMenu } from "@/components/Common/UserMenu"
import useAuth from "@/hooks/useAuth"

const tabs = [
  { title: "Home", to: "/" },
  { title: "Novo curso", to: "/courses/new" },
] as const

export function TopNav() {
  const { user } = useAuth()

  return (
    <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-4 border-b bg-card px-4 sm:gap-6 sm:px-10">
      <Link to="/" className="shrink-0">
        <Logo variant="icon" asLink={false} className="sm:hidden" />
        <Logo asLink={false} className="hidden sm:block" />
      </Link>
      <nav aria-label="Principal" className="flex items-center gap-1">
        {tabs.map((tab) => (
          <Link
            key={tab.to}
            to={tab.to}
            activeOptions={{ exact: true }}
            className="whitespace-nowrap rounded-[6px] px-3.5 py-2 text-base"
            activeProps={{
              className: "bg-muted font-semibold text-foreground",
            }}
            inactiveProps={{ className: "text-muted-foreground" }}
          >
            {tab.title}
          </Link>
        ))}
      </nav>
      <div className="ml-auto flex items-center gap-2">
        <Appearance />
        {user && <UserMenu user={user} />}
      </div>
    </header>
  )
}
