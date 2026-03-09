"""Render HF_v3 relocation fields into heatmaps (quicklook + optional normalized).

Usage:
    python scripts/generate_hf_map.py --input output/relocation_fields_v3/subject_123.parquet
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Tuple, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as patheffects

try:  # cartopy es opcional
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    HAS_CARTOPY = True
except Exception:  # pragma: no cover
    HAS_CARTOPY = False

try:  # geopandas opcional (fallback sin cartopy)
    import geopandas as gpd
    HAS_GEODATA = True
except Exception:  # pragma: no cover
    HAS_GEODATA = False

DEFAULT_METRIC = "delta_hf_total_v3"
SUPPORTED_METRICS = {
    "hf_total_v3",
    "hf_total_v3_norm",
    "hf_aspects",
    "hf_angles",
    "hf_houses",
    "delta_hf_total_v3",
    "delta_hf_aspects",
    "delta_hf_angles",
    "delta_hf_houses",
}


def reshape_grid(df: pd.DataFrame, metric: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    lat_idx_max = int(df["grid_lat_index"].max())
    lon_idx_max = int(df["grid_lon_index"].max())
    n_lat = lat_idx_max + 1
    n_lon = lon_idx_max + 1

    grid_vals = np.full((n_lat, n_lon), np.nan)
    grid_lats = np.full((n_lat, n_lon), np.nan)
    grid_lons = np.full((n_lat, n_lon), np.nan)

    for _, row in df.iterrows():
        i = int(row["grid_lat_index"])
        j = int(row["grid_lon_index"])
        grid_vals[i, j] = float(row[metric])
        grid_lats[i, j] = float(row["relocation_latitude"])
        grid_lons[i, j] = float(row["relocation_longitude"])

    return grid_vals, grid_lats, grid_lons


def compute_normalized(df: pd.DataFrame) -> pd.DataFrame:
    if "hf_total_v3_norm" in df.columns:
        return df
    mean = df["hf_total_v3"].mean()
    std = df["hf_total_v3"].std()
    df = df.copy()
    df["hf_total_v3_norm"] = (df["hf_total_v3"] - mean) / std if std and std > 0 else 0.0
    return df


def _process_ranking_points(ranking_points: Optional[list], max_points: int = 5) -> List[Tuple[float, float, str]]:
    """Dedup by city/name, keep top-N, and extract (lat, lon, label)."""
    if not ranking_points:
        return []
    seen = set()
    cleaned: List[Tuple[float, float, str]] = []
    for pt in ranking_points:
        extracted = _extract_point(pt)
        if not extracted:
            continue
        lat, lon, label = extracted
        key = (label or f"{lat:.3f},{lon:.3f}").lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append((lat, lon, label))
        if len(cleaned) >= max_points:
            break
    return cleaned


def _default_scale(metric: str, grid_vals: np.ndarray, vmin: Optional[float], vmax: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    if vmin is not None and vmax is not None:
        return vmin, vmax
    if metric.startswith("delta_"):
        finite_vals = grid_vals[np.isfinite(grid_vals)]
        if finite_vals.size == 0:
            return vmin, vmax
        max_abs = np.nanpercentile(np.abs(finite_vals), 98)
        return -max_abs, max_abs
    # escala fija por defecto para métricas absolutas
    return vmin if vmin is not None else 10.0, vmax if vmax is not None else 35.0


def _extract_point(pt: dict) -> Optional[Tuple[float, float, str]]:
    lat = (
        pt.get("lat")
        or pt.get("latitude")
        or pt.get("relocation_latitude")
        or pt.get("city_lat")
    )
    lon = (
        pt.get("lon")
        or pt.get("lng")
        or pt.get("longitude")
        or pt.get("relocation_longitude")
        or pt.get("city_lon")
    )
    if lat is None or lon is None:
        return None
    city = pt.get("city") or pt.get("name") or ""
    country = pt.get("country")
    label = f"{city}, {country}" if city and country else city
    return float(lat), float(lon), label


def plot_with_cartopy(
    grid_vals: np.ndarray,
    lats: np.ndarray,
    lons: np.ndarray,
    title: str,
    output_path: Path,
    vmin: Optional[float],
    vmax: Optional[float],
    alpha: float,
    ranking_points: Optional[List[Tuple[float, float, str]]] = None,
    natal_point: Optional[Tuple[float, float]] = None,
) -> None:
    extent = [np.nanmin(lons), np.nanmax(lons), np.nanmin(lats), np.nanmax(lats)]
    proj = ccrs.PlateCarree()
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=proj)
    ax.add_feature(cfeature.LAND, facecolor="#f8f4e8", zorder=0)
    ax.add_feature(cfeature.OCEAN, facecolor="#e6f2ff", zorder=0)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, zorder=1)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle="-", edgecolor="#444", zorder=1)
    im = ax.imshow(
        grid_vals,
        origin="lower",
        extent=extent,
        transform=proj,
        aspect="auto",
        vmin=vmin,
        vmax=vmax,
        alpha=alpha,
        cmap="turbo",
    )
    ax.coastlines(linewidth=0.8)
    gl = ax.gridlines(draw_labels=True, linewidth=0.4, linestyle="--", color="#888", alpha=0.7)
    gl.top_labels = False
    gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER

    if ranking_points:
        for idx, (lat, lon, label) in enumerate(ranking_points):
            ax.scatter(lon, lat, color="red", s=28, transform=proj, zorder=3, edgecolors="white", linewidths=0.4)
            if label:
                dy = 0.6 * ((idx % 3) - 1)
                txt = ax.text(
                    lon,
                    lat + dy,
                    f" {label}",
                    color="red",
                    fontsize=7,
                    transform=proj,
                    zorder=3,
                    path_effects=[patheffects.withStroke(linewidth=1, foreground="white")],
                )

    if natal_point:
        n_lat, n_lon = natal_point
        ax.scatter(n_lon, n_lat, color="black", marker="*", s=70, edgecolors="white", linewidths=0.6, zorder=4, transform=proj)
        ax.text(
            n_lon,
            n_lat + 1.0,
            "Natal",
            color="black",
            fontsize=7,
            transform=proj,
            zorder=4,
            path_effects=[patheffects.withStroke(linewidth=1, foreground="white")],
        )

    cbar = plt.colorbar(im, ax=ax, orientation="vertical", pad=0.02)
    cbar.set_label(title)
    ax.set_title(title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_plain(
    grid_vals: np.ndarray,
    lats: np.ndarray,
    lons: np.ndarray,
    title: str,
    output_path: Path,
    vmin: Optional[float],
    vmax: Optional[float],
    alpha: float,
    ranking_points: Optional[List[Tuple[float, float, str]]] = None,
    natal_point: Optional[Tuple[float, float]] = None,
) -> None:
    fig = plt.figure(figsize=(12, 6))
    extent = [np.nanmin(lons), np.nanmax(lons), np.nanmin(lats), np.nanmax(lats)]
    ax = plt.gca()
    if HAS_GEODATA:
        try:
            world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
            world.boundary.plot(ax=ax, color="#555", linewidth=0.6, zorder=0)
        except Exception:
            pass
    im = plt.imshow(
        grid_vals,
        origin="lower",
        extent=extent,
        aspect="auto",
        vmin=vmin,
        vmax=vmax,
        alpha=alpha,
        cmap="turbo",
    )
    if ranking_points:
        for idx, (lat, lon, label) in enumerate(ranking_points):
            plt.scatter(lon, lat, color="red", s=28, edgecolors="white", linewidths=0.4, zorder=3)
            if label:
                dy = 0.6 * ((idx % 3) - 1)
                plt.text(
                    lon,
                    lat + dy,
                    f" {label}",
                    color="red",
                    fontsize=7,
                    zorder=3,
                    path_effects=[patheffects.withStroke(linewidth=1, foreground="white")],
                )
    if natal_point:
        n_lat, n_lon = natal_point
        plt.scatter(n_lon, n_lat, color="black", marker="*", s=70, edgecolors="white", linewidths=0.6, zorder=4)
        plt.text(
            n_lon,
            n_lat + 1.0,
            "Natal",
            color="black",
            fontsize=7,
            zorder=4,
            path_effects=[patheffects.withStroke(linewidth=1, foreground="white")],
        )
    plt.colorbar(im, label=title)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title(title)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HF_v3 heatmap from relocation parquet")
    parser.add_argument("--input", required=True, help="Path to subject parquet (HF_v3)")
    parser.add_argument("--metric", default=DEFAULT_METRIC, help=f"Metric to plot ({', '.join(SUPPORTED_METRICS)})")
    parser.add_argument("--output-dir", default="output/maps", help="Directory to write PNGs")
    parser.add_argument("--vmin", type=float, default=None, help="Fixed vmin (if omitted: delta -> escala simétrica por percentil 98; absoluta -> 10)")
    parser.add_argument("--vmax", type=float, default=None, help="Fixed vmax (if omitted: delta -> escala simétrica por percentil 98; absoluta -> 35)")
    parser.add_argument("--alpha", type=float, default=0.9, help="Alpha for heatmap overlay")
    parser.add_argument("--ranking", type=str, default=None, help="Optional ranking JSON to plot city points (top-5, dedup ciudad)")
    parser.add_argument("--top-k-cities", type=int, default=5, help="Max city labels to draw (dedup by city name)")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise FileNotFoundError(in_path)

    df = pd.read_parquet(in_path)
    df = compute_normalized(df)

    if args.metric not in SUPPORTED_METRICS:
        raise ValueError(f"Unsupported metric {args.metric}. Supported: {SUPPORTED_METRICS}")
    if args.metric not in df.columns:
        raise KeyError(f"Metric {args.metric} not found in parquet columns")

    grid_vals, grid_lats, grid_lons = reshape_grid(df, args.metric)

    # escala por defecto según métrica
    args.vmin, args.vmax = _default_scale(args.metric, grid_vals, args.vmin, args.vmax)

    ranking_points = None
    if args.ranking:
        r_path = Path(args.ranking)
        if r_path.exists():
            with r_path.open("r", encoding="utf-8") as f:
                ranking_points = _process_ranking_points(json.load(f), max_points=args.top_k_cities)

    subject_id = df.iloc[0].get("subject_id", "unknown")
    metric_name = args.metric
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"subject_{subject_id}_{metric_name}.png"

    title = f"HF_v3 {metric_name} (subject {subject_id})"

    natal_point = None
    if "natal_latitude" in df.columns and "natal_longitude" in df.columns:
        natal_point = (float(df.iloc[0]["natal_latitude"]), float(df.iloc[0]["natal_longitude"]))

    if HAS_CARTOPY:
        plot_with_cartopy(
            grid_vals,
            grid_lats,
            grid_lons,
            title,
            out_path,
            vmin=args.vmin,
            vmax=args.vmax,
            alpha=args.alpha,
            ranking_points=ranking_points,
            natal_point=natal_point,
        )
    else:
        plot_plain(
            grid_vals,
            grid_lats,
            grid_lons,
            title,
            out_path,
            vmin=args.vmin,
            vmax=args.vmax,
            alpha=args.alpha,
            ranking_points=ranking_points,
            natal_point=natal_point,
        )
    print(f"Saved map to {out_path}")


if __name__ == "__main__":
    main()
