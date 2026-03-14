"""Tarea 1.3 — Test visual HF por dominio para Frida Kahlo (ID 35255).

Genera una figura matplotlib con 3 mapas en modo Mollweide:
  - HF_global (todos los planetas)
  - HF_h7    (significadores Casa 7 · Relaciones)
  - HF_h10   (significadores Casa 10 · Carrera)

Los tres mapas deben ser visualmente distintos.
Si fueran iguales el filtro planet_subset no estaría funcionando.

Uso:
    .venv/Scripts/python.exe scripts/test_hf_domain_visual.py
    # guarda output/test_hf_domain_frida.png
"""
from __future__ import annotations

import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "abu_engine"))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

from core.chart import chart_json
from core.houses_swiss import calculate_houses, HOUSE_SYSTEM_PLACIDUS
from harmony.field_v3 import compute_hf_v3
from harmony.houses import house_significators

# ── Frida Kahlo birth data (Rodden AA) ────────────────────────────────────────
# 1907-07-06 08:30 local, Coyoacan MX, UTC-6:36:38
_TZ_OFFSET = timedelta(hours=6, minutes=36, seconds=38)
BIRTH_DT_UTC = datetime(1907, 7, 6, 8, 30, 0, tzinfo=timezone.utc) + _TZ_OFFSET
BIRTH_LAT = 19.328888
BIRTH_LON = -99.160278

# ── Grid ──────────────────────────────────────────────────────────────────────
STEP = 5.0
LATS = np.arange(-70, 71, STEP)
LONS = np.arange(-180, 181, STEP)


def _build_angles(natal_chart, houses_data) -> dict:
    """Merge planet longitudes + ASC/MC into a flat angles_deg dict."""
    angles: dict[str, float] = {p.name: p.lon for p in natal_chart.planets}
    angles["ASC"] = float(houses_data["asc"])
    angles["MC"] = float(houses_data["mc"])
    return angles


def compute_grid(
    natal_angles: dict,
    natal_cusps: list,
    planet_subset: list[str] | None,
) -> np.ndarray:
    """Compute HF_total_v3 for every (lat, lon) in the grid."""
    grid = np.zeros((len(LATS), len(LONS)), dtype=float)
    for i, lat in enumerate(LATS):
        for j, lon in enumerate(LONS):
            try:
                h = calculate_houses(BIRTH_DT_UTC, lat, lon, HOUSE_SYSTEM_PLACIDUS)
                angles = dict(natal_angles)
                angles["ASC"] = float(h["asc"])
                angles["MC"] = float(h["mc"])
                cusps = h["cusps"]
                result = compute_hf_v3(
                    angles,
                    cusps=cusps,
                    planet_subset=planet_subset,
                )
                grid[i, j] = result["hf_total_v3"]
            except Exception:
                grid[i, j] = np.nan
    return grid


def main():
    print("Computing natal chart for Frida Kahlo…")
    natal = chart_json(BIRTH_LAT, BIRTH_LON, BIRTH_DT_UTC)
    natal_houses = calculate_houses(BIRTH_DT_UTC, BIRTH_LAT, BIRTH_LON, HOUSE_SYSTEM_PLACIDUS)
    natal_angles = _build_angles(natal, natal_houses)
    natal_cusps = natal_houses["cusps"]

    print(f"  Planets: {list(natal_angles.keys())}")
    print(f"  ASC: {natal_angles['ASC']:.2f}°  MC: {natal_angles['MC']:.2f}°")

    # ── Compute house significators ──────────────────────────────────────────
    # Build a minimal natal_data dict compatible with house_significators
    natal_data_for_sig = {
        "planets": [{"name": p.name, "longitude": p.lon} for p in natal.planets],
        "houses": [{"num": i + 1, "longitude": c} for i, c in enumerate(natal_cusps)],
    }

    sig_h7  = house_significators(natal_data_for_sig, 7)
    sig_h10 = house_significators(natal_data_for_sig, 10)
    print(f"  H7  significators: {sig_h7}")
    print(f"  H10 significators: {sig_h10}")

    # ── Compute grids ─────────────────────────────────────────────────────────
    domains = [
        ("HF Global",   None),
        ("HF Casa 7\n(Relaciones)", sig_h7),
        ("HF Casa 10\n(Carrera)",   sig_h10),
    ]

    grids = []
    for label, subset in domains:
        tag = label.split("\n")[0].replace(" ", "_")
        print(f"Computing {tag} ({len(LATS)*len(LONS)} points)…")
        g = compute_grid(natal_angles, natal_cusps, subset)
        grids.append(g)
        print(f"  range: [{np.nanmin(g):.3f}, {np.nanmax(g):.3f}]")

    # ── Plot ──────────────────────────────────────────────────────────────────
    LON_MESH, LAT_MESH = np.meshgrid(LONS, LATS)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6),
                             subplot_kw={"projection": "mollweide"})
    fig.suptitle("Frida Kahlo — HF por Dominio de Casa (Tarea 1.3)",
                 fontsize=14, fontweight="bold")

    for ax, (label, _), grid in zip(axes, domains, grids):
        lon_rad = np.deg2rad(LON_MESH)
        lat_rad = np.deg2rad(LAT_MESH)

        vmin, vmax = np.nanpercentile(grid, 2), np.nanpercentile(grid, 98)
        vcenter = np.nanmedian(grid)
        vcenter = float(np.clip(vcenter, vmin + 1e-6, vmax - 1e-6))
        norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)

        pcm = ax.pcolormesh(lon_rad, lat_rad, grid,
                            cmap="RdYlGn", norm=norm, shading="auto")
        plt.colorbar(pcm, ax=ax, shrink=0.6, pad=0.05)
        ax.set_title(label, fontsize=11)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.grid(True, linewidth=0.3, alpha=0.5)

    plt.tight_layout()
    out_path = REPO_ROOT / "output" / "test_hf_domain_frida.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    print(f"\nSaved -> {out_path}")

    # ── Sanity check: are the three grids different? ──────────────────────────
    diff_g_h7  = np.nanmean(np.abs(grids[0] - grids[1]))
    diff_g_h10 = np.nanmean(np.abs(grids[0] - grids[2]))
    diff_h7_h10 = np.nanmean(np.abs(grids[1] - grids[2]))
    print(f"\nMean absolute difference:")
    print(f"  Global vs H7 : {diff_g_h7:.4f}")
    print(f"  Global vs H10: {diff_g_h10:.4f}")
    print(f"  H7     vs H10: {diff_h7_h10:.4f}")
    if all(d > 0.01 for d in [diff_g_h7, diff_g_h10, diff_h7_h10]):
        print("\nPASS -- all three maps are visually distinct.")
    else:
        print("\nFAIL -- some maps look identical, check planet_subset filter.")


if __name__ == "__main__":
    main()
