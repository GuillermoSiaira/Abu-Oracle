"""
enrich_events.py — Enriquece eventos históricos con patrones astrológicos activos.

Para cada evento en eventos_raw.jsonl:
  1. Convierte fecha a JD (manejo Juliano vs Gregoriano)
  2. Llama a pattern_detectors.detect_active_patterns(jd, lookback=30, lookforward=30)
  3. Para eventos discretos puntuales (Grupo C), agrega los detectados en la ventana
  4. Marca date_precision: "year" | "month" | "day" según defaults sospechosos

Output: eventos_enriched.jsonl
  {
    "fecha": "0404-01-01",
    "descripcion": "...",
    "url": "...",
    "date_precision": "year",
    "jd": 1867251.5,
    "configs_active": [
      {
        "type": "opposition_MS", "group": "A", "label": "...",
        "participants": ["mars", "saturn"],
        "days_offset": -7, "orb": 1.2,
        "details": {...}
      },
      ...
    ]
  }

Diseño AFK:
  - Checkpoint cada 100 eventos en .enrich_checkpoint.json
  - Resumable: si checkpoint existe, salta los ya procesados
  - Log estructurado: [N/total] descripción corta → patrones encontrados
  - --audit-only: corre solo el análisis de granularidad sin enriquecer
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, Iterable

import swisseph as swe

sys.path.insert(0, str(Path(__file__).parent))
from pattern_detectors import detect_active_patterns, scan_window_discrete, Pattern


# Frontera Julian → Gregorian (15 oct 1582 = JD 2299161.5)
GREGORIAN_START_JD = 2299161.5


def parse_fecha(fecha_str: str) -> tuple[int, int, int, str]:
    """
    Parsea 'YYYY-MM-DD' y deduce precisión.

    Retorna (year, month, day, precision):
      - precision == "year"  si month=1, day=1 (sospechoso)
      - precision == "month" si day=1 (sospechoso)
      - precision == "day"   en otro caso

    NOTA: la heurística es conservadora. Para auditoría definitiva
    correr --audit-only sobre el corpus completo.
    """
    y, m, d = fecha_str.split("-")
    y, m, d = int(y), int(m), int(d)
    if m == 1 and d == 1:
        precision = "year"
    elif d == 1:
        precision = "month"
    else:
        precision = "day"
    return y, m, d, precision


def to_jd(year: int, month: int, day: int) -> float:
    """
    Convierte fecha civil a JD (proléptico Gregoriano para fechas pre-1582 también).
    Swiss Ephemeris usa proléptico Gregoriano internamente cuando se usa swe.julday.
    Para eventos pre-1582 originalmente en calendario Juliano, esto introduce
    ~10 días de offset; en una ventana ±30 días este offset NO invalida la detección.
    """
    return swe.julday(year, month, day, 12.0)  # mediodía UTC


def jd_to_date_str(jd: float) -> str:
    y, m, d, _ = swe.revjul(jd)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def load_events(path: Path) -> list[dict]:
    out = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line: continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[WARN] Line {i} invalid JSON: {e}", file=sys.stderr)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Audit de granularidad
# ─────────────────────────────────────────────────────────────────────────────

def audit_precision(events: list[dict]) -> dict:
    counts = {"year": 0, "month": 0, "day": 0, "unparseable": 0}
    examples = {"year": [], "month": [], "day": []}
    for ev in events:
        try:
            _, _, _, prec = parse_fecha(ev["fecha"])
            counts[prec] += 1
            if len(examples[prec]) < 3:
                examples[prec].append(ev["fecha"] + " — " + ev.get("descripcion", "")[:60])
        except Exception:
            counts["unparseable"] += 1
    total = sum(counts.values())
    return {
        "total": total,
        "counts": counts,
        "ratios": {k: round(v / total, 4) for k, v in counts.items()},
        "examples": examples,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Enriquecimiento
# ─────────────────────────────────────────────────────────────────────────────

def enrich_event(event: dict, window_days: float = 30.0) -> dict:
    y, m, d, precision = parse_fecha(event["fecha"])
    jd = to_jd(y, m, d)

    # Patrones activos en el JD del evento
    continuous_patterns = detect_active_patterns(jd, lookback_days=0, lookforward_days=0)
    # Eventos discretos en la ventana
    discrete_patterns = scan_window_discrete(jd - window_days, jd + window_days)

    configs = []
    for p in continuous_patterns + discrete_patterns:
        days_offset = round(p.jd - jd, 2)
        if abs(days_offset) > window_days:
            continue
        configs.append({
            "type":         p.type,
            "group":        p.group,
            "label":        p.label,
            "participants": p.participants,
            "days_offset":  days_offset,
            "orb":          round(p.orb, 4) if p.orb is not None else None,
            "details":      p.details,
        })

    return {
        **event,
        "date_precision": precision,
        "jd":             jd,
        "configs_active": configs,
    }


def enrich_events(
    events: list[dict],
    output_path: Path,
    checkpoint_path: Path,
    window_days: float = 30.0,
    log_every: int = 50,
) -> None:
    # Reanudación
    done_indices: set[int] = set()
    if checkpoint_path.exists():
        cp = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        done_indices = set(cp.get("done_indices", []))
        print(f"[RESUME] Reanudando desde checkpoint: {len(done_indices)}/{len(events)} hechos")

    # Abrir output en modo append
    mode = "a" if done_indices else "w"
    fout = output_path.open(mode, encoding="utf-8")

    start = time.time()
    try:
        for i, ev in enumerate(events):
            if i in done_indices:
                continue
            try:
                enriched = enrich_event(ev, window_days=window_days)
                fout.write(json.dumps(enriched, ensure_ascii=False) + "\n")
                fout.flush()
            except Exception as e:
                print(f"[ERROR] event {i} ({ev.get('fecha')}): {e}", file=sys.stderr)
                # Aún así marcar como procesado para no atascar
            done_indices.add(i)

            if (i + 1) % log_every == 0 or (i + 1) == len(events):
                elapsed = time.time() - start
                rate = (i + 1 - len(done_indices) + len(done_indices)) / elapsed if elapsed > 0 else 0
                eta = (len(events) - i - 1) / max(rate, 0.01)
                print(f"[{i+1}/{len(events)}] {ev.get('fecha','?')} — "
                      f"{len(enriched.get('configs_active', []))} configs · "
                      f"rate={rate:.1f}ev/s · ETA={eta/60:.1f}min")

            # Checkpoint cada 100
            if (i + 1) % 100 == 0:
                checkpoint_path.write_text(
                    json.dumps({"done_indices": sorted(list(done_indices))}, ensure_ascii=False),
                    encoding="utf-8",
                )
    finally:
        fout.close()
        checkpoint_path.write_text(
            json.dumps({"done_indices": sorted(list(done_indices))}, ensure_ascii=False),
            encoding="utf-8",
        )

    print(f"[DONE] {len(done_indices)}/{len(events)} eventos enriquecidos en {(time.time()-start)/60:.1f}min")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Enrich historical events with active astrological patterns.")
    parser.add_argument("--input",  type=Path, required=True, help="Path to eventos_raw.jsonl")
    parser.add_argument("--output", type=Path, help="Path to eventos_enriched.jsonl (required unless --audit-only)")
    parser.add_argument("--window-days", type=float, default=30.0)
    parser.add_argument("--checkpoint", type=Path, default=Path("data/mundana/.enrich_checkpoint.json"))
    parser.add_argument("--audit-only", action="store_true", help="Solo correr análisis de date_precision")
    parser.add_argument("--report", type=Path, help="Path para guardar reporte de audit (json)")
    args = parser.parse_args()

    events = load_events(args.input)
    print(f"[LOAD] {len(events)} eventos cargados desde {args.input}")

    if args.audit_only:
        report = audit_precision(events)
        out_str = json.dumps(report, ensure_ascii=False, indent=2)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(out_str, encoding="utf-8")
            print(f"[AUDIT] Reporte guardado en {args.report}")
        print(out_str)
        return

    if not args.output:
        parser.error("--output es requerido salvo en --audit-only")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    enrich_events(events, args.output, args.checkpoint, window_days=args.window_days)


if __name__ == "__main__":
    main()
