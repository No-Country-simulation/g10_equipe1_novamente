import { Link } from "@tanstack/react-router"

import { Appearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import { UserMenu } from "@/components/Common/UserMenu"
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "@/components/ui/navigation-menu"
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
      <NavigationMenu viewport={false} aria-label="Principal">
        <NavigationMenuList className="gap-1">
          {tabs.map((tab) => (
            <NavigationMenuItem key={tab.to}>
              <NavigationMenuLink
                asChild
                className="h-auto flex-row rounded-[6px] bg-transparent px-3.5 py-2 text-base font-normal text-muted-foreground data-[status=active]:bg-muted data-[status=active]:font-semibold data-[status=active]:text-foreground"
              >
                <Link to={tab.to} activeOptions={{ exact: true }}>
                  {tab.title}
                </Link>
              </NavigationMenuLink>
            </NavigationMenuItem>
          ))}
        </NavigationMenuList>
      </NavigationMenu>
      <div className="ml-auto flex items-center gap-2">
        <Appearance />
        {user && <UserMenu user={user} />}
      </div>
    </header>
  )
}
