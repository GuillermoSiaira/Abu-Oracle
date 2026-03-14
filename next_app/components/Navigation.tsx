'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Globe } from 'lucide-react';

const navLinks = [
  { href: '/', label: 'Home' },
  { href: '/chart', label: 'Carta' },
  { href: '/relocation', label: 'Relocalización', icon: Globe },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <header className="w-full h-14 bg-slate-950 border-b border-slate-800 flex items-center px-6 select-none">
      <div className="flex items-center gap-2">
        <Link href="/" className="text-amber-400 font-serif text-lg tracking-wide hover:text-amber-300 transition-colors">
          ABU ORACLE
        </Link>
        <span className="text-slate-500 text-sm hidden sm:inline">
          — Astrological Intelligence Engine
        </span>
      </div>
      <nav className="ml-8 flex items-center gap-1">
        {navLinks.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors ${
                active
                  ? 'bg-amber-500/10 text-amber-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              {Icon && <Icon className="w-3.5 h-3.5" />}
              {label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
