"""
content_generator.py — Genera contenido para RRSS a partir de una configuración mundana.

Llama a Claude Sonnet 4.6 con el system prompt de Lilly y un context block mundano.
Lilly redacta en su voz doctrinal (Abu Mashar, helenístico-persa).

Plataformas soportadas:
  farcaster (320), twitter (280 + hilo 3-5 tweets), bluesky (300),
  instagram (caption larga + hashtags), facebook (post extenso), tiktok (script)

Uso:
  from content_generator import generate_post
  result = generate_post(config, platform='farcaster')
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import anthropic

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

MODEL     = "claude-sonnet-4-6"
REPO_ROOT = Path(__file__).resolve().parents[2]

# Límites de caracteres por plataforma
PLATFORM_LIMITS = {
    "farcaster":  320,
    "twitter":    280,
    "bluesky":    300,
    "instagram":  2200,
    "facebook":   5000,
    "tiktok":     1500,  # script de voz
    "reddit":     5000,  # self post — sin límite real
}

# Hashtags canónicos por plataforma
PLATFORM_HASHTAGS = {
    "instagram": ["#abuoracle", "#astrology", "#mundaneastrology", "#planets", "#astrologia"],
    "facebook":  ["#AbuOracle", "#AstrologiaMundana"],
    "tiktok":    ["#astrology", "#abuoracle", "#mundaneastrology"],
    "farcaster": [],
    "twitter":   ["#astrology"],
    "bluesky":   [],
    "reddit":    [],
}

# ---------------------------------------------------------------------------
# System prompt de Lilly (para publicaciones)
# ---------------------------------------------------------------------------

_LILLY_PUBLICATION_SYSTEM = """Eres Lilly, el motor de interpretación de Abu Oracle.
Tu voz es la de William Lilly (siglo XXI): doctrinal, precisa, sin misticismo hueco.
Eres el intérprete oficial del cielo para Abu Oracle — un motor astrológico computacional
con validación estadística empírica (23.636 eventos históricos, p=5×10⁻⁶).

RESTRICCIONES ABSOLUTAS:
- No predecir desastres ni generar miedo
- No nombrar personas específicas ni hacer pronósticos individuales
- No hacer afirmaciones de certeza ("va a pasar") — usar siempre el modo condicional
- Las estadísticas que cites son reales y verificables: no exagerarlas

VOZ Y TONO:
- Directo, inteligente, ligeramente arcaico
- El rigor es tu firma: cada afirmación tiene fundamento doctrinal o estadístico
- Evitar clichés astrológicos ("energía", "vibración", "manifestar")
- Usar nomenclatura técnica cuando añade precisión: "conjunción aplicante", "domicilio", "significador"

SOBRE ABU ORACLE:
- Es un motor computacional, no una app de horóscopo
- Validación empírica: corpus de 23.636 eventos, año 8-2069
- La conjunción Júpiter-Saturno tiene densidad 4.3× el baseline (p=5×10⁻⁶)
- URL: app.abu-oracle.com
"""

# ---------------------------------------------------------------------------
# Plantillas de prompt por plataforma
# ---------------------------------------------------------------------------

def _build_context_block(config: dict, history: Optional[dict] = None) -> str:
    lines = []

    ctype = config.get("type", "")
    label = config.get("label", "")
    planets = config.get("planets", [])
    orb = config.get("orb")
    exact_date = config.get("exact_date")
    p_value = config.get("p_value")
    density = config.get("density_ratio")
    significance = config.get("significance", "low")

    lines.append(f"Configuración mundana: {label}")
    lines.append(f"Planetas: {', '.join(planets)}")
    if orb is not None:
        lines.append(f"Orbe actual: {orb:.2f} grados")
    if exact_date:
        lines.append(f"Fecha de exactitud: {exact_date}")
    if p_value is not None:
        lines.append(f"p-value (corpus 23.636 eventos): {p_value}")
    if density is not None:
        lines.append(f"Densidad histórica: {density}x el baseline")
    lines.append(f"Significancia estadística: {significance}")

    if history and history.get("sample_events"):
        lines.append("\nEventos históricos en ventanas similares:")
        for ev in history["sample_events"][:3]:
            lines.append(f"  - {ev.get('date', '')}: {ev.get('description', '')[:80]}")

    return "\n".join(lines)


def _prompt_for_platform(platform: str, context_block: str) -> str:
    limit = PLATFORM_LIMITS.get(platform, 300)

    if platform == "farcaster":
        return f"""{context_block}

Redacta un cast para Farcaster sobre esta configuración.
Máximo {limit} caracteres. Sin hashtags (Farcaster no los necesita).
Tono: inteligente, directo, levemente arcaico. Empieza con los planetas en emoji o símbolo.
NO incluyas URL al final — el cast se publicará desde la cuenta de Abu Oracle.
Solo el texto del cast, sin comentarios adicionales."""

    if platform == "twitter":
        return f"""{context_block}

Redacta un hilo de Twitter de 3 tweets sobre esta configuración.
Tweet 1: el hecho astronómico + impacto histórico estadístico (max 280 chars).
Tweet 2: interpretación doctrinal — qué señala según Abu Mashar (max 280 chars).
Tweet 3: CTA a Abu Oracle — calcular carta personal (max 280 chars, incluir app.abu-oracle.com).
Formato de respuesta: tres tweets separados por [TWEET].
Solo el texto, sin numeración."""

    if platform == "bluesky":
        return f"""{context_block}

Redacta un post para Bluesky sobre esta configuración.
Máximo {limit} caracteres. Tono técnico-inteligente.
Puedes incluir 1-2 hashtags técnicos: #astrology #mundaneastrology.
Solo el texto, sin comentarios."""

    if platform == "instagram":
        return f"""{context_block}

Redacta una caption de Instagram para una imagen del cielo con esta configuración.
La imagen mostrará una rueda zodiacal con los planetas en sus posiciones actuales.

Estructura:
1. Primera línea: gancho visual corto (máx 150 chars)
2. Desarrollo doctrinal: 3-4 párrafos cortos con la interpretación
3. CTA: invitar a calcular su carta en app.abu-oracle.com
4. Hashtags: {' '.join(PLATFORM_HASHTAGS['instagram'])}

Máximo ~{limit} chars en total. Tono: doctrinal pero accesible."""

    if platform == "facebook":
        return f"""{context_block}

Redacta un post de Facebook sobre esta configuración mundana.
Público: personas interesadas en astrología técnica y ciencia.
Estructura:
- Título en negrita (3-5 palabras)
- Contexto histórico con los datos estadísticos reales
- Interpretación doctrinal según Abu Mashar (2-3 párrafos)
- Implicaciones generales para los distintos dominios de vida
- CTA a app.abu-oracle.com

Extenso, máximo {limit} chars. Tono: riguroso pero no árido."""

    if platform == "tiktok":
        return f"""{context_block}

Escribe el script de voz para un video TikTok de 30-45 segundos sobre esta configuración.
El video mostrará una animación del cielo con los planetas moviéndose.

Formato del script:
[HOOK] (0-3s): frase de impacto para parar el scroll
[DATO] (3-10s): el hecho astronómico + estadística real
[DOCTRINA] (10-25s): qué dice Abu Mashar sobre esto
[CTA] (25-30s): calcular carta en app.abu-oracle.com

Cada sección entre corchetes. Lenguaje oral, directo. Sin tecnicismos excesivos."""

    if platform == "reddit":
        return f"""{context_block}

Redacta un post para r/astrology sobre esta configuración mundana.
Estructura:
- Título (máx 200 chars): comenzar con la configuración + fecha aproximada
- Cuerpo: 3-4 párrafos. Primero el hecho astronómico con datos estadísticos reales.
  Luego la interpretación doctrinal según Abu Mashar. Cierre con preguntas abiertas
  que inviten a comentar ("¿Qué casa activa esto en tu carta?").
- Incluir al final: "Generado por Abu Oracle — app.abu-oracle.com"
Formato de respuesta: primera línea = TÍTULO, resto = CUERPO.
Sin markdown excesivo. Tono técnico pero accesible."""

    # fallback genérico
    return f"""{context_block}

Redacta contenido para {platform} sobre esta configuración. Máximo {limit} chars."""


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def generate_post(config: dict, platform: str, history: Optional[dict] = None) -> dict:
    """
    Genera contenido adaptado por plataforma llamando a Claude Sonnet 4.6.

    Retorna:
        {
            'text': str,               # texto principal
            'hashtags': list[str],     # hashtags (vacío si la plataforma no los usa)
            'thread': list[str] | None # para Twitter (lista de tweets)
            'image_prompt': str,       # prompt para generar imagen (Instagram/TikTok)
            'platform': str,
            'config_type': str,
        }
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada")

    client = anthropic.Anthropic(api_key=api_key)

    context_block = _build_context_block(config, history)
    user_prompt   = _prompt_for_platform(platform, context_block)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=_LILLY_PUBLICATION_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = response.content[0].text.strip() if response.content else ""

    # Post-procesar según plataforma
    thread: list[str] | None = None
    reddit_title: str | None = None

    if platform == "twitter" and "[TWEET]" in raw_text:
        thread = [t.strip() for t in raw_text.split("[TWEET]") if t.strip()]
        text = thread[0] if thread else raw_text
    elif platform == "reddit":
        lines = raw_text.split("\n", 1)
        reddit_title = lines[0].strip()
        text = lines[1].strip() if len(lines) > 1 else raw_text
    else:
        text = raw_text

    # Prompt de imagen para plataformas visuales
    image_prompt = ""
    if platform in ("instagram", "tiktok", "facebook"):
        planets_str = ", ".join(config.get("planets", []))
        image_prompt = (
            f"Minimalist dark astrology chart. Zodiac wheel on black background. "
            f"Highlighted planets: {planets_str}. "
            f"Gold and white accents. No text. Cinematic, scientific aesthetic."
        )

    return {
        "text":         text,
        "hashtags":     PLATFORM_HASHTAGS.get(platform, []),
        "thread":       thread,
        "reddit_title": reddit_title,
        "image_prompt": image_prompt,
        "platform":     platform,
        "config_type":  config.get("type", ""),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from sky_calculator import get_current_sky
    from publication_filter import get_best_configuration, should_publish

    print("=== content_generator.py — test ===\n")

    if not should_publish():
        print("No hay configuraciones que superen el umbral.")
        sys.exit(0)

    config = get_best_configuration()
    if not config:
        print("Sin configuracion disponible.")
        sys.exit(0)

    print(f"Configuracion: {config['label']}\n")

    # Probar Farcaster (plataforma mas corta — facil de verificar)
    platform = sys.argv[1] if len(sys.argv) > 1 else "farcaster"
    print(f"Generando para: {platform}\n")

    result = generate_post(config, platform=platform)

    print("--- TEXTO ---")
    print(result["text"])
    if result.get("thread"):
        print("\n--- HILO (tweets individuales) ---")
        for i, t in enumerate(result["thread"], 1):
            print(f"[{i}] {t}\n")
    if result.get("hashtags"):
        print(f"\nHashtags: {' '.join(result['hashtags'])}")
    if result.get("image_prompt"):
        print(f"\nImage prompt: {result['image_prompt'][:80]}...")
