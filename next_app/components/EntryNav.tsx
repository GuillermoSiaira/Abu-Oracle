'use client';

export type EntryKey = 'panorama' | 'transits' | 'natal' | 'relocation';

export interface EntryNavProps {
  activeEntry: EntryKey | null;
  onSelect: (entry: EntryKey) => void;
  disabled: boolean;
}

interface EntryDef {
  key: EntryKey;
  icon: string;
  labelDesktop: string;
  labelMobile: string;
}

const ENTRIES: EntryDef[] = [
  { key: 'panorama',    icon: '🔭', labelDesktop: 'Panorama actual', labelMobile: 'Panorama'  },
  { key: 'transits',   icon: '⚡', labelDesktop: 'Tránsitos',        labelMobile: 'Tránsitos' },
  { key: 'natal',      icon: '☿', labelDesktop: 'Carta natal',       labelMobile: 'Carta'     },
  { key: 'relocation', icon: '🌍', labelDesktop: 'Relocalización',   labelMobile: 'Reloc.'    },
];

export function EntryNav({ activeEntry, onSelect, disabled }: EntryNavProps) {
  return (
    <>
      {/* ── Desktop: vertical stack ─────────────────────────────── */}
      <nav
        aria-label="Oracle entry points"
        className={`hidden md:flex flex-col gap-0.5 px-2 py-2 border-b border-slate-800 shrink-0
          ${disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''}`}
      >
        {ENTRIES.map(({ key, icon, labelDesktop }) => {
          const isActive = activeEntry === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => onSelect(key)}
              disabled={disabled}
              className={`flex items-center gap-2.5 w-full px-3 py-2 rounded-sm text-left text-xs font-mono
                transition-colors
                ${isActive
                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                }`}
            >
              <span className="text-sm leading-none shrink-0">{icon}</span>
              <span className="leading-tight">{labelDesktop}</span>
            </button>
          );
        })}
      </nav>

      {/* ── Mobile: horizontal tab bar pinned to bottom ─────────── */}
      <nav
        aria-label="Oracle entry points"
        className={`md:hidden flex flex-row border-t border-slate-800 shrink-0
          ${disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''}`}
        style={{ height: '56px' }}
      >
        {ENTRIES.map(({ key, icon, labelMobile }) => {
          const isActive = activeEntry === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => onSelect(key)}
              disabled={disabled}
              className={`flex flex-col items-center justify-center flex-1 gap-0.5 text-[10px] font-mono
                transition-colors
                ${isActive
                  ? 'text-amber-400 bg-amber-500/10 border-t-2 border-amber-500/50'
                  : 'text-slate-500 hover:text-slate-300 border-t-2 border-transparent'
                }`}
            >
              <span className="text-sm leading-none">{icon}</span>
              <span className="leading-tight">{labelMobile}</span>
            </button>
          );
        })}
      </nav>
    </>
  );
}

export default EntryNav;
