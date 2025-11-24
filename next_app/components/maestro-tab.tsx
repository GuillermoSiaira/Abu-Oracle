import { useAppStore } from "@/lib/store"

export function MaestroTab() {
  const lillyData = useAppStore((s) => s.lillyData)

  // Nada aún
  if (!lillyData?.maestro) {
    return (
      <div className="text-center py-8 text-sm opacity-70">
        El JSON Maestro todavía no está disponible.
        <br />
        Genera una interpretación primero.
      </div>
    )
  }

  return (
    <pre className="p-4 text-xs bg-black/20 rounded overflow-x-auto whitespace-pre-wrap">
      {JSON.stringify(lillyData.maestro, null, 2)}
    </pre>
  )
}
