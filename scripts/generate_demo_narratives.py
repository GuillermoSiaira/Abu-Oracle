"""
Generate relocation narratives for demo subjects.

- Online mode (default): calls Lilly Engine POST /api/ai/interpret
- Offline mode (--offline): generates structured narratives from ranking data

Usage:
    python scripts/generate_demo_narratives.py              # requires Lilly on :8001
    python scripts/generate_demo_narratives.py --offline     # no services needed
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime

import requests

ROOT = Path(__file__).resolve().parent.parent
DEMO_DIR = ROOT / "output" / "demo"

ZODIAC_SIGNS = [
    "Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo",
    "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"
]
SIGN_ELEMENTS = {
    "Aries": "Fuego", "Tauro": "Tierra", "Géminis": "Aire", "Cáncer": "Agua",
    "Leo": "Fuego", "Virgo": "Tierra", "Libra": "Aire", "Escorpio": "Agua",
    "Sagitario": "Fuego", "Capricornio": "Tierra", "Acuario": "Aire", "Piscis": "Agua"
}


def lon_to_sign(lon: float) -> str:
    idx = int(lon / 30) % 12
    return ZODIAC_SIGNS[idx]


def generate_offline_narrative(subject: dict, ranking: list) -> dict:
    """Build a structured narrative from ranking data without LLM."""
    name = subject["display_name"]
    natal_hf = subject.get("natal_hf", 0)
    max_hf = subject.get("max_hf", 0)
    gain_pct = ((max_hf - natal_hf) / natal_hf * 100) if natal_hf > 0 else 0

    top3 = ranking[:3]
    top_cities = [f"{r.get('city', '?')} ({r.get('country', '?')})" for r in top3]
    top_hf = [r.get("hf_total_v3", 0) for r in top3]

    # ASC signs for top locations
    asc_signs = [lon_to_sign(r.get("asc_lon", 0)) for r in top3]
    mc_signs = [lon_to_sign(r.get("mc_lon", 0)) for r in top3]

    # Determine geographic pattern
    lats = [r.get("relocation_latitude", 0) for r in top3]
    avg_lat = sum(lats) / len(lats) if lats else 0
    hemisphere = "hemisferio sur" if avg_lat < 0 else "hemisferio norte"
    lat_zone = "latitudes altas" if abs(avg_lat) > 50 else "latitudes medias" if abs(avg_lat) > 25 else "latitudes ecuatoriales"

    headline = f"Relocalización HF para {name}: {top_cities[0]} lidera el ranking"

    narrative = (
        f"El análisis del campo armónico (Harmony Field) de {name} revela un patrón "
        f"geográfico definido: las ubicaciones óptimas se concentran en {lat_zone} del {hemisphere}. "
        f"La puntuación HF natal es {natal_hf:.2f}, mientras que la mejor ubicación "
        f"({top_cities[0]}) alcanza {top_hf[0]:.2f} — un incremento del {gain_pct:.1f}%.\n\n"
        f"Las tres mejores ciudades son:\n"
        f"1. **{top_cities[0]}** (HF: {top_hf[0]:.2f}) — ASC en {asc_signs[0]}, MC en {mc_signs[0]}\n"
        f"2. **{top_cities[1]}** (HF: {top_hf[1]:.2f}) — ASC en {asc_signs[1]}, MC en {mc_signs[1]}\n"
        f"3. **{top_cities[2]}** (HF: {top_hf[2]:.2f}) — ASC en {asc_signs[2]}, MC en {mc_signs[2]}\n\n"
        f"El componente de angularidad (hf_angles) y la distribución de casas (hf_houses) "
        f"son los factores que más varían geográficamente, mientras que los aspectos planetarios "
        f"(hf_aspects) permanecen constantes. Esto indica que la relocalización modifica "
        f"fundamentalmente cómo se expresan las energías planetarias a través de las casas "
        f"y los ángulos del horizonte."
    )

    # Build component analysis
    if top3:
        best = top3[0]
        aspects_pct = best.get("hf_aspects", 0) / best.get("hf_total_v3", 1) * 100
        angles_pct = best.get("hf_angles", 0) / best.get("hf_total_v3", 1) * 100
        houses_pct = best.get("hf_houses", 0) / best.get("hf_total_v3", 1) * 100
    else:
        aspects_pct = angles_pct = houses_pct = 33

    actions = [
        f"Evaluar {top_cities[0]} como destino prioritario (mayor ganancia HF: +{gain_pct:.1f}%)",
        f"Considerar {top_cities[1]} y {top_cities[2]} como alternativas viables",
        f"La angularidad ({angles_pct:.0f}% del total) es el factor más sensible a la ubicación",
        "Comparar el ranking HF con factores prácticos (idioma, clima, oportunidades)",
    ]

    return {
        "headline": headline,
        "narrative": narrative,
        "actions": actions,
        "astro_metadata": {
            "source": "offline",
            "language": "es",
            "model": "rule-based",
            "natal_hf": round(natal_hf, 4),
            "max_hf": round(max_hf, 4),
            "gain_pct": round(gain_pct, 2),
            "top_city": top_cities[0] if top_cities else None,
            "components": {
                "aspects_pct": round(aspects_pct, 1),
                "angles_pct": round(angles_pct, 1),
                "houses_pct": round(houses_pct, 1),
            }
        }
    }


def generate_online_narrative(subject: dict, ranking: list, lilly_url: str) -> dict:
    """Call Lilly Swarm /api/chat for LLM-based narrative."""
    name = subject["display_name"]
    natal_hf = subject.get("natal_hf", 0)
    max_hf = subject.get("max_hf", 0)
    gain_pct = ((max_hf - natal_hf) / natal_hf * 100) if natal_hf > 0 else 0

    top5 = ranking[:5]
    top5_data = []
    for i, r in enumerate(top5):
        top5_data.append({
            "rank": i + 1,
            "city": r.get("city", "?"),
            "country": r.get("country", "?"),
            "hf_total": round(r.get("hf_total_v3", 0), 2),
            "hf_aspects": round(r.get("hf_aspects", 0), 2),
            "hf_angles": round(r.get("hf_angles", 0), 2),
            "hf_houses": round(r.get("hf_houses", 0), 2),
            "asc_sign": lon_to_sign(r.get("asc_lon", 0)),
            "mc_sign": lon_to_sign(r.get("mc_lon", 0)),
            "lat": r.get("relocation_latitude", 0),
            "lon": r.get("relocation_longitude", 0),
        })

    context = {
        "type": "relocation_analysis",
        "subject": name,
        "natal_hf": round(natal_hf, 2),
        "max_hf": round(max_hf, 2),
        "gain_pct": round(gain_pct, 1),
        "top_cities": top5_data,
    }

    message = (
        f"Genera una interpretación de relocalización astrológica para {name}. "
        f"Su HF natal es {natal_hf:.2f} y la mejor ubicación alcanza {max_hf:.2f} (+{gain_pct:.1f}%). "
        f"Usa el contexto JSON adjunto con el ranking de las 5 mejores ciudades. "
        f"Responde en formato JSON con las claves: headline (string), narrative (string con markdown), "
        f"actions (array de 3-4 strings con recomendaciones concretas)."
    )

    payload = {
        "message": message,
        "session_id": f"demo_{subject.get('slug', 'unknown')}",
        "context": context,
    }

    resp = requests.post(f"{lilly_url}/api/chat", json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    # Lilly returns {"response": "..."} — parse the JSON from the response text
    raw = data.get("response", "")
    try:
        # Try to extract JSON from markdown code block if present
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        parsed = json.loads(raw)
        parsed["astro_metadata"] = {
            "source": "lilly_swarm",
            "language": "es",
            "model": "gpt-4o",
            "natal_hf": round(natal_hf, 4),
            "max_hf": round(max_hf, 4),
            "gain_pct": round(gain_pct, 2),
        }
        return parsed
    except (json.JSONDecodeError, IndexError):
        # If Lilly didn't return valid JSON, wrap the raw response
        return {
            "headline": f"Relocalización HF para {name}",
            "narrative": raw,
            "actions": [],
            "astro_metadata": {
                "source": "lilly_swarm",
                "language": "es",
                "model": "gpt-4o",
                "natal_hf": round(natal_hf, 4),
                "max_hf": round(max_hf, 4),
                "gain_pct": round(gain_pct, 2),
                "parse_fallback": True,
            }
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate narratives for demo subjects")
    parser.add_argument("--offline", action="store_true", help="Generate rule-based narratives without Lilly")
    parser.add_argument("--lilly-url", default="http://localhost:8001", help="Lilly Engine URL")
    args = parser.parse_args()

    index_path = DEMO_DIR / "index.json"
    if not index_path.exists():
        print("ERROR: Run generate_demo_pack.py first")
        return

    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    subjects = index["subjects"]
    ok, fail = 0, 0

    for subj in subjects:
        slug = subj["slug"]
        subj_dir = DEMO_DIR / slug
        ranking_path = subj_dir / "ranking.json"

        if not ranking_path.exists():
            print(f"  SKIP {slug}: no ranking.json")
            fail += 1
            continue

        with open(ranking_path, "r", encoding="utf-8") as f:
            ranking = json.load(f)

        print(f"  {slug}... ", end="")

        if args.offline:
            narrative = generate_offline_narrative(subj, ranking)
        else:
            try:
                narrative = generate_online_narrative(subj, ranking, args.lilly_url)
            except Exception as e:
                print(f"Lilly error ({e}), falling back to offline")
                narrative = generate_offline_narrative(subj, ranking)

        out_path = subj_dir / "narrative.json"
        out_path.write_text(json.dumps(narrative, indent=2, ensure_ascii=False), encoding="utf-8")
        subj["has_narrative"] = True
        ok += 1
        print(f"OK ({narrative['astro_metadata']['source']})")

    # Update index
    index["subjects"] = subjects
    index["narratives_generated"] = datetime.now().isoformat()
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDone: {ok} narratives, {fail} skipped")


if __name__ == "__main__":
    main()
