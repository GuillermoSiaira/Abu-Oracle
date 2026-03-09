import dynamic from "next/dynamic";
import { Suspense } from "react";

export const dynamic = "force-dynamic";

const RelocationMapClient = dynamic(() => import("./RelocationMapClient"), {
  ssr: false,
  loading: () => <div className="p-6">Cargando mapa…</div>,
});

export default function RelocationMapPage() {
  return (
    <Suspense fallback={<div className="p-6">Cargando mapa…</div>}>
      <RelocationMapClient />
    </Suspense>
  );
}
