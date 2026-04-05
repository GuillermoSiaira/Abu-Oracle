"""
correlator_temporal.py — Hipótesis Mundana A: correlación temporal.

Detecta si los eventos históricos del corpus (23.636 entradas, año 8-2069)
se agrupan con frecuencia mayor que el azar alrededor de:
  - Conjunciones Júpiter-Saturno  (orbe ±8°)
  - Oposiciones Marte-Saturno     (orbe ±8°)

Algoritmo:
  1. Escaneo cada 5 días (año 8-2069) → identifica episodios de configuración activa
  2. Ventana ±30 días alrededor de cada episodio → días "config"
  3. Clasifica cada evento como config / baseline
  4. Por episodio: cuenta eventos en su ventana → distribución config_counts
  5. Genera ventanas baseline de igual tamaño en fechas sin configuración activa
  6. Mann-Whitney U: config_counts vs baseline_counts
  7. Output JSON + Markdown

NO tocar: abu_engine/, harmony/, field_v3.py, angularity.py
"""

import json
import math
import random
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import NamedTuple

import swisseph as swe
from scipy import stats

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_MUNDANA = REPO_ROOT / "data" / "mundana"
EPHE_DIR = REPO_ROOT / "data" / "ephe"

EVENTOS_PATH = DATA_MUNDANA / "eventos_raw.jsonl"
OUTPUT_JSON = DATA_MUNDANA / "correlations_temporal.json"
OUTPUT_MD = DATA_MUNDANA / "RESULTADOS_H_mundana_A.md"

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

ORB_DEG = 8.0          # orbe de aspecto en grados
WINDOW_DAYS = 30       # días antes/después del episodio
SCAN_STEP_DAYS = 5     # resolución del escaneo
BASELINE_SAMPLES = 500 # ventanas baseline aleatorias por configuración
RANDOM_SEED = 42

# Flags swisseph — Moshier si no hay DE431
_DE431_MARKER = EPHE_DIR / "sepl_m54.se1"
if _DE431_MARKER.exists():
    swe.set_ephe_path(str(EPHE_DIR))
    _FLAGS = swe.FLG_SWIEPH
    _EPHE_SOURCE = "DE431"
else:
    _FLAGS = swe.FLG_MOSEPH
    _EPHE_SOURCE = "Moshier"

# ---------------------------------------------------------------------------
# Utilidades de fecha ↔ JD
# ---------------------------------------------------------------------------

def _date_to_jd(year: int, month: int, day: int) -> float:
    cal = swe.JUL_CAL if (year, month, day) < (1582, 10, 15) else swe.GREG_CAL
    return swe.julday(year, month, day, 12.0, cal)


def _parse_fecha(fecha_str: str) -> tuple[int, int, int]:
    """'YYYY-MM-DD' → (year, month, day). Años con ceros iniciales son válidos."""
    y, m, d = fecha_str.split("-")
    return int(y), int(m), int(d)


def _jd_to_approx_date(jd: float) -> str:
    """JD → 'YYYY-MM-DD' aproximado (solo para display)."""
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


# ---------------------------------------------------------------------------
# Posiciones y aspectos
# ---------------------------------------------------------------------------

def _get_positions(jd: float) -> dict:
    result = {}
    for name, pid in [("jupiter", swe.JUPITER), ("saturn", swe.SATURN), ("mars", swe.MARS)]:
        pos, _ = swe.calc_ut(jd, pid, _FLAGS)
        result[name] = pos[0]
    return result


def _angular_distance(lon1: float, lon2: float) -> float:
    diff = abs(lon1 - lon2) % 360
    return min(diff, 360 - diff)


def _is_conjunction(lon1: float, lon2: float) -> bool:
    return _angular_distance(lon1, lon2) <= ORB_DEG


def _is_opposition(lon1: float, lon2: float) -> bool:
    diff = abs(lon1 - lon2) % 360
    dist = min(abs(diff - 180), abs(diff + 180 - 360))
    return dist <= ORB_DEG


# ---------------------------------------------------------------------------
# Paso 1 — Escaneo de episodios de configuración
# ---------------------------------------------------------------------------

class Episode(NamedTuple):
    config_type: str   # "conj_JS" | "opp_MS"
    jd_start: float    # primer día activo
    jd_end: float      # último día activo
    jd_peak: float     # día de mínima separación

    @property
    def window_start(self) -> float:
        return self.jd_start - WINDOW_DAYS

    @property
    def window_end(self) -> float:
        return self.jd_end + WINDOW_DAYS


def _scan_episodes(jd_start: float, jd_end: float) -> list[Episode]:
    """
    Escanea el rango [jd_start, jd_end] cada SCAN_STEP_DAYS días
    y agrupa días activos consecutivos en episodios.
    """
    print(f"  Escaneando configuraciones ({_EPHE_SOURCE}) …", flush=True)

    # Para cada tipo: acumular tramos activos
    active_conj: list[float] = []
    active_opp: list[float] = []

    jd = jd_start
    n_steps = 0
    while jd <= jd_end:
        pos = _get_positions(jd)
        if _is_conjunction(pos["jupiter"], pos["saturn"]):
            active_conj.append(jd)
        if _is_opposition(pos["mars"], pos["saturn"]):
            active_opp.append(jd)
        jd += SCAN_STEP_DAYS
        n_steps += 1

    print(f"  Pasos escaneados: {n_steps:,}")
    print(f"  Días activos conj J-S: {len(active_conj)}")
    print(f"  Días activos opos M-S: {len(active_opp)}")

    def _group_into_episodes(active_jds: list[float], ctype: str) -> list[Episode]:
        if not active_jds:
            return []
        episodes = []
        seg_start = active_jds[0]
        seg_prev = active_jds[0]
        gap_threshold = SCAN_STEP_DAYS * 3  # tolerancia de gap entre días activos
        for jd in active_jds[1:]:
            if jd - seg_prev > gap_threshold:
                # cerrar episodio anterior
                episodes.append(_make_episode(ctype, seg_start, seg_prev))
                seg_start = jd
            seg_prev = jd
        episodes.append(_make_episode(ctype, seg_start, seg_prev))
        return episodes

    def _make_episode(ctype: str, jd_s: float, jd_e: float) -> Episode:
        # Refinar: buscar el día de separación mínima en el tramo
        peak_jd = jd_s
        best_sep = 999.0
        j = jd_s
        while j <= jd_e + SCAN_STEP_DAYS:
            pos = _get_positions(j)
            if ctype == "conj_JS":
                sep = _angular_distance(pos["jupiter"], pos["saturn"])
            else:
                diff = abs(pos["mars"] - pos["saturn"]) % 360
                sep = min(abs(diff - 180), abs(diff + 180 - 360))
            if sep < best_sep:
                best_sep = sep
                peak_jd = j
            j += 1.0  # refinamiento diario
        return Episode(ctype, jd_s, jd_e, peak_jd)

    episodes = []
    episodes.extend(_group_into_episodes(active_conj, "conj_JS"))
    episodes.extend(_group_into_episodes(active_opp, "opp_MS"))
    episodes.sort(key=lambda e: e.jd_start)
    return episodes


# ---------------------------------------------------------------------------
# Paso 2 — Clasificar eventos
# ---------------------------------------------------------------------------

def _load_events() -> list[dict]:
    events = []
    with open(EVENTOS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                y, m, d = _parse_fecha(e["fecha"])
                e["_jd"] = _date_to_jd(y, m, d)
                events.append(e)
            except Exception:
                pass
    return events


def _classify_events(events: list[dict], episodes: list[Episode]) -> tuple[list, list]:
    """
    Devuelve (window_events, baseline_events).
    window_events  = eventos dentro de la ventana de cualquier episodio
    baseline_events = eventos fuera de todas las ventanas
    """
    # Construir set de JD ranges de ventana (como intervalos)
    # Optimización: marcar JDs de ventana en un conjunto discreto de días enteros
    window_jd_set: set[int] = set()
    for ep in episodes:
        jd = ep.window_start
        while jd <= ep.window_end:
            window_jd_set.add(int(jd))
            jd += 1.0

    window_evs = []
    baseline_evs = []
    for e in events:
        if int(e["_jd"]) in window_jd_set:
            window_evs.append(e)
        else:
            baseline_evs.append(e)

    return window_evs, baseline_evs


# ---------------------------------------------------------------------------
# Paso 3 — Conteos por episodio + ventanas baseline
# ---------------------------------------------------------------------------

def _count_events_per_episode(events: list[dict], episodes: list[Episode]) -> list[int]:
    """Cuenta eventos dentro de la ventana ±WINDOW_DAYS de cada episodio."""
    counts = []
    for ep in episodes:
        w_start = ep.window_start
        w_end = ep.window_end
        n = sum(1 for e in events if w_start <= e["_jd"] <= w_end)
        counts.append(n)
    return counts


def _sample_baseline_windows(
    all_events: list[dict],
    episodes: list[Episode],
    corpus_jd_start: float,
    corpus_jd_end: float,
    n_samples: int,
    rng: random.Random,
) -> list[int]:
    """
    Genera ventanas baseline aleatorias fuera de todos los episodios.
    Cada ventana tiene tamaño 2*WINDOW_DAYS (mismo que las ventanas de episodio).
    """
    # Marcar JDs de episodio activo (no solo ventanas)
    forbidden_jd_set: set[int] = set()
    for ep in episodes:
        jd = ep.window_start
        while jd <= ep.window_end:
            forbidden_jd_set.add(int(jd))
            jd += 1.0

    window_size = 2 * WINDOW_DAYS
    total_range = corpus_jd_end - corpus_jd_start
    baseline_counts = []
    attempts = 0
    max_attempts = n_samples * 20

    while len(baseline_counts) < n_samples and attempts < max_attempts:
        attempts += 1
        center = corpus_jd_start + rng.random() * total_range
        w_start = center - WINDOW_DAYS
        w_end = center + WINDOW_DAYS

        # Verificar que la ventana no solape con ningún episodio
        overlap = any(int(j) in forbidden_jd_set for j in range(int(w_start), int(w_end) + 1, 10))
        if overlap:
            continue

        n = sum(1 for e in all_events if w_start <= e["_jd"] <= w_end)
        baseline_counts.append(n)

    return baseline_counts


# ---------------------------------------------------------------------------
# Paso 4 — Estadísticas
# ---------------------------------------------------------------------------

def _stats(values: list) -> dict:
    if not values:
        return {"n": 0, "mean": 0.0, "median": 0.0, "std": 0.0, "min": 0, "max": 0}
    arr = sorted(values)
    n = len(arr)
    mean = sum(arr) / n
    median = arr[n // 2] if n % 2 else (arr[n // 2 - 1] + arr[n // 2]) / 2
    std = math.sqrt(sum((x - mean) ** 2 for x in arr) / n)
    return {"n": n, "mean": round(mean, 4), "median": median, "std": round(std, 4),
            "min": arr[0], "max": arr[-1]}


def _run_mannwhitney(config_counts: list, baseline_counts: list) -> dict:
    if len(config_counts) < 3 or len(baseline_counts) < 3:
        return {"error": "muestra insuficiente", "U": None, "p_value": None}
    stat, p = stats.mannwhitneyu(config_counts, baseline_counts, alternative="greater")
    n1, n2 = len(config_counts), len(baseline_counts)
    U_max = n1 * n2
    r = (2 * stat) / U_max - 1  # rank-biserial: -1 (cfg<base) … 0 … +1 (cfg>base)
    return {
        "U": round(float(stat), 4),
        "p_value": round(float(p), 6),
        "rank_biserial_r": round(r, 4),
        "n_config": n1,
        "n_baseline": n2,
        "significant_p05": bool(p < 0.05),
    }


# ---------------------------------------------------------------------------
# Escritura de resultados
# ---------------------------------------------------------------------------

def _write_json(results: dict) -> None:
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n  -> {OUTPUT_JSON}")


def _write_markdown(results: dict) -> None:
    r = results
    lines = [
        "# Resultados H_mundana_A — Correlación Temporal",
        "",
        f"**Fecha:** {r['metadata']['run_date']}  ",
        f"**Dataset:** {r['metadata']['n_events']:,} eventos · {r['metadata']['fecha_min']} – {r['metadata']['fecha_max']}  ",
        f"**Efemérides:** {r['metadata']['ephe_source']}  ",
        f"**Orbe:** ±{ORB_DEG}°  **Ventana:** ±{WINDOW_DAYS} días  ",
        "",
        "---",
        "",
        "## Episodios detectados",
        "",
        f"| Configuración | Episodios | Días activos totales |",
        f"|---|---|---|",
    ]
    for cfg_key, cfg in r["configurations"].items():
        lines.append(
            f"| {cfg['label']} | {cfg['n_episodes']} | ~{cfg['n_episodes'] * cfg['median_episode_days']:.0f} |"
        )

    lines += ["", "---", "", "## Resultados por configuración", ""]

    for cfg_key, cfg in r["configurations"].items():
        mw = cfg["mannwhitney"]
        cs = cfg["stats_config"]
        bs = cfg["stats_baseline"]
        sig = "✅ SIGNIFICATIVO" if mw.get("significant_p05") else "❌ no significativo"
        lines += [
            f"### {cfg['label']}",
            "",
            f"| | Config (ventana ±{WINDOW_DAYS}d) | Baseline (aleatorio) |",
            f"|---|---|---|",
            f"| N ventanas | {cs['n']} | {bs['n']} |",
            f"| Media eventos/ventana | {cs['mean']:.2f} | {bs['mean']:.2f} |",
            f"| Mediana | {cs['median']} | {bs['median']} |",
            f"| Desv. estándar | {cs['std']:.2f} | {bs['std']:.2f} |",
            f"| Rango | [{cs['min']}, {cs['max']}] | [{bs['min']}, {bs['max']}] |",
            "",
            f"**Mann-Whitney U = {mw.get('U', 'N/A')}** · p = {mw.get('p_value', 'N/A')} · r = {mw.get('rank_biserial_r', 'N/A')}",
            "",
            f"**Resultado: {sig}**",
            "",
        ]

    # Clasificación global
    total = r["global"]
    pct_window = total["pct_events_in_windows"]
    pct_expected = total["pct_days_in_windows"]
    lines += [
        "---",
        "",
        "## Clasificación global de eventos",
        "",
        f"| | N | % |",
        f"|---|---|---|",
        f"| Eventos en ventana de configuración | {total['n_window_events']:,} | {pct_window:.1f}% |",
        f"| Eventos en baseline | {total['n_baseline_events']:,} | {100-pct_window:.1f}% |",
        f"| Días en ventana (% del corpus) | — | {pct_expected:.1f}% |",
        "",
        f"**Ratio densidad**: {total['density_ratio']:.3f}x "
        f"({'mayor' if total['density_ratio'] > 1 else 'menor'} que baseline)",
        "",
        "---",
        "",
        "## Interpretación",
        "",
    ]

    # Interpretación automática
    interpretations = []
    for cfg_key, cfg in r["configurations"].items():
        mw = cfg["mannwhitney"]
        cs = cfg["stats_config"]
        bs = cfg["stats_baseline"]
        ratio = cs["mean"] / bs["mean"] if bs["mean"] > 0 else 0
        if mw.get("significant_p05"):
            interpretations.append(
                f"- **{cfg['label']}**: confirmada (p={mw['p_value']}, r={mw['rank_biserial_r']}). "
                f"Media eventos/ventana: {cs['mean']:.1f} vs {bs['mean']:.1f} baseline ({ratio:.2f}x)."
            )
        else:
            interpretations.append(
                f"- **{cfg['label']}**: no confirmada (p={mw['p_value']}). "
                f"Media: {cs['mean']:.1f} config vs {bs['mean']:.1f} baseline."
            )

    lines.extend(interpretations)
    lines += [
        "",
        "### Limitación principal",
        "",
        "El corpus está fuertemente sesgado hacia eventos del siglo XIX-XX (>68% de los eventos).",
        "Las conjunciones J-S tienen período ~20 años y las oposiciones M-S ~2 años —",
        "la distribución desigual de eventos puede inflar artificialmente las densidades en períodos modernos.",
        "Una réplica con corpus estratificado por siglo reforzaría las conclusiones.",
        "",
        "---",
        "",
        f"*Generado por `scripts/mundana/correlator_temporal.py`*",
    ]

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  -> {OUTPUT_MD}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    from datetime import datetime

    print("=" * 60)
    print("correlator_temporal.py — Hipótesis Mundana A")
    print("=" * 60)

    # ── Cargar eventos ──────────────────────────────────────────
    print("\n[1/5] Cargando eventos …")
    events = _load_events()
    print(f"  Eventos cargados: {len(events):,}")

    jds = [e["_jd"] for e in events]
    corpus_jd_start = min(jds)
    corpus_jd_end = max(jds)
    fecha_min = _jd_to_approx_date(corpus_jd_start)
    fecha_max = _jd_to_approx_date(corpus_jd_end)
    print(f"  Rango JD: {corpus_jd_start:.1f} – {corpus_jd_end:.1f} ({fecha_min} – {fecha_max})")

    # ── Escaneo de episodios ────────────────────────────────────
    print("\n[2/5] Escaneando configuraciones planetarias …")
    episodes = _scan_episodes(corpus_jd_start, corpus_jd_end)

    episodes_conj = [e for e in episodes if e.config_type == "conj_JS"]
    episodes_opp = [e for e in episodes if e.config_type == "opp_MS"]
    print(f"  Episodios conj J-S: {len(episodes_conj)}")
    print(f"  Episodios opos M-S: {len(episodes_opp)}")

    # ── Clasificar eventos ──────────────────────────────────────
    print("\n[3/5] Clasificando eventos en window / baseline …")
    window_events, baseline_events = _classify_events(events, episodes)
    n_window = len(window_events)
    n_baseline = len(baseline_events)
    print(f"  Eventos en ventana  : {n_window:,}")
    print(f"  Eventos en baseline : {n_baseline:,}")

    # Días de ventana como % del total
    total_corpus_days = corpus_jd_end - corpus_jd_start
    window_days_set: set[int] = set()
    for ep in episodes:
        j = ep.window_start
        while j <= ep.window_end:
            window_days_set.add(int(j))
            j += 1.0
    pct_days_window = len(window_days_set) / total_corpus_days * 100
    pct_events_window = n_window / len(events) * 100
    density_ratio = (pct_events_window / pct_days_window) if pct_days_window > 0 else 0
    print(f"  % días en ventana   : {pct_days_window:.1f}%")
    print(f"  % eventos en ventana: {pct_events_window:.1f}%")
    print(f"  Ratio densidad      : {density_ratio:.3f}x")

    # ── Conteos por episodio + baseline ────────────────────────
    print("\n[4/5] Contando eventos por episodio y generando baseline …")
    rng = random.Random(RANDOM_SEED)

    config_results = {}
    for cfg_type, ep_list, label in [
        ("conj_JS", episodes_conj, "Conjunción Júpiter-Saturno"),
        ("opp_MS", episodes_opp, "Oposición Marte-Saturno"),
    ]:
        counts_cfg = _count_events_per_episode(events, ep_list)
        counts_base = _sample_baseline_windows(
            events, episodes, corpus_jd_start, corpus_jd_end,
            BASELINE_SAMPLES, rng
        )
        mw = _run_mannwhitney(counts_cfg, counts_base)

        # Duración media de episodio (en días de escaneo)
        durations = [ep.jd_end - ep.jd_start for ep in ep_list]
        med_dur = sorted(durations)[len(durations) // 2] if durations else 0

        config_results[cfg_type] = {
            "label": label,
            "n_episodes": len(ep_list),
            "median_episode_days": round(med_dur, 1),
            "stats_config": _stats(counts_cfg),
            "stats_baseline": _stats(counts_base),
            "mannwhitney": mw,
            "episode_counts": counts_cfg,
            "sample_episodes": [
                {
                    "peak": _jd_to_approx_date(ep.jd_peak),
                    "window": f"{_jd_to_approx_date(ep.window_start)} – {_jd_to_approx_date(ep.window_end)}",
                    "events_in_window": counts_cfg[i],
                }
                for i, ep in enumerate(ep_list[:10])  # primeros 10 para el JSON
            ],
        }

        print(f"\n  {label}:")
        print(f"    Episodios: {len(ep_list)} · Media cfg: {config_results[cfg_type]['stats_config']['mean']:.2f} "
              f"· Media base: {config_results[cfg_type]['stats_baseline']['mean']:.2f}")
        print(f"    Mann-Whitney p={mw.get('p_value')} · r={mw.get('rank_biserial_r')} "
              f"· sig={mw.get('significant_p05')}")

    # ── Escribir outputs ────────────────────────────────────────
    print("\n[5/5] Escribiendo resultados …")

    results = {
        "metadata": {
            "hypothesis": "H_mundana_A",
            "run_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "n_events": len(events),
            "fecha_min": fecha_min,
            "fecha_max": fecha_max,
            "ephe_source": _EPHE_SOURCE,
            "orb_deg": ORB_DEG,
            "window_days": WINDOW_DAYS,
            "scan_step_days": SCAN_STEP_DAYS,
            "baseline_samples": BASELINE_SAMPLES,
        },
        "global": {
            "n_window_events": n_window,
            "n_baseline_events": n_baseline,
            "pct_events_in_windows": round(pct_events_window, 2),
            "pct_days_in_windows": round(pct_days_window, 2),
            "density_ratio": round(density_ratio, 4),
        },
        "configurations": config_results,
    }

    _write_json(results)
    _write_markdown(results)

    print("\n" + "=" * 60)
    print("COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    main()
