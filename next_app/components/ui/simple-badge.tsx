// next_app/components/ui/simple-badge.tsx
import React from "react";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "solid" | "outline";
  className?: string;
}

export function Badge({
  children,
  variant = "solid",
  className = "",
}: BadgeProps) {
  const base =
    "px-2 py-0.5 text-xs font-medium rounded-md inline-flex items-center";

  const styles =
    variant === "outline"
      ? "border border-gray-400 text-gray-700"
      : "bg-gray-800 text-white";

  return <span className={`${base} ${styles} ${className}`}>{children}</span>;
}
