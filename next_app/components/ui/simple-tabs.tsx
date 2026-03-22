// next_app/components/ui/simple-tabs.tsx
"use client";

import React, { useState, ReactNode } from "react";

interface TabsProps {
  defaultValue: string;
  children: ReactNode;
  className?: string;
}

interface TabsContextType {
  value: string;
  setValue: (val: string) => void;
}

const TabsContext = React.createContext<TabsContextType | null>(null);

export function Tabs({ defaultValue, children, className }: TabsProps) {
  const [value, setValue] = useState(defaultValue);
  return (
    <TabsContext.Provider value={{ value, setValue }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabsList({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`flex gap-2 ${className}`}>{children}</div>;
}

export function TabsTrigger({
  value,
  children,
  className = "",
}: {
  value: string;
  children: ReactNode;
  className?: string;
}) {
  const ctx = React.useContext(TabsContext);
  if (!ctx) throw new Error("TabsTrigger must be inside <Tabs>");

  const isActive = ctx.value === value;

  return (
    <button
      onClick={() => ctx.setValue(value)}
      className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
        isActive
          ? "bg-slate-700 text-amber-400 border border-slate-600"
          : "bg-slate-900/60 text-slate-500 hover:text-slate-300 border border-slate-700/40"
      } ${className}`}
    >
      {children}
    </button>
  );
}

export function TabsContent({
  value,
  children,
  className = "",
}: {
  value: string;
  children: ReactNode;
  className?: string;
}) {
  const ctx = React.useContext(TabsContext);
  if (!ctx) return null;

  if (ctx.value !== value) return null;

  return <div className={className}>{children}</div>;
}
