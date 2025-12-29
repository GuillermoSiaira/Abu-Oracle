// next_app/components/ui/simple-label.tsx
import React from "react"

export interface SimpleLabelProps
  extends React.LabelHTMLAttributes<HTMLLabelElement> {}

export function Label({ children, className = "", ...props }: SimpleLabelProps) {
  return (
    <label className={`text-sm font-medium ${className}`} {...props}>
      {children}
    </label>
  )
}
