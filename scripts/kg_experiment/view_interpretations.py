#!/usr/bin/env python3
"""
Visor de interpretaciones KG-C03.

Toma un results_*.json (y, si existe, el cross_judge_*.json del mismo diseño)
y produce un Markdown legible con, por cada sujeto:

  - Respuesta A (modelo + formato) completa
  - Respuesta B (modelo + formato) completa
  - Tabla de scores por criterio: Claude A/B + Gemini A/B
  - Ganador por juez

Permite ver QUÉ se evalúa como diferencia de calidad doctrinal — el contenido
real de cada lectura y cómo lo puntuó cada juez, lado a lado.

No llama a ningún modelo ni a Abu Engine. Solo lee JSON ya generados.

Uso:
    python scripts/kg_experiment/view_interpretations.py --design v5_natal_kg_haiku
    python scripts/kg_experiment/view_interpretations.py --design v5_natal_kg_haiku --subject gs004
    python scripts/kg_experiment/view_interpretations.py --design v6_natal_kg_gemini_flash --out lecturas_v6.md
    # Sin --out escribe a stdout. Con --out escribe el archivo .md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CRITERIA = [
    "coherencia_doctrinal",
    "especificidad",
    "multi_hop_reasoning",
    "ausencia_de_generico",
    "sintesis",
]


def _latest(base: Path, prefix: str) -> Path | None:
    cands = sorted(base.glob(f"{prefix}_*.json"), key=lambda p: p.stat().st_mtime)
    return cands[-1] if cands else None


def _winner(a: float, b: float) -> str:
    if b > a:
        return "B"
    if a > b:
        return "A"
    return "tie"


def _scores_table(claude: dict, gemini: dict | None) -> list[str]:
    """Tabla markdown de scores por criterio."""
    c_a = (claude or {}).get("scores_a", {}) or {}
    c_b = (claude or {}).get("scores_b", {}) or {}
    g_a = (gemini or {}).get("scores_a", {}) or {} if gemini else {}
    g_b = (gemini or {}).get("scores_b", {}) or {} if gemini else {}

    lines = []
    if gemini:
        lines.append("| Criterio | Claude A | Claude B | Gemini A | Gemini B |")
        lines.append("|---|---|---|---|---|")
        for crit in CRITERIA:
            lines.append(
                f"| {crit} | {c_a.get(crit, '?')} | {c_b.get(crit, '?')} "
                f"| {g_a.get(crit, '?')} | {g_b.get(crit, '?')} |"
            )
        ta, tb = c_a.get("total", "?"), c_b.get("total", "?")
        gta, gtb = g_a.get("total", "?"), g_b.get("total", "?")
        lines.append(f"| **TOTAL** | **{ta}** | **{tb}** | **{gta}** | **{gtb}** |")
    else:
        lines.append("| Criterio | Claude A | Claude B |")
        lines.append("|---|---|---|")
        for crit in CRITERIA:
            lines.append(f"| {crit} | {c_a.get(crit, '?')} | {c_b.get(crit, '?')} |")
        ta, tb = c_a.get("total", "?"), c_b.get("total", "?")
        lines.append(f"| **TOTAL** | **{ta}** | **{tb}** |")
    return lines


def build_markdown(design: str, results: list[dict], cross: list[dict] | None,
                   subject_filter: str | None) -> str:
    cross_by_id = {}
    if cross:
        for c in cross:
            cross_by_id[c.get("subject_id")] = c.get("cross_scores_gemini")

    out: list[str] = []
    out.append(f"# Interpretaciones — {design}")
    out.append("")
    out.append("A = JSON narrativo · B = KG tripletas. Mismo contexto informativo, distinto formato/modelo.")
    out.append("")

    for r in results:
        if "scores" not in r:
            continue
        sid = r.get("subject_id")
        if subject_filter and sid != subject_filter:
            continue
        name = r.get("subject_name", sid)
        ua = r.get("usage_a", {}) or {}
        ub = r.get("usage_b", {}) or {}
        model_a = ua.get("model", "?")
        model_b = ub.get("model", "?")
        prov_a = ua.get("provider", "anthropic")
        prov_b = ub.get("provider", "anthropic")

        claude_scores = r.get("scores", {})
        gemini_scores = cross_by_id.get(sid)

        ca_tot = float(claude_scores.get("total_a", 0))
        cb_tot = float(claude_scores.get("total_b", 0))

        out.append("")
        out.append("=" * 70)
        out.append(f"## {name}  (`{sid}`)")
        out.append("")
        # Veredicto rápido
        verdict = f"Claude: A={ca_tot:.0f} B={cb_tot:.0f} (gana {_winner(ca_tot, cb_tot)})"
        if gemini_scores:
            ga_tot = float(gemini_scores.get("total_a", 0))
            gb_tot = float(gemini_scores.get("total_b", 0))
            verdict += f"  ·  Gemini: A={ga_tot:.0f} B={gb_tot:.0f} (gana {_winner(ga_tot, gb_tot)})"
        out.append(f"**{verdict}**")
        out.append("")
        out.extend(_scores_table(claude_scores, gemini_scores))
        out.append("")
        out.append(f"### 🟦 Respuesta A — JSON · `{model_a}` ({prov_a})")
        out.append("")
        out.append((r.get("response_a") or "").strip())
        out.append("")
        out.append(f"### 🟩 Respuesta B — KG · `{model_b}` ({prov_b})")
        out.append("")
        out.append((r.get("response_b") or "").strip())
        out.append("")

    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="Visor de interpretaciones KG-C03")
    ap.add_argument("--design", required=True, help="ID del diseño (ej: v5_natal_kg_haiku)")
    ap.add_argument("--subject", default=None, help="Filtrar a un subject_id (ej: gs004)")
    ap.add_argument("--out", default=None, help="Archivo .md de salida (default: stdout)")
    ap.add_argument("--results", default=None, help="Path explícito a un results_*.json")
    args = ap.parse_args()

    base = REPO_ROOT / "data" / "kg_experiment" / args.design
    if not base.exists():
        raise SystemExit(f"ERROR: no existe {base}")

    results_path = Path(args.results) if args.results else _latest(base, "results")
    if not results_path or not results_path.exists():
        raise SystemExit(f"ERROR: no hay results_*.json en {base}")

    cross_path = _latest(base, "cross_judge")

    with open(results_path, encoding="utf-8") as f:
        results = json.load(f)
    cross = None
    if cross_path:
        with open(cross_path, encoding="utf-8") as f:
            cross = json.load(f)

    md = build_markdown(args.design, results, cross, args.subject)

    # Banner informativo a stderr (no contamina el markdown en stdout)
    print(f"[results] {results_path.name}", file=sys.stderr)
    print(f"[cross  ] {cross_path.name if cross_path else 'ninguno'}", file=sys.stderr)

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(md, encoding="utf-8")
        print(f"[escrito] {out_path}", file=sys.stderr)
    else:
        print(md)


if __name__ == "__main__":
    main()
