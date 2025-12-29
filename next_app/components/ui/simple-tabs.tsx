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
      className={`px-3 py-1 rounded-md border ${
        isActive ? "bg-black text-white" : "bg-white text-black"
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
