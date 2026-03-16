'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/lib/store';
import { UI, DEMO_DESCRIPTIONS } from '@/lib/i18n';
import { runAbuAnalyze } from '@/services/abu';

// ---------------------------------------------------------------------------
// Static data — mirrors output/demo/index.json (subjects + hardcoded metadata)
// ---------------------------------------------------------------------------

interface DemoSubject {
  slug: string;
  display_name: string;
  birth_datetime: string; // UTC ISO
  natal_lat: number;
  natal_lon: number;
  birth_city: string;
  years: string;
  rodden: string;
}

const SUBJECTS: DemoSubject[] = [
  {
    slug: 'einstein',
    display_name: 'Albert Einstein',
    birth_datetime: '1879-03-14T10:50:02+00:00',
    natal_lat: 48.39833333333333,
    natal_lon: 9.991666666666665,
    birth_city: 'Ulm, Alemania',
    years: '1879 – 1955',
    rodden: 'AA',
  },
  {
    slug: 'freud',
    display_name: 'Sigmund Freud',
    birth_datetime: '1856-05-06T17:17:25+00:00',
    natal_lat: 49.64083333333333,
    natal_lon: 18.145,
    birth_city: 'Příbor, Rep. Checa',
    years: '1856 – 1939',
    rodden: 'AA',
  },
  {
    slug: 'jung',
    display_name: 'Carl G. Jung',
    birth_datetime: '1875-07-26T18:54:44+00:00',
    natal_lat: 47.593333333333334,
    natal_lon: 9.318055555555555,
    birth_city: 'Kesswil, Suiza',
    years: '1875 – 1961',
    rodden: 'A',
  },
  {
    slug: 'tesla',
    display_name: 'Nikola Tesla',
    birth_datetime: '1856-07-09T22:58:45+00:00',
    natal_lat: 44.56388888888888,
    natal_lon: 15.318055555555555,
    birth_city: 'Smiljan, Croacia',
    years: '1856 – 1943',
    rodden: 'B',
  },
  {
    slug: 'gandhi',
    display_name: 'Mohandas Gandhi',
    birth_datetime: '1869-10-02T02:33:22+00:00',
    natal_lat: 21.642222222222223,
    natal_lon: 69.60916666666667,
    birth_city: 'Porbandar, India',
    years: '1869 – 1948',
    rodden: 'A',
  },
  {
    slug: 'frida',
    display_name: 'Frida Kahlo',
    birth_datetime: '1907-07-06T15:06:38+00:00',
    natal_lat: 19.328888888888887,
    natal_lon: -99.16027777777778,
    birth_city: 'Coyoacán, México',
    years: '1907 – 1954',
    rodden: 'AA',
  },
  {
    slug: 'picasso',
    display_name: 'Pablo Picasso',
    birth_datetime: '1881-10-25T23:32:41+00:00',
    natal_lat: 36.72027777777778,
    natal_lon: -4.420277777777778,
    birth_city: 'Málaga, España',
    years: '1881 – 1973',
    rodden: 'AA',
  },
  {
    slug: 'vangogh',
    display_name: 'Vincent Van Gogh',
    birth_datetime: '1853-03-30T10:41:23+00:00',
    natal_lat: 51.47166666666667,
    natal_lon: 4.655555555555556,
    birth_city: 'Zundert, Países Bajos',
    years: '1853 – 1890',
    rodden: 'AA',
  },
  {
    slug: 'borges',
    display_name: 'Jorge Luis Borges',
    birth_datetime: '1899-08-24T07:46:48+00:00',
    natal_lat: -34.613055555555555,
    natal_lon: -58.37722222222222,
    birth_city: 'Buenos Aires, Argentina',
    years: '1899 – 1986',
    rodden: 'AA',
  },
  {
    slug: 'bowie',
    display_name: 'David Bowie',
    birth_datetime: '1947-01-08T09:15:00+00:00',
    natal_lat: 51.50861111111111,
    natal_lon: -0.12583333333333302,
    birth_city: 'Brixton, Londres',
    years: '1947 – 2016',
    rodden: 'A',
  },
];

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function DemoPage() {
  const router = useRouter();
  const { lang, setBirthData, setAbuData, setIsLoading, setError, setIsDemo } = useAppStore();
  const t = UI[lang as keyof typeof UI] ?? UI.es;

  const [loadingSlug, setLoadingSlug] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleSelect(subject: DemoSubject) {
    if (loadingSlug) return;
    setLoadingSlug(subject.slug);
    setLocalError(null);
    setError(null);

    const birthDataPayload = {
      birthDate: subject.birth_datetime,
      lat: subject.natal_lat,
      lon: subject.natal_lon,
      city: subject.birth_city,
      userName: subject.display_name,
      residenceCity: subject.birth_city,
      residenceLat: subject.natal_lat,
      residenceLon: subject.natal_lon,
      futureCity: null,
      futureLat: null,
      futureLon: null,
      futureDate: null,
    };

    try {
      setIsLoading(true);
      setIsDemo(true);
      setBirthData(birthDataPayload);

      const abuRes = await runAbuAnalyze({
        person: { name: subject.display_name },
        birth: {
          date: subject.birth_datetime,
          lat: subject.natal_lat,
          lon: subject.natal_lon,
        },
        current: {
          lat: subject.natal_lat,
          lon: subject.natal_lon,
          date: new Date().toISOString(),
        },
      });

      setAbuData(abuRes);
      router.push('/chart');
    } catch (err: any) {
      console.error('[Demo] Error:', err);
      setLocalError(err.message || 'Error inesperado.');
      setIsDemo(false);
    } finally {
      setIsLoading(false);
      setLoadingSlug(null);
    }
  }

  const desc = DEMO_DESCRIPTIONS;

  return (
    <main className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto px-6 py-10 space-y-8">

        {/* Header */}
        <div className="space-y-1 text-center">
          <h1
            className="text-3xl tracking-[0.12em] text-amber-400/90"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            {t.demoPageTitle}
          </h1>
          <p className="text-[11px] font-mono text-slate-500 tracking-wider">
            {t.demoPageSubtitle}
          </p>
        </div>

        <div className="w-16 h-px bg-amber-500/20 mx-auto" />

        {localError && (
          <p className="text-red-400 text-xs font-mono text-center">⚠ {localError}</p>
        )}

        {/* Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {SUBJECTS.map((s) => {
            const isLoading = loadingSlug === s.slug;
            const isDisabled = !!loadingSlug && !isLoading;
            return (
              <button
                key={s.slug}
                onClick={() => handleSelect(s)}
                disabled={isDisabled || isLoading}
                className={`
                  group text-left px-4 py-3.5 rounded-sm border transition-all
                  bg-[#080808]
                  ${isLoading
                    ? 'border-amber-500/50 bg-amber-500/5 cursor-wait'
                    : isDisabled
                      ? 'border-slate-800/40 opacity-40 cursor-not-allowed'
                      : 'border-slate-800 hover:border-amber-500/40 hover:bg-amber-500/5 cursor-pointer'
                  }
                `}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p
                      className="text-amber-400/90 text-base tracking-wide truncate"
                      style={{ fontFamily: 'var(--font-serif)' }}
                    >
                      {s.display_name}
                    </p>
                    <p className="text-[10px] font-mono text-slate-600 mt-0.5">
                      {s.years} · {s.birth_city}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1.5 leading-snug">
                      {desc[s.slug]?.[lang as keyof typeof desc[typeof s.slug]] ?? desc[s.slug]?.es}
                    </p>
                  </div>
                  <div className="shrink-0 flex flex-col items-end gap-1 pt-0.5">
                    <span className="text-[9px] font-mono text-slate-600 border border-slate-800 px-1.5 py-0.5 rounded-sm">
                      {s.rodden}
                    </span>
                    {isLoading && (
                      <span className="text-[9px] font-mono text-amber-500 animate-pulse">
                        {t.demoLoading}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            );
          })}
        </div>

      </div>
    </main>
  );
}
