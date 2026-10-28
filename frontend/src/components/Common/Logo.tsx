import { Link } from "@tanstack/react-router"
import { Brain } from "lucide-react"
import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  const content = (
    <div className={cn("flex items-center gap-2.5 select-none", className)}>
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm ring-1 ring-primary/30">
        <Brain className="h-5 w-5" />
      </div>
      {(variant === "full" || variant === "responsive") && (
        <div
          className={cn(
            "flex flex-col text-left leading-none",
            variant === "responsive" && "group-data-[collapsible=icon]:hidden",
          )}
        >
          <div className="flex items-center text-lg font-bold tracking-tight">
            <span className="text-foreground font-heading">Nova</span>
            <span className="text-primary font-heading">Mente</span>
          </div>
          <span className="text-[10px] font-mono tracking-wider uppercase text-muted-foreground font-semibold mt-0.5">
            IA Educacional · OCI
          </span>
        </div>
      )}
    </div>
  )

  if (!asLink) {
    return content
  }

  return (
    <Link to="/" className="inline-flex items-center">
      {content}
    </Link>
  )
}
