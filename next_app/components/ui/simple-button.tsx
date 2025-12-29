// next_app/components/ui/simple-button.tsx
import type { ButtonHTMLAttributes, ReactNode } from "react"

interface SimpleButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  className?: string
  size?: "sm" | "md" | "lg"
}

export function Button({
  children,
  className = "",
  size = "md",
  ...props
}: SimpleButtonProps) {
  const sizeClasses = {
    sm: "px-2 py-1 text-sm",
    md: "px-3 py-2 text-base",
    lg: "px-4 py-3 text-lg",
  }

  return (
    <button
      {...props}
      className={`rounded-md border bg-primary text-primary-foreground hover:bg-primary/80 transition ${sizeClasses[size]} ${className}`}
    >
      {children}
    </button>
  )
}
