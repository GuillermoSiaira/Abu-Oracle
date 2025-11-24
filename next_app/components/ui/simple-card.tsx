// next_app/components/ui/simple-card.tsx
import type { ReactNode } from "react";

interface SimpleCardProps {
  children: ReactNode;
  className?: string;
}

// =========================
// CARD CONTAINER
// =========================
export function Card({ children, className = "" }: SimpleCardProps) {
  return (
    <div className={`rounded-md border p-4 ${className}`}>
      {children}
    </div>
  );
}

// =========================
// HEADER
// =========================
export function CardHeader({ children, className = "" }: SimpleCardProps) {
  return (
    <div className={`mb-2 ${className}`}>
      {children}
    </div>
  );
}

// =========================
// TITLE
// =========================
export function CardTitle({ children, className = "" }: SimpleCardProps) {
  return (
    <h3 className={`text-lg font-bold ${className}`}>
      {children}
    </h3>
  );
}

// =========================
// CONTENT
// =========================
export function CardContent({ children, className = "" }: SimpleCardProps) {
  return (
    <div className={`${className}`}>
      {children}
    </div>
  );
}

// =========================
// DESCRIPTION (Nuevo)
// =========================
export function CardDescription({
  children,
  className = "",
}: SimpleCardProps) {
  return (
    <p className={`text-sm text-muted-foreground ${className}`}>
      {children}
    </p>
  );
}
