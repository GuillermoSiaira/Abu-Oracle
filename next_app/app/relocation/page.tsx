import { Suspense } from "react";
import RelocationClient from "./RelocationClient";

export default function RelocationPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center h-full text-slate-500">
          Cargando relocalización…
        </div>
      }
    >
      <RelocationClient />
    </Suspense>
  );
}
