"""
image_generator.py — Genera imágenes para posts del pipeline Mundana.

Dos funciones principales:
  generate_sky_diagram(config)          → PNG 300×300 del diagrama planetario mundano
  generate_hf_map_image(slug, domain)  → PNG 800×400 del Harmony Field de un sujeto

matplotlib.use('Agg') al inicio — necesario en entornos headless (Docker, Cloud Run).
"""

from __future__ import annotations

import io
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless — debe ir antes de cualquier import pyplot

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
GEOJSON_DIR = REPO_ROOT / "next_app" / "public" / "geojson"

# Colores por planeta
PLANET_COLORS: dict[str, str] = {
    "Sun":     "#fbbf24",
    "Moon":    "#e2e8f0",
    "Mercury": "#94a3b8",
    "Venus":   "#f9a8d4",
    "Mars":    "#ef4444",
    "Jupiter": "#fb923c",
    "Saturn":  "#a78bfa",
    "Uranus":  "#67e8f9",
    "Neptune": "#818cf8",
    "Pluto":   "#6b7280",
}

# Símbolos Unicode por planeta
PLANET_SYMBOLS: dict[str, str] = {
    "Sun":     "☉",
    "Moon":    "☽",
    "Mercury": "☿",
    "Venus":   "♀",
    "Mars":    "♂",
    "Jupiter": "♃",
    "Saturn":  "♄",
    "Uranus":  "⛢",
    "Neptune": "♆",
    "Pluto":   "♇",
}

# Símbolos de los 12 signos zodiacales (Aries…Piscis)
ZODIAC_SYMBOLS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]

# Color de línea de aspecto por tipo de configuración
ASPECT_LINE_COLORS: dict[str, tuple[str, float]] = {
    "conjunction": ("#ffffff", 0.8),
    "opposition":  ("#ef4444", 0.6),
    "square":      ("#f97316", 0.6),
    "trine":       ("#4ade80", 0.6),
}

BG_COLOR    = "#0a0a0f"
SECTOR_EDGE = "#2a2a3a"
LABEL_GRAY  = "#4a4a6a"
TEXT_LIGHT  = "#cbd5e1"
WATERMARK   = "#2a2a3a"


# ---------------------------------------------------------------------------
# Función auxiliar: lon eclíptica → theta polar matplotlib
# ---------------------------------------------------------------------------

def _lon_to_theta(lon_deg: float) -> float:
    """
    Convierte longitud eclíptica (0°=Aries, sentido antihorario) a theta
    para proyección polar de matplotlib donde 0=derecha, sentido antihorario.
    Aries (0°) queda arriba (π/2).
    """
    return math.radians((90.0 - lon_deg) % 360)


# ---------------------------------------------------------------------------
# Función 1: generate_sky_diagram
# ---------------------------------------------------------------------------

def generate_sky_diagram(config: dict) -> bytes:
    """
    Genera un diagrama circular de la configuración planetaria mundana.

    Args:
        config: dict con campos:
            planet_a, planet_b          — nombres de los planetas (ej: "Jupiter")
            config_type                 — tipo (ej: "conjunction_JS")
            exact_date                  — fecha ISO (ej: "2026-05-15")
            current_longitude_a         — longitud eclíptica de planet_a (0–360)
            current_longitude_b         — longitud eclíptica de planet_b (0–360)

    Returns:
        PNG en bytes (300×300px, DPI 150)
    """
    planet_a   = config.get("planet_a", "Jupiter")
    planet_b   = config.get("planet_b", "Saturn")
    config_type = config.get("config_type", "")
    exact_date  = config.get("exact_date", "")
    lon_a       = float(config.get("current_longitude_a", 0.0))
    lon_b       = float(config.get("current_longitude_b", 0.0))

    # Determinar color de línea de aspecto
    aspect_key = config_type.split("_")[0].lower()  # "conjunction", "opposition", etc.
    line_color, line_alpha = ASPECT_LINE_COLORS.get(
        aspect_key, ("#ffffff", 0.5)
    )

    fig = plt.figure(figsize=(3, 3), dpi=150, facecolor=BG_COLOR)
    ax  = fig.add_subplot(111, projection="polar", facecolor=BG_COLOR)

    # ── Sectores zodiacales ──────────────────────────────────────────────
    for i in range(12):
        start = math.radians((90 - i * 30) % 360)
        end   = math.radians((90 - (i + 1) * 30) % 360)
        # Borde del sector
        ax.plot([start, start], [0, 1], color=SECTOR_EDGE, lw=0.6, zorder=1)

    # Círculo exterior
    theta_ring = np.linspace(0, 2 * math.pi, 360)
    ax.plot(theta_ring, np.ones(360), color=SECTOR_EDGE, lw=0.8, zorder=1)

    # Labels de signos (centro de cada sector a radio 0.87)
    for i, sym in enumerate(ZODIAC_SYMBOLS):
        angle = math.radians((90 - i * 30 - 15) % 360)
        ax.text(
            angle, 0.87, sym,
            ha="center", va="center",
            color=LABEL_GRAY, fontsize=7, zorder=2,
        )

    # ── Planetas ────────────────────────────────────────────────────────
    planets_to_draw = [(planet_a, lon_a), (planet_b, lon_b)]
    for name, lon in planets_to_draw:
        theta = _lon_to_theta(lon)
        color  = PLANET_COLORS.get(name, "#ffffff")
        symbol = PLANET_SYMBOLS.get(name, "★")

        ax.scatter([theta], [0.65], s=60, color=color, zorder=5, linewidths=0)
        ax.text(
            theta, 0.52, symbol,
            ha="center", va="center",
            color=color, fontsize=10, fontweight="bold", zorder=6,
        )

    # ── Línea de aspecto ────────────────────────────────────────────────
    theta_a = _lon_to_theta(lon_a)
    theta_b = _lon_to_theta(lon_b)
    # Convertir a cartesianas para dibujar la línea
    r = 0.65
    x1, y1 = r * math.cos(theta_a), r * math.sin(theta_a)
    x2, y2 = r * math.cos(theta_b), r * math.sin(theta_b)
    # En proyección polar usamos una línea recta en coordenadas cartesianas
    # Matplotlib polar: necesitamos interpolar puntos en theta/r
    # Usamos un truco: dibujar en axes cartesianas superpuestas
    ax_cart = fig.add_axes(
        ax.get_position(),
        frameon=False,
        xlim=(-1, 1), ylim=(-1, 1),
        zorder=10,
    )
    ax_cart.axis("off")
    ax_cart.set_facecolor("none")
    ax_cart.plot(
        [x1, x2], [y1, y2],
        color=line_color, alpha=line_alpha, lw=1.5, zorder=10,
    )

    # ── Texto central: tipo de aspecto ──────────────────────────────────
    sym_a = PLANET_SYMBOLS.get(planet_a, planet_a)
    sym_b = PLANET_SYMBOLS.get(planet_b, planet_b)
    aspect_label = f"{aspect_key.capitalize()} {sym_a}{sym_b}"

    ax.text(
        0, 0, aspect_label,
        ha="center", va="center",
        color=TEXT_LIGHT, fontsize=8, zorder=7,
        transform=ax.transData,
    )

    # Fecha
    if exact_date:
        ax.text(
            0, -0.22, exact_date,
            ha="center", va="center",
            color=LABEL_GRAY, fontsize=7, zorder=7,
            transform=ax.transData,
        )

    # ── Estilo polar ────────────────────────────────────────────────────
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_rmax(1.0)
    ax.set_rmin(0.0)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=BG_COLOR, bbox_inches="tight", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Función 2: generate_hf_map_image
# ---------------------------------------------------------------------------

def generate_hf_map_image(subject_slug: str, domain: str = "global") -> bytes:
    """
    Genera imagen del Harmony Field de un sujeto para plataformas sociales.

    Args:
        subject_slug: slug del sujeto (ej: "einstein")
        domain:       dominio HF (ej: "global", "h10", "h07")
                      Se mapea a la propiedad GeoJSON: "global"→"hf_global", "h10"→"hf_h10"

    Returns:
        PNG en bytes (800×400px)

    Raises:
        FileNotFoundError: si el GeoJSON no existe para el slug dado
    """
    geojson_path = GEOJSON_DIR / f"{subject_slug}_domains.geojson"
    if not geojson_path.exists():
        raise FileNotFoundError(f"GeoJSON not found for {subject_slug}: {geojson_path}")

    # Determinar propiedad HF
    if domain == "global":
        hf_field = "hf_global"
    else:
        hf_field = f"hf_{domain}"

    # Cargar GeoJSON
    with open(geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)

    features = geojson["features"]
    lons, lats, hf_vals = [], [], []

    for feat in features:
        coords = feat["geometry"]["coordinates"]  # [lon, lat]
        props  = feat["properties"]

        hf = props.get(hf_field)
        if hf is None:
            print(f"[WARNING] Campo '{hf_field}' no encontrado en GeoJSON — usando hf_global")
            hf = props.get("hf_global", 0.0)

        lons.append(coords[0])
        lats.append(coords[1])
        hf_vals.append(float(hf))

    lons    = np.array(lons)
    lats    = np.array(lats)
    hf_vals = np.array(hf_vals)

    # Normalizar al rango del dataset para el colormap
    hf_min, hf_max = hf_vals.min(), hf_vals.max()

    fig, ax = plt.subplots(figsize=(8, 4), dpi=100, facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    sc = ax.scatter(
        lons, lats,
        c=hf_vals,
        cmap="RdYlGn",
        vmin=hf_min, vmax=hf_max,
        s=6,
        linewidths=0,
        alpha=0.7,
        zorder=2,
    )

    # Watermark
    ax.text(
        0.99, 0.02, "abu-oracle.com",
        transform=ax.transAxes,
        ha="right", va="bottom",
        color=WATERMARK, fontsize=8,
        zorder=5,
    )

    ax.axis("off")
    plt.tight_layout(pad=0)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=BG_COLOR, bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf.read()
