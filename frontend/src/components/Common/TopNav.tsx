import { Link } from "@tanstack/react-router"
import { Menu } from "lucide-react"

import { Appearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import { UserMenu } from "@/components/Common/UserMenu"
import { Button } from "@/components/ui/button"
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "@/components/ui/navigation-menu"
import { Separator } from "@/components/ui/separator"
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import useAuth from "@/hooks/useAuth"

const tabs = [
  { title: "Home", to: "/courses" },
  { title: "Novo curso", to: "/courses/new" },
] as const

export function TopNav() {
  const { user } = useAuth()

  return (
    <header className="sticky top-0 z-10 h-16 shrink-0 border-b bg-card px-4 sm:px-10">
      <div className="mx-auto flex h-full max-w-7xl items-center gap-6">
        <Link to="/" className="shrink-0">
          <Logo variant="icon" asLink={false} className="lg:hidden" />
          <Logo asLink={false} className="hidden lg:block" />
        </Link>

        <NavigationMenu
          viewport={false}
          aria-label="Principal"
          className="hidden lg:flex"
        >
          <NavigationMenuList className="gap-1">
            {tabs.map((tab) => (
              <NavigationMenuItem key={tab.to}>
                <NavigationMenuLink
                  asChild
                  className="group inline-flex h-10 w-max flex-row items-center justify-center rounded-md bg-transparent px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-accent-foreground data-[status=active]:bg-muted data-[status=active]:font-semibold data-[status=active]:text-foreground"
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
          <Separator
            orientation="vertical"
            className="data-[orientation=vertical]:h-4"
          />
          {user && <UserMenu user={user} />}
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="lg:hidden">
                <Menu />
                <span className="sr-only">Abrir menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent className="overflow-y-auto">
              <SheetHeader>
                <SheetTitle>
                  <Logo asLink={false} />
                </SheetTitle>
                <SheetDescription className="sr-only">
                  Navegação principal
                </SheetDescription>
              </SheetHeader>
              <nav
                aria-label="Principal (celular)"
                className="flex flex-col gap-1 p-4"
              >
                {tabs.map((tab) => (
                  <SheetClose asChild key={tab.to}>
                    <Button
                      asChild
                      variant="ghost"
                      className="justify-start text-base font-normal text-muted-foreground data-[status=active]:bg-muted data-[status=active]:font-semibold data-[status=active]:text-foreground"
                    >
                      <Link to={tab.to} activeOptions={{ exact: true }}>
                        {tab.title}
                      </Link>
                    </Button>
                  </SheetClose>
                ))}
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  )
}
