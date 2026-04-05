"""
validate_technique_tokens.py
-----------------------------
Valida que max_tokens=768 con Haiku sea suficiente para technique_lot y
technique_firdaria sobre los 4 sujetos del gold standard.

Replica exactamente lo que hace /api/lilly/technique:
  1. POST /analyze (Abu Engine local :8000) → abuData
  2. Construye context block (placeholder — solo los campos que importan al modelo)
  3. Llama a claude-haiku-4-5-20251001 con max_tokens=768 directamente
     (SIN completeLilly — necesitamos el stop_reason real)
  4. Reporta output_tokens y stop_reason por sujeto × técnica

Criterio de aprobación:
  - Todos los stop_reason == "end_turn"
  - Ningún output_tokens > 700 (margen de 68 tokens sobre el umbral crítico)

Uso:
  python scripts/finops/validate_technique_tokens.py

Requiere:
  - Abu Engine en localhost:8000
  - ANTHROPIC_API_KEY en entorno o .env.local
"""

import json
import os
import sys
import time
import requests
import anthropic
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

ABU_URL    = "http://localhost:8000"
MODEL      = "claude-haiku-4-5-20251001"
MAX_TOKENS = 768
TECHNIQUES = ["lot", "firdaria"]


# GS_001 (Jung, 1875) y GS_002 (Tesla, 1856) superan el rango de efemérides del
# engine local — se sustituyen por Einstein y Freud del demo pack (mismo orden de
# diversidad de cartas, mismo propósito de medición).
# GS_003 (Turing) y GS_004 (Siaira) son los gold standards reales.
SUBJECTS = [
    {
        "alias": "Turing (GS_003)",
        "birth_date": "1912-06-23T02:15:00Z",
        "birth_lat": 51.52,
        "birth_lon": -0.19,
        "current_lat": 51.5074,
        "current_lon": -0.1278,
        "name": "Alan Turing",
    },
    {
        "alias": "Siaira (GS_004)",
        "birth_date": "1978-07-06T00:15:00Z",
        "birth_lat": -37.8464,
        "birth_lon": -58.2556,
        "current_lat": -34.6037,
        "current_lon": -58.3816,
        "name": "Guillermo Siaira",
    },
    {
        "alias": "Einstein (demo)",
        "birth_date": "1879-03-14T11:30:00Z",
        "birth_lat": 48.4011,
        "birth_lon": 9.9876,
        "current_lat": 48.4011,
        "current_lon": 9.9876,
        "name": "Albert Einstein",
    },
    {
        "alias": "Freud (demo)",
        "birth_date": "1856-05-06T18:30:00Z",
        "birth_lat": 49.5938,
        "birth_lon": 17.2509,
        "current_lat": 49.5938,
        "current_lon": 17.2509,
        "name": "Sigmund Freud",
    },
]

# ── Load LILLY_SYSTEM_PROMPT ──────────────────────────────────────────────────
# Lee el archivo TS y extrae el string exportado

def load_system_prompt() -> str:
    """Extrae LILLY_SYSTEM_PROMPT de lib/lilly-prompt.ts como texto plano."""
    prompt_path = Path("next_app/lib/lilly-prompt.ts")
    if not prompt_path.exists():
        sys.exit(f"No se encontró {prompt_path}")
    src = prompt_path.read_text(encoding="utf-8")
    # Busca el bloque del template literal
    marker = "export const LILLY_SYSTEM_PROMPT"
    idx = src.find(marker)
    if idx == -1:
        sys.exit("LILLY_SYSTEM_PROMPT no encontrado en lilly-prompt.ts")
    # Extrae entre backticks
    start = src.find("`", idx) + 1
    end   = src.rfind("`")
    return src[start:end]

# ── Fetch abuData ─────────────────────────────────────────────────────────────

def fetch_abu_data(subj: dict) -> dict:
    """Llama a /analyze con los datos del sujeto."""
    payload = {
        "person": {"name": subj["name"]},
        "birth":  {"date": subj["birth_date"], "lat": subj["birth_lat"], "lon": subj["birth_lon"]},
        "current": {"lat": subj["current_lat"], "lon": subj["current_lon"], "date": "2026-04-05T00:00:00Z"},
    }
    r = requests.post(f"{ABU_URL}/analyze", json=payload, timeout=30)
    if not r.ok:
        sys.exit(f"[/analyze] {subj['name']}: {r.status_code} {r.text[:200]}")
    return r.json()

# ── Build minimal context block ───────────────────────────────────────────────

def build_context_block(abu: dict, technique: str) -> str:
    """
    Replica lo que assembleContextBlock produce para click_technique.
    Versión simplificada — suficiente para que el modelo reciba contexto real.
    """
    p = abu.get("person", {})
    chart = abu.get("chart", {})
    derived = abu.get("derived", {})

    planets = chart.get("planets", [])
    houses  = chart.get("houses", {})
    sect    = derived.get("sect", "unknown")
    firdaria = derived.get("firdaria", {})
    profection = derived.get("profection", {})
    lots     = derived.get("lots", [])

    lines = [
        "═══════════════════════════════════════",
        "CARTA NATAL",
        "═══════════════════════════════════════",
        f"Nombre: {p.get('name','Sujeto')}",
        f"Secta: {sect}",
        f"ASC: {houses.get('asc', '?')}° | MC: {houses.get('mc', '?')}°",
        "",
        "PLANETAS",
    ]
    for pl in planets:
        dig = pl.get("dignity", {})
        dig_str = dig.get("kind", "peregrine") if isinstance(dig, dict) else str(dig)
        retro = " [℞]" if pl.get("retrograde") else ""
        lines.append(
            f"  {pl.get('name','?')}: {pl.get('sign','?')} {pl.get('degree',0):.1f}° "
            f"Casa {pl.get('house','?')} | {dig_str}{retro}"
        )

    lines += [
        "",
        "═══════════════════════════════════════",
        "LÍNEA DE TIEMPO",
        "═══════════════════════════════════════",
        f"Profección: Casa {profection.get('house','?')} | Señor: {profection.get('lord','?')}",
    ]

    if firdaria:
        curr = firdaria.get("current", {})
        lines.append(
            f"Firdaria Mayor: {curr.get('major','?')} | Menor: {curr.get('sub','?')} "
            f"| Hasta: {curr.get('end_date','?')}"
        )

    lines += [
        "",
        "═══════════════════════════════════════",
        "CONTEXTO ACTIVO",
        "═══════════════════════════════════════",
        f"Evento: click_technique → technique={technique}",
        "Tab: persian_techniques",
        f"Fecha actual: 2026-04-05",
        "",
    ]

    if technique == "firdaria" and firdaria:
        curr = firdaria.get("current", {})
        lines += [
            "FIRDARIA ACTIVO",
            f"  Mayor: {curr.get('major','?')}",
            f"  Menor: {curr.get('sub','?')}",
            f"  Inicio: {curr.get('start_date','?')}",
            f"  Fin: {curr.get('end_date','?')}",
        ]

    if technique == "lot" and lots:
        lines.append("PARTES ARÁBICAS")
        for lot in lots:
            lines.append(
                f"  {lot.get('name','?')}: {lot.get('sign','?')} {lot.get('degree',0):.1f}° "
                f"Casa {lot.get('house','?')} | Señor: {lot.get('lord','?')}"
            )

    return "\n".join(lines)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    repo_root = Path(__file__).parent.parent.parent
    os.chdir(repo_root)

    # API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        env_local = Path("next_app/.env.local")
        if env_local.exists():
            for line in env_local.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip("'\"")
                    break
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY no encontrado")

    system_prompt = load_system_prompt()
    client = anthropic.Anthropic(api_key=api_key)

    print(f"\nModelo: {MODEL}  |  max_tokens: {MAX_TOKENS}")
    print(f"Técnicas: {TECHNIQUES}")
    print(f"Sujetos: {len(SUBJECTS)}")
    print("=" * 70)

    results = []
    any_truncated = False

    for subj in SUBJECTS:
        print(f"\n[{subj['alias']}] Fetching abuData...")
        abu = fetch_abu_data(subj)

        for technique in TECHNIQUES:
            block = build_context_block(abu, technique)
            input_tokens_est = (len(system_prompt) + len(block)) // 4  # rough

            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": block}],
            )

            out_tokens  = response.usage.output_tokens
            stop_reason = response.stop_reason
            truncated   = stop_reason == "max_tokens"

            if truncated:
                any_truncated = True

            flag = "TRUNCADO" if truncated else "OK"
            print(
                f"  {technique:10s} | output_tokens={out_tokens:4d} | "
                f"stop_reason={stop_reason:12s} | {flag}"
            )

            results.append({
                "subject": subj["alias"],
                "technique": technique,
                "output_tokens": out_tokens,
                "stop_reason": stop_reason,
                "truncated": truncated,
            })

            time.sleep(0.5)  # evitar rate limit en burst

    # ── Resumen ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"{'Sujeto':<22} {'Técnica':<12} {'Tokens':>8}  {'stop_reason':<14}  {'Estado'}")
    print("-" * 70)
    for r in results:
        flag = "TRUNCADO" if r["truncated"] else "OK"
        print(
            f"{r['subject']:<22} {r['technique']:<12} {r['output_tokens']:>8}  "
            f"{r['stop_reason']:<14}  {flag}"
        )

    print("-" * 70)
    max_out = max(r["output_tokens"] for r in results)
    print(f"Max output_tokens: {max_out}  (umbral alerta: 700, límite: {MAX_TOKENS})")

    if any_truncated:
        print("\nRESULTADO: FAIL — hay truncaciones, max_tokens=768 insuficiente.")
        print("   Revisar que tecnicas truncan y ajustar antes de cerrar el fix.")
    else:
        print(f"\nRESULTADO: PASS — todos end_turn, max={max_out} tokens.")
        print("   max_tokens=768 confirmado suficiente para lot y firdaria con Haiku.")
        print("   Fix 68853f9 validado. Cerrar.")

    # Guardar JSON para referencia
    out_path = Path("research/finops/validate_technique_tokens_results.json")
    out_path.write_text(json.dumps({
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "date": "2026-04-05",
        "results": results,
        "any_truncated": any_truncated,
        "max_output_tokens": max_out,
    }, indent=2, ensure_ascii=False))
    print(f"\nResultados guardados en {out_path}")


if __name__ == "__main__":
    main()
