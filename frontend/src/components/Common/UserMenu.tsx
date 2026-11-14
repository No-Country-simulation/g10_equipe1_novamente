import { Link as RouterLink } from "@tanstack/react-router"
import { ChevronDown, LogOut, Settings } from "lucide-react"

import type { UserPublic } from "@/client"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import useAuth from "@/hooks/useAuth"
import { getInitials } from "@/utils"

function UserAvatar({ name }: { name: string }) {
  return (
    <Avatar className="size-8">
      <AvatarFallback className="bg-muted text-sm font-semibold text-foreground">
        {getInitials(name)}
      </AvatarFallback>
    </Avatar>
  )
}

export function UserMenu({ user }: { user: UserPublic }) {
  const { logout } = useAuth()
  const name = user.full_name || user.email

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        data-testid="user-menu"
        className="flex items-center gap-2 rounded-md p-1 outline-none hover:bg-accent focus-visible:ring-[3px] focus-visible:ring-ring/50"
      >
        <UserAvatar name={name} />
        <span className="hidden max-w-40 truncate sm:block">{name}</span>
        <ChevronDown className="hidden size-4 text-muted-foreground sm:block" />
        <span className="sr-only">Menu da conta</span>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="min-w-56" align="end" sideOffset={4}>
        <DropdownMenuLabel className="flex items-center gap-2.5 font-normal">
          <UserAvatar name={name} />
          <div className="flex min-w-0 flex-col">
            <p className="truncate text-sm font-semibold">{name}</p>
            <p className="truncate text-xs text-muted-foreground">
              {user.email}
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <RouterLink to="/settings">
            <Settings />
            Configurações da conta
          </RouterLink>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => logout()}>
          <LogOut />
          Sair
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
