// next_app/app/finops/page.tsx
// Página pública FinOps — asignación óptima model×max_tokens por ruta Lilly.
// Sin auth requerida. Datos hardcodeados desde la última ejecución del MILP solver.
// Esta página es informativa: la asignación óptima es una recomendación,
// no una decisión automática. Cada cambio requiere confirmación manual del operador.

export const metadata = {
  title: "FinOps — Abu Oracle",
  description: "Asignación óptima model × max_tokens por ruta Lilly. Solver MILP.",
};

// ── Datos del solver (última ejecución: 2026-04-05, N=1000, seed=42) ──────────

const SOLVER_META = {
  status: "Optimal",
  generatedAt: "2026-04-05",
  nUsers: 1000,
  pContinuationEmpirical: 0.036,
  baselineCostPerReq: 0.011656,
  optimalCostPerReq:  0.008287,
  savingsPerReq:      0.003369,
  savingsPct:         28.9,
};

type RouteRow = {
  route: string;
  baseModel: "sonnet" | "haiku";
  baseMaxTokens: number;
  optModel: "sonnet" | "haiku";
  optMaxTokens: number;
  deltaCost: number;
  notes: string;
  doctrinalRisk: "review" | "validated";
};

const ROUTES: RouteRow[] = [
  {
    route: "screen-open",
    baseModel: "sonnet", baseMaxTokens: 1024,
    optModel:  "sonnet", optMaxTokens:  2048,
    deltaCost: -0.003513,
    notes: "Elimina continuaciones (71% → ~5%)",
    doctrinalRisk: "validated",
  },
  {
    route: "planet",
    baseModel: "sonnet", baseMaxTokens: 1024,
    optModel:  "sonnet", optMaxTokens:  1024,
    deltaCost: 0,
    notes: "",
    doctrinalRisk: "validated",
  },
  {
    route: "technique_lot",
    baseModel: "haiku", baseMaxTokens: 2048,
    optModel:  "haiku", optMaxTokens:   768,
    deltaCost: 0,
    notes: "max_tokens sobre-provisionado (mean=415)",
    doctrinalRisk: "validated",
  },
  {
    route: "technique_firdaria",
    baseModel: "haiku", baseMaxTokens: 2048,
    optModel:  "haiku", optMaxTokens:   768,
    deltaCost: 0,
    notes: "max_tokens sobre-provisionado (mean=425)",
    doctrinalRisk: "validated",
  },
  {
    route: "technique_lunar",
    baseModel: "haiku", baseMaxTokens: 1536,
    optModel:  "haiku", optMaxTokens:  1536,
    deltaCost: 0,
    notes: "",
    doctrinalRisk: "validated",
  },
  {
    route: "city",
    baseModel: "haiku", baseMaxTokens: 1024,
    optModel:  "haiku", optMaxTokens:  1024,
    deltaCost: 0,
    notes: "",
    doctrinalRisk: "validated",
  },
  {
    route: "domain",
    baseModel: "sonnet", baseMaxTokens: 1024,
    optModel:  "haiku",  optMaxTokens:  1024,
    deltaCost: -0.012285,
    notes: "Mayor palanca de ahorro",
    doctrinalRisk: "review",
  },
  {
    route: "house",
    baseModel: "sonnet", baseMaxTokens: 1024,
    optModel:  "haiku",  optMaxTokens:  1024,
    deltaCost: -0.010217,
    notes: "",
    doctrinalRisk: "review",
  },
  {
    route: "sky",
    baseModel: "sonnet", baseMaxTokens: 1536,
    optModel:  "sonnet", optMaxTokens:  1536,
    deltaCost: 0,
    notes: "",
    doctrinalRisk: "validated",
  },
  {
    route: "transit",
    baseModel: "sonnet", baseMaxTokens: 1024,
    optModel:  "haiku",  optMaxTokens:  1024,
    deltaCost: -0.010965,
    notes: "",
    doctrinalRisk: "review",
  },
  {
    route: "chat",
    baseModel: "sonnet", baseMaxTokens: 2500,
    optModel:  "sonnet", optMaxTokens:  2500,
    deltaCost: 0,
    notes: "",
    doctrinalRisk: "validated",
  },
];

const SAVINGS_SCALE = [
  { n: 100,   monthly: 101.08  },
  { n: 500,   monthly: 505.40  },
  { n: 1000,  monthly: 1010.79 },
];

const R5_VIOLATIONS = [
  { route: "screen-open", cost: 0.023847, plans: "annual, monthly" },
  { route: "planet",      cost: 0.013167, plans: "annual" },
  { route: "sky",         cost: 0.013842, plans: "annual" },
  { route: "chat",        cost: 0.013152, plans: "annual" },
];

// ── Helpers UI ─────────────────────────────────────────────────────────────────

function ModelBadge({ model }: { model: "sonnet" | "haiku" }) {
  return model === "sonnet" ? (
    <span className="px-1.5 py-0.5 rounded text-xs font-mono bg-violet-500/20 text-violet-300 border border-violet-500/30">
      sonnet
    </span>
  ) : (
    <span className="px-1.5 py-0.5 rounded text-xs font-mono bg-teal-500/20 text-teal-300 border border-teal-500/30">
      haiku
    </span>
  );
}

function DeltaBadge({ delta }: { delta: number }) {
  if (delta === 0) return <span className="text-slate-500 font-mono text-xs">—</span>;
  return (
    <span className="font-mono text-xs text-emerald-400">
      −${Math.abs(delta).toFixed(6)}
    </span>
  );
}

function RiskBadge({ risk }: { risk: "review" | "validated" }) {
  return risk === "review" ? (
    <span className="inline-flex items-center gap-1 text-xs text-amber-400">
      <span>⚠️</span> revisar
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-xs text-emerald-400">
      <span>✅</span> validado
    </span>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function FinOpsPage() {
  const changed = ROUTES.filter(
    (r) => r.baseModel !== r.optModel || r.baseMaxTokens !== r.optMaxTokens
  );
  const toReview = changed.filter((r) => r.doctrinalRisk === "review");

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 px-6 py-10 max-w-5xl mx-auto">

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-2xl font-serif tracking-wide text-slate-100">
            FinOps — Asignación óptima de rutas Lilly
          </h1>
          <span className="px-2 py-0.5 rounded text-xs bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 font-mono">
            LP {SOLVER_META.status}
          </span>
        </div>
        <p className="text-sm text-slate-400 max-w-2xl">
          Resultado del solver MILP ({SOLVER_META.generatedAt}). Minimiza costo por request
          ponderado por tráfico de ruta. La tabla muestra la asignación actual de producción
          vs la asignación óptima calculada.{" "}
          <strong className="text-amber-400">
            Esta es una recomendación — cada cambio requiere confirmación manual del operador.
          </strong>
        </p>
      </div>

      {/* Savings strip */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {SAVINGS_SCALE.map(({ n, monthly }) => (
          <div
            key={n}
            className="rounded-lg border border-slate-700/60 bg-slate-900/60 px-5 py-4"
          >
            <div className="text-xs text-slate-500 mb-1">{n} usuarios · 300 req/mes</div>
            <div className="text-2xl font-mono text-emerald-400">
              ${monthly.toFixed(2)}
            </div>
            <div className="text-xs text-slate-500 mt-0.5">ahorro / mes</div>
          </div>
        ))}
        <div className="col-span-3 flex items-center gap-6 px-5 py-3 rounded-lg border border-slate-700/60 bg-slate-900/40">
          <div>
            <span className="text-xs text-slate-500">Ahorro/req</span>
            <span className="ml-2 font-mono text-emerald-400 text-sm">
              ${SOLVER_META.savingsPerReq.toFixed(6)}
            </span>
          </div>
          <div>
            <span className="text-xs text-slate-500">Reducción costo</span>
            <span className="ml-2 font-mono text-emerald-400 text-sm">
              {SOLVER_META.savingsPct}%
            </span>
          </div>
          <div>
            <span className="text-xs text-slate-500">P(continuación) empírico</span>
            <span className="ml-2 font-mono text-slate-300 text-sm">3.6%</span>
          </div>
          {/* Shadow price indicator */}
          <div className="ml-auto flex items-center gap-2">
            <span className="text-xs text-slate-500">Shadow price TPM</span>
            <span className="px-2 py-0.5 rounded text-xs bg-amber-500/15 text-amber-400 border border-amber-500/25">
              ⚡ activo @ N=1000
            </span>
          </div>
        </div>
      </div>

      {/* Assignment table */}
      <div className="mb-8">
        <h2 className="text-sm font-medium text-slate-400 uppercase tracking-widest mb-3">
          Asignación por ruta
        </h2>
        <div className="rounded-lg border border-slate-700/60 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700/60 bg-slate-900/80">
                <th className="text-left px-4 py-3 text-xs text-slate-500 font-normal">Ruta</th>
                <th className="text-left px-4 py-3 text-xs text-slate-500 font-normal">Actual</th>
                <th className="px-3 py-3 text-xs text-slate-500 font-normal">mt</th>
                <th className="text-left px-4 py-3 text-xs text-slate-500 font-normal">Óptimo</th>
                <th className="px-3 py-3 text-xs text-slate-500 font-normal">mt</th>
                <th className="text-right px-4 py-3 text-xs text-slate-500 font-normal">Δcost/req</th>
                <th className="text-center px-4 py-3 text-xs text-slate-500 font-normal">Riesgo doctrinal</th>
                <th className="text-left px-4 py-3 text-xs text-slate-500 font-normal">Nota</th>
              </tr>
            </thead>
            <tbody>
              {ROUTES.map((row, i) => {
                const isChanged = row.baseModel !== row.optModel || row.baseMaxTokens !== row.optMaxTokens;
                return (
                  <tr
                    key={row.route}
                    className={[
                      i % 2 === 0 ? "bg-slate-900/30" : "bg-slate-900/10",
                      isChanged ? "border-l-2 border-l-emerald-500/40" : "",
                    ].join(" ")}
                  >
                    <td className="px-4 py-2.5 font-mono text-xs text-slate-300">{row.route}</td>
                    <td className="px-4 py-2.5">
                      <ModelBadge model={row.baseModel} />
                    </td>
                    <td className="px-3 py-2.5 text-center font-mono text-xs text-slate-400">
                      {row.baseMaxTokens}
                    </td>
                    <td className="px-4 py-2.5">
                      <ModelBadge model={row.optModel} />
                    </td>
                    <td className="px-3 py-2.5 text-center font-mono text-xs text-slate-300">
                      {row.optMaxTokens}
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <DeltaBadge delta={row.deltaCost} />
                    </td>
                    <td className="px-4 py-2.5 text-center">
                      {isChanged ? (
                        <RiskBadge risk={row.doctrinalRisk} />
                      ) : (
                        <span className="text-slate-600 text-xs">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-xs text-slate-500">{row.notes}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Action items */}
      {toReview.length > 0 && (
        <div className="mb-8 rounded-lg border border-amber-500/20 bg-amber-500/5 px-5 py-4">
          <h3 className="text-sm font-medium text-amber-400 mb-2">
            ⚠️ Cambios que requieren validación doctrinal antes de deploy
          </h3>
          <p className="text-xs text-slate-400 mb-3">
            Estas rutas pasarían de Sonnet a Haiku. El modelo es más barato pero puede
            degradar la profundidad interpretativa en lecturas doctrinales complejas.
            Validar con al menos 3 cartas ciegas antes de activar en producción.
          </p>
          <div className="flex flex-wrap gap-2">
            {toReview.map((r) => (
              <span
                key={r.route}
                className="px-2.5 py-1 rounded font-mono text-xs bg-slate-800 border border-amber-500/30 text-amber-300"
              >
                {r.route} · −${Math.abs(r.deltaCost).toFixed(4)}/req
              </span>
            ))}
          </div>
        </div>
      )}

      {/* R5 diagnostic */}
      <div className="mb-8">
        <h2 className="text-sm font-medium text-slate-400 uppercase tracking-widest mb-3">
          R5 — Margen mínimo por request
        </h2>
        <p className="text-xs text-slate-500 mb-3">
          R5 exige que cada request genere margen ≥ $0.0008 (annual) / $0.001 (monthly).
          Las siguientes rutas violan R5 incluso con la asignación óptima — hallazgo
          estructural: el costo de Sonnet excede el umbral en rutas con output alto.
          R5 es satisfacible a nivel de <em>sesión</em> (mix de rutas baratas + caras).
        </p>
        <div className="rounded-lg border border-slate-700/60 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700/60 bg-slate-900/80">
                <th className="text-left px-4 py-2.5 text-xs text-slate-500 font-normal">Ruta</th>
                <th className="text-right px-4 py-2.5 text-xs text-slate-500 font-normal">Costo óptimo/req</th>
                <th className="text-left px-4 py-2.5 text-xs text-slate-500 font-normal">Planes afectados</th>
              </tr>
            </thead>
            <tbody>
              {R5_VIOLATIONS.map((v, i) => (
                <tr key={v.route} className={i % 2 === 0 ? "bg-slate-900/30" : "bg-slate-900/10"}>
                  <td className="px-4 py-2 font-mono text-xs text-slate-300">{v.route}</td>
                  <td className="px-4 py-2 text-right font-mono text-xs text-rose-400">
                    ${v.cost.toFixed(6)}
                  </td>
                  <td className="px-4 py-2 text-xs text-slate-400">{v.plans}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-600 mt-2">
          Umbral R5: annual ${(0.012329 - 0.0008).toFixed(6)} · monthly ${(0.016667 - 0.001).toFixed(6)}
        </p>
      </div>

      {/* Footer notes */}
      <div className="border-t border-slate-800 pt-6 space-y-2 text-xs text-slate-600">
        <p>
          <strong className="text-slate-500">Nota continuación:</strong>{" "}
          El simulador N=1000 reporta continuation_rate=6.5% (resultado ponderado observado).
          El solver usa 3.6% empírico (33/495 records de producción). No son el mismo dato:
          el 6.5% emerge del bug de screen-open (71.1% cont × 8.7% tráfico = 6.2%).
          El parámetro 3.6% es el fallback para rutas sin tasa empírica propia.
        </p>
        <p>
          <strong className="text-slate-500">Shadow price TPM:</strong>{" "}
          Activo a N=1000 (99.84% utilización Tier 2). El solver removió la restricción
          TPM como hard constraint (discrepancia en conteo de cache tokens) — se reporta
          como indicador.
        </p>
        <p>
          <strong className="text-slate-500">Fuente:</strong>{" "}
          scripts/finops/milp_solver.py · PuLP 3.3.0 / CBC 2.10.3 ·{" "}
          research/finops/load_simulation_results.json
        </p>
      </div>
    </div>
  );
}
