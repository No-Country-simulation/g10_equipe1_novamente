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
  { title: "Home", to: "/" },
  { title: "Novo curso", to: "/courses/new" },
] as const

export function TopNav() {
  const { user } = useAuth()

  return (
    <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-6 border-b bg-card px-4 sm:px-10">
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
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="outline" size="icon" className="lg:hidden">
              <Menu />
              <span className="sr-only">Abrir menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent className="overflow-y-auto">
            <SheetHeader>
              <SheetTitle>Menu</SheetTitle>
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
    </header>
  )
}
