"use client";

import { useSearchParams } from "next/navigation";
import HFRelocationMap from "@/components/HFRelocationMap";

const DEFAULT_SUBJECT = "1000";

export default function RelocationMapClient() {
  const params = useSearchParams();
  const subject = params.get("subject") ?? DEFAULT_SUBJECT;
  const geojsonUrl = `/geojson/subject_${subject}_hf.geojson`;
  const rankingUrl = `/rankings/subject_${subject}_ranking.json`;

  return (
    <div className="px-4 py-6 space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Relocation Map (HF v3)</h1>
        <p className="text-sm text-gray-600 mt-1">
          Usa <code>scripts/export_hf_geojson.py</code> para generar <code>.geojson</code> y cópialo a <code>public/geojson</code>.
          Ranking opcional en <code>public/rankings</code>. Cambia el sujeto con <code>?subject=123</code>.
        </p>
      </div>
      <HFRelocationMap geojsonUrl={geojsonUrl} rankingUrl={rankingUrl} />
    </div>
  );
}
