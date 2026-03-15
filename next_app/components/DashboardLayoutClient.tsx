'use client';

// Wrapper client que habilita ssr:false para DashboardLayout y toda su sub-árbol.
// dynamic+ssr:false solo puede usarse en Client Components, no en layout.tsx (Server Component).
import dynamic from 'next/dynamic';
import type { ReactNode } from 'react';

const DashboardLayout = dynamic(() => import('./DashboardLayout'), { ssr: false });

export default function DashboardLayoutClient({ children }: { children: ReactNode }) {
  return <DashboardLayout>{children}</DashboardLayout>;
}
