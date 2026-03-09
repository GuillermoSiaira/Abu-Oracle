import BirthDataPanel from "@/components/birth-data-panel";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-[#0b0b0b] to-[#050505]">
      <div className="container mx-auto py-16 space-y-14">
        
        {/* HEADER — Technical / Grant Narrative */}
        <header className="text-center space-y-3">
          <h1 className="text-4xl md:text-5xl font-serif tracking-tight text-amber-500">
            ABU — Astrological Computation Engine
          </h1>

          <p className="text-slate-400 max-w-2xl mx-auto text-sm md:text-base">
            Deterministic astronomical computation using high-precision ephemerides,
            geospatial resolution (WGS84) and reproducible temporal anchors.
          </p>
        </header>

        {/* INPUT PANEL */}
        <div className="max-w-2xl mx-auto">
          <BirthDataPanel />
        </div>

      </div>
    </main>
  );
}
