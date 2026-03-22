"""
Test visual HF por dominio — 10 sujetos × 3 dominios (global, H7, H10)

Genera una grilla 10×3 de mapas HF de relocalización.
Cada fila = un sujeto. Columnas: global, Casa 7 (Relaciones), Casa 10 (Carrera).

Uso:
    .venv/Scripts/python.exe scripts/test_hf_domain_visual.py
    # guarda output/maps/hf_domain_test_10subjects.png
"""
from __future__ import annotations

import json
import sys
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Path setup ────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "abu_engine"))

from core.chart import _compute_planet_positions
from core.houses_swiss import calculate_houses, HOUSE_SYSTEM_PLACIDUS
from harmony.field_v3 import compute_hf_v3
from harmony.houses import house_significators

# ── Paths ─────────────────────────────────────────────────────────────────────
BIRTHDATA_PATH = REPO_ROOT / "data" / "raw" / "raw_birthdata.jsonl"
OUTPUT_PATH = REPO_ROOT / "output" / "maps"

# ── Subjects — slug → ID ──────────────────────────────────────────────────────
SUBJECTS: Dict[str, int] = {
    'einstein': 308660,
    'freud':    337730,
    'jung':     366580,
    'tesla':    357700,
    'gandhi':   61360,
    'frida':    35255,
    'picasso':  76835,
    'vangogh':  317785,
    'borges':   12145,
    'mlk':      238010,
}

# ── Grid settings (5°×5° for speed) ──────────────────────────────────────────
LAT_RANGE = np.arange(-70, 71, 5, dtype=float)
LON_RANGE = np.arange(-180, 176, 5, dtype=float)


# ── Datetime parsing ──────────────────────────────────────────────────────────

def _parse_tz_offset(tz_str: str) -> timedelta:
    """Parse a timezone offset string like '+00:39:58' or '-4:16:48' into a timedelta."""
    tz_str = tz_str.strip()
    m = re.match(r'^([+-])(\d+):(\d+)(?::(\d+))?$', tz_str)
    if not m:
        return timedelta(0)
    sign = 1 if m.group(1) == '+' else -1
    hours = int(m.group(2))
    minutes = int(m.group(3))
    seconds = int(m.group(4)) if m.group(4) else 0
    return timedelta(seconds=sign * (hours * 3600 + minutes * 60 + seconds))


def _record_to_utc(record: dict) -> Optional[datetime]:
    """Convert a JSONL birth record to UTC datetime.

    The JSONL timezone field is the LMT/TZ offset of the local birth time.
    UTC = local_time - offset.
    """
    try:
        date_str = record.get('birth_date', '')
        time_str = record.get('birth_time', '00:00:00')
        tz_str = record.get('timezone', '+00:00')

        local_dt = datetime.fromisoformat(f"{date_str}T{time_str}")
        tz_offset = _parse_tz_offset(tz_str)
        # local = UTC + offset  =>  UTC = local - offset
        utc_dt = (local_dt - tz_offset).replace(tzinfo=timezone.utc)
        return utc_dt
    except Exception as e:
        print(f"  ERROR parsing datetime for record {record.get('id')}: {e}")
        return None


# ── JSONL loading ─────────────────────────────────────────────────────────────

def load_natal_records(jsonl_path: Path) -> Dict[int, dict]:
    """Load all records from JSONL, keyed by integer ID."""
    data: Dict[int, dict] = {}
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                rid = record.get('id')
                if rid is not None:
                    data[int(rid)] = record
            except json.JSONDecodeError:
                continue
    return data


# ── Natal data builder for house_significators ────────────────────────────────

def build_natal_data_for_sig(natal_angles: dict, natal_cusps: List[float]) -> dict:
    """Build minimal dict accepted by house_significators()."""
    return {
        "planets": [
            {"name": k, "longitude": v}
            for k, v in natal_angles.items()
            if k not in ("ASC", "MC")
        ],
        "houses": [
            {"num": i + 1, "longitude": c}
            for i, c in enumerate(natal_cusps)
        ],
    }


# ── HF field computation ──────────────────────────────────────────────────────

def compute_field_grid(
    birth_dt: datetime,
    natal_planet_pos: dict,
    planet_subset: Optional[List[str]] = None,
) -> np.ndarray:
    """Compute HF field on the LAT_RANGE×LON_RANGE grid."""
    grid = np.full((len(LAT_RANGE), len(LON_RANGE)), np.nan)
    for i, lat in enumerate(LAT_RANGE):
        for j, lon in enumerate(LON_RANGE):
            try:
                h = calculate_houses(birth_dt, float(lat), float(lon), HOUSE_SYSTEM_PLACIDUS)
                angles = dict(natal_planet_pos)
                angles["ASC"] = float(h["asc"])
                angles["MC"] = float(h["mc"])
                cusps = list(h["cusps"])
                hf = compute_hf_v3(angles, cusps=cusps, planet_subset=planet_subset)
                grid[i, j] = float(hf["hf_total_v3"])
            except Exception:
                pass  # leave as NaN
    return grid


# ── Distinctness metric ───────────────────────────────────────────────────────

def are_distinct(g1: np.ndarray, g2: np.ndarray) -> Tuple[bool, float]:
    """Return (distinct, correlation). Distinct if |corr| < 0.99."""
    f1 = g1.flatten()
    f2 = g2.flatten()
    mask = ~(np.isnan(f1) | np.isnan(f2))
    f1, f2 = f1[mask], f2[mask]
    if len(f1) < 2:
        return False, float('nan')
    corr = float(np.corrcoef(f1, f2)[0, 1])
    return abs(corr) < 0.99, corr


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    print("Loading natal records from JSONL...")
    all_records = load_natal_records(BIRTHDATA_PATH)
    print(f"  Loaded {len(all_records)} records\n")

    # Resolve subjects
    found: Dict[str, dict] = {}
    for slug, sid in SUBJECTS.items():
        if sid in all_records:
            found[slug] = all_records[sid]
            print(f"  found: {slug} (ID {sid})")
        else:
            print(f"  NOT FOUND: {slug} (ID {sid})")
    print(f"\nFound {len(found)}/{len(SUBJECTS)} subjects\n")

    n_subjects = len(found)
    col_titles = ['Global (all planets)', 'Casa 7 · Relaciones', 'Casa 10 · Carrera']

    fig, axes = plt.subplots(n_subjects, 3, figsize=(18, 4 * n_subjects))
    fig.suptitle(
        'HF Relocation Field — Global vs H7 (Relaciones) vs H10 (Carrera)',
        fontsize=14, fontweight='bold', y=1.005
    )

    report_lines: List[str] = []

    for row_idx, (slug, record) in enumerate(found.items()):
        print(f"Processing {slug} (ID {record['id']})...")

        birth_dt = _record_to_utc(record)
        if birth_dt is None:
            print(f"  SKIP {slug}: cannot parse birth datetime")
            continue

        natal_lat = float(record['latitude'])
        natal_lon = float(record['longitude'])

        try:
            natal_planet_pos = _compute_planet_positions(birth_dt)
        except Exception as e:
            print(f"  ERROR computing planet positions for {slug}: {e}")
            continue

        try:
            natal_houses = calculate_houses(birth_dt, natal_lat, natal_lon, HOUSE_SYSTEM_PLACIDUS)
            natal_angles = dict(natal_planet_pos)
            natal_angles["ASC"] = float(natal_houses["asc"])
            natal_angles["MC"] = float(natal_houses["mc"])
            natal_cusps = list(natal_houses["cusps"])
        except Exception as e:
            print(f"  ERROR computing natal houses for {slug}: {e}")
            continue

        natal_data_for_sig = build_natal_data_for_sig(natal_angles, natal_cusps)

        try:
            planets_h7 = house_significators(natal_data_for_sig, house=7)
        except Exception as e:
            planets_h7 = []
            print(f"  WARNING: house_significators H7 failed: {e}")

        try:
            planets_h10 = house_significators(natal_data_for_sig, house=10)
        except Exception as e:
            planets_h10 = []
            print(f"  WARNING: house_significators H10 failed: {e}")

        print(f"  H7  planets: {planets_h7}")
        print(f"  H10 planets: {planets_h10}")

        print("  Computing global field...")
        try:
            grid_global = compute_field_grid(birth_dt, natal_planet_pos, planet_subset=None)
        except Exception as e:
            print(f"  ERROR global field: {e}")
            grid_global = np.zeros((len(LAT_RANGE), len(LON_RANGE)))

        print("  Computing H7 field...")
        if planets_h7:
            try:
                grid_h7 = compute_field_grid(birth_dt, natal_planet_pos, planet_subset=planets_h7)
            except Exception as e:
                print(f"  ERROR H7 field: {e}")
                grid_h7 = np.zeros_like(grid_global)
        else:
            print("  SKIP H7 (empty planet list)")
            grid_h7 = np.zeros_like(grid_global)

        print("  Computing H10 field...")
        if planets_h10:
            try:
                grid_h10 = compute_field_grid(birth_dt, natal_planet_pos, planet_subset=planets_h10)
            except Exception as e:
                print(f"  ERROR H10 field: {e}")
                grid_h10 = np.zeros_like(grid_global)
        else:
            print("  SKIP H10 (empty planet list)")
            grid_h10 = np.zeros_like(grid_global)

        distinct_h7, corr_h7   = are_distinct(grid_global, grid_h7)  if planets_h7  else (False, float('nan'))
        distinct_h10, corr_h10 = are_distinct(grid_global, grid_h10) if planets_h10 else (False, float('nan'))
        maps_distinct = distinct_h7 or distinct_h10

        grids = [grid_global, grid_h7, grid_h10]
        subtitles = [
            'all planets',
            ', '.join(planets_h7)  if planets_h7  else '(empty)',
            ', '.join(planets_h10) if planets_h10 else '(empty)',
        ]

        for col_idx, (grid, subtitle) in enumerate(zip(grids, subtitles)):
            valid = grid[~np.isnan(grid)]
            if len(valid) > 0:
                vmin = float(np.percentile(valid, 5))
                vmax = float(np.percentile(valid, 95))
            else:
                vmin, vmax = 0.0, 1.0
            ax = axes[row_idx, col_idx] if n_subjects > 1 else axes[col_idx]
            ax.imshow(
                grid, origin='lower', aspect='auto',
                cmap='RdYlGn', vmin=vmin, vmax=vmax,
                extent=[-180, 175, -70, 70]
            )
            if row_idx == 0:
                ax.set_title(col_titles[col_idx], fontsize=11, fontweight='bold')
            if col_idx == 0:
                ax.set_ylabel(slug, fontsize=11, fontweight='bold', rotation=0,
                              labelpad=45, va='center')
            ax.set_xlabel(subtitle, fontsize=7)
            ax.set_xticks([])
            ax.set_yticks([])

        status = 'SI' if maps_distinct else 'NO'
        h7_str  = ', '.join(planets_h7)  if planets_h7  else '(vacio)'
        h10_str = ', '.join(planets_h10) if planets_h10 else '(vacio)'
        corr_h7_str  = f"{corr_h7:.3f}"  if not (isinstance(corr_h7,  float) and corr_h7  != corr_h7)  else 'N/A'
        corr_h10_str = f"{corr_h10:.3f}" if not (isinstance(corr_h10, float) and corr_h10 != corr_h10) else 'N/A'
        report_lines.append(
            f"{slug:<12} | H7: [{h7_str:<30}] corr={corr_h7_str} "
            f"| H10: [{h10_str:<30}] corr={corr_h10_str} "
            f"| distintos: {status}"
        )
        print(f"  mapas distintos: {status}  (corr_H7={corr_h7_str}, corr_H10={corr_h10_str})")

    plt.tight_layout()
    out_file = OUTPUT_PATH / 'hf_domain_test_10subjects.png'
    plt.savefig(str(out_file), dpi=120, bbox_inches='tight')
    plt.close()
    print(f"\nSaved: {out_file}")

    print("\n" + "=" * 100)
    print("DIAGNOSTICO POR SUJETO:")
    print("=" * 100)
    for line in report_lines:
        print(line)

    distinct_count = sum(1 for ln in report_lines if '| distintos: SI' in ln)
    print(f"\n{distinct_count}/{len(report_lines)} sujetos con mapas visualmente distintos entre global, H7 y H10")
    print(f"PNG guardado en: {out_file}")


if __name__ == '__main__':
    main()
