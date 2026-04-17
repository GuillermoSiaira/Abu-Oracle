"""
content_generator.py — Genera contenido diferenciado para RRSS a partir de una
configuración mundana.

ESTILOS DE CONTENIDO (rotan automáticamente por día de la semana):
  stats       — liderado por la evidencia estadística (p-value, densidad, corpus)
  individual  — cómo activa cartas específicas según ascendente/casas
  geographic  — ángulo Harmony Field: dónde en el mundo importa esto (PROVISIONAL —
                citar como concepto y capacidad, no números específicos mientras
                el módulo HF está en desarrollo activo)
  doctrine    — interpretación doctrinal pura: Abu Mashar, Bonatti, Lilly 1647

Plataformas soportadas:
  farcaster (320), twitter (hilo 3 tweets), bluesky (300),
  instagram (caption larga), facebook (post extenso), tiktok (script),
  reddit (post + título)

Uso:
  from content_generator import generate_post
  result = generate_post(config, platform='bluesky')          # estilo auto-rotante
  result = generate_post(config, platform='bluesky', style='stats')  # forzar estilo
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
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
    "tiktok":     1500,   # script de voz
    "reddit":     5000,   # self post — sin límite real
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
# Estilos de contenido
#
# Cada estilo define un ángulo diferente para el mismo evento astronómico.
# La rotación garantiza variedad en el feed sin requerir intervención manual.
#
# NOTA SOBRE ESTILO "geographic":
#   El Harmony Field (HF) está en desarrollo activo — los módulos de cálculo
#   y sus pesos estadísticos pueden cambiar en próximas sesiones.
#   Los posts con este estilo deben citar la *capacidad del sistema* (qué puede
#   hacer Abu Oracle) y la *pregunta geográfica* (¿dónde resonará esto en tu carta?)
#   sin hacer afirmaciones de números HF específicos para configuraciones mundanas,
#   que dependen de la carta individual y no están disponibles en este pipeline.
#   Cuando el módulo HF esté estabilizado, este estilo puede enriquecerse con
#   ejemplos calculados (ej: "para Virgo ascendente, esta configuración activa H10
#   en ciudades a latitud 40-50°N").
# ---------------------------------------------------------------------------

CONTENT_STYLES: dict[str, dict] = {
    "stats": {
        "description": "Liderado por la evidencia estadística — p-values, corpus, densidad histórica",
        "instruction": (
            "El gancho del post son los datos estadísticos del context block: "
            "p-value, densidad histórica, tamaño del corpus. "
            "Empezá con el número — no con la interpretación. "
            "Luego: breve contexto de qué significa estadísticamente. "
            "Luego: qué dice la doctrina sobre esta configuración. "
            "El mensaje central es: 'esto no es creencia — es medición sobre 23.636 eventos históricos.' "
            "Terminar con CTA a app.abu-oracle.com."
        ),
    },
    "individual": {
        "description": "Cómo esta configuración activa cartas individuales según ascendente/casas",
        "instruction": (
            "El gancho es la personalización: el cielo es el mismo para todos, "
            "pero tu respuesta depende de tu carta natal. "
            "Da 2-3 ejemplos concretos de cómo esta configuración activa distintas casas "
            "según el ascendente: 'Si tu ascendente es X, esto activa tu Casa N (dominio Y)'. "
            "Elegí los ascendentes más representativos para la configuración. "
            "Mencionar que Abu Oracle calcula exactamente qué casa y qué señores están activados. "
            "Terminar con CTA a app.abu-oracle.com para ver la activación individual."
        ),
    },
    "geographic": {
        "description": (
            "Ángulo Harmony Field — dónde en el mundo importa esto para tu carta. "
            "PROVISIONAL: citar capacidad del sistema, no números HF específicos."
        ),
        "instruction": (
            "El gancho es la pregunta geográfica: la misma configuración planetaria "
            "resuena de forma distinta según tu carta natal Y tu ubicación geográfica. "
            "Enmarcar desde el Harmony Field de Abu Oracle: un campo escalar que calcula "
            "exactamente qué ciudades amplifican cada dominio de tu carta. "
            "Preguntar: ¿en qué ciudad del mundo activa esto tu dominio de carrera, amor, hogar? "
            "IMPORTANTE: no citar números HF específicos — citar la capacidad del sistema. "
            "El HF está validado estadísticamente para cartas individuales; los posts mundanos "
            "no tienen acceso a la carta del lector. "
            "Terminar con CTA a app.abu-oracle.com/map o app.abu-oracle.com."
        ),
    },
    "doctrine": {
        "description": "Interpretación doctrinal pura — Abu Mashar, Bonatti, William Lilly 1647",
        "instruction": (
            "Interpretá desde la doctrina clásica helenístico-persa: Abu Mashar, Bonatti, Lilly. "
            "Qué dicen los textos sobre esta configuración. En qué épocas históricas ocurrió "
            "y qué se puede inferir de esas ventanas. Qué dominios de vida señala la tradición. "
            "El rigor doctrinal y la precisión histórica son el diferenciador — "
            "no los datos estadísticos (aunque podés mencionar brevemente que están validados). "
            "Voz ligeramente arcaica. Terminar con CTA a app.abu-oracle.com."
        ),
    },
}

# Orden de rotación por día de semana (0=Lunes … 3=Jueves → repite)
_STYLE_ROTATION = ["stats", "individual", "geographic", "doctrine"]


def _select_style(config: dict, day_override: int | None = None) -> str:
    """
    Selecciona el estilo rotando por día de la semana (mod 4).
    Con cooldown de 3 días se cubren los 4 estilos en ~12 días.

    Args:
        config: configuración mundana (no se usa actualmente — reservado para
                lógica futura, ej: forzar 'stats' si p_value es muy bajo)
        day_override: inyectar día manualmente (0-6) para tests
    """
    day = day_override if day_override is not None else datetime.now(timezone.utc).weekday()
    return _STYLE_ROTATION[day % len(_STYLE_ROTATION)]


# ---------------------------------------------------------------------------
# System prompt de Lilly (para publicaciones)
# ---------------------------------------------------------------------------

_LILLY_PUBLICATION_SYSTEM = """Eres Lilly, el motor de interpretación de Abu Oracle.

Abu Oracle no es una app de horóscopo. Es un motor astrológico computacional con base
en la doctrina helenístico-persa (Abu Mashar, Bonatti, William Lilly 1647) y validación
estadística empírica sobre 23.636 eventos históricos (año 8–2069).

LO QUE NOS DIFERENCIA (incorporar en la voz, no declarar como lista):

1. ESTADÍSTICA REAL — nuestras afirmaciones tienen p-values, densidades históricas y
   corpus medibles. No interpretamos "energías" — calculamos correlaciones sobre datos.
   Ejemplo: conjunción Júpiter-Saturno → densidad 4.3× el baseline, p=5×10⁻⁶.

2. ACTIVACIÓN INDIVIDUAL — cualquier configuración mundana se mapea sobre la carta natal
   del usuario. Abu Oracle calcula exactamente qué casa, qué señor, qué técnica temporal
   está activada para CADA carta específica. El cielo colectivo es el contexto;
   la carta natal es la clave de lectura.

3. HARMONY FIELD (campo geográfico) — sistema único que calcula dónde en el mundo
   cada configuración resuena más para cada carta natal. No líneas de astrocartografía —
   un campo escalar continuo con base estadística.
   (En desarrollo activo — al mencionarlo, citar la capacidad del sistema, no números
   específicos derivados de cartas individuales.)

4. CONVERGENCIA TEMPORAL — Abu Oracle detecta cuándo profección anual + período firdaria
   + tránsito lento convergen sobre el mismo dominio simultáneamente. Un tránsito solo
   es contexto; la convergencia de tres técnicas temporales es señal.

RESTRICCIONES ABSOLUTAS:
- No predecir desastres específicos ni generar miedo
- No nombrar personas específicas ni hacer pronósticos individuales
- No afirmaciones de certeza ("va a pasar") — siempre modo condicional o histórico
- Las estadísticas que cites son las del context block — no inventar ni exagerar números
- No usar: "energía", "vibración", "manifestar", "el universo te habla", "alinear"

VOZ:
- Directo, inteligente, levemente arcaico. El rigor es la firma.
- Nomenclatura técnica cuando añade precisión: "conjunción aplicante", "domicilio",
  "significador", "orbe", "p-value", "densidad histórica", "señor del año"
- El post debe sentirse como algo que no puede encontrarse en ninguna otra cuenta.
  Porque estadísticamente verificado con 23.636 eventos, no puede.
"""

# ---------------------------------------------------------------------------
# Context block (datos de la configuración → prompt de usuario)
# ---------------------------------------------------------------------------

def _build_context_block(config: dict, history: Optional[dict] = None) -> str:
    lines = []

    ctype      = config.get("type", "")
    label      = config.get("label", "")
    planets    = config.get("planets", [])
    orb        = config.get("orb")
    exact_date = config.get("exact_date")
    p_value    = config.get("p_value")
    density    = config.get("density_ratio")
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


# ---------------------------------------------------------------------------
# Prompts por plataforma (con inyección de estilo)
# ---------------------------------------------------------------------------

def _prompt_for_platform(platform: str, context_block: str, style: str = "doctrine") -> str:
    limit          = PLATFORM_LIMITS.get(platform, 300)
    style_info     = CONTENT_STYLES.get(style, CONTENT_STYLES["doctrine"])
    style_instr    = style_info["instruction"]

    if platform == "farcaster":
        return f"""{context_block}

ÁNGULO DE ESTE POST ({style}):
{style_instr}

Redactá un cast para Farcaster. Máximo {limit} caracteres. Sin hashtags.
Empezá con los planetas en símbolo o emoji. Voz doctrinal e inteligente.
NO incluir URL al final — el cast se publica desde la cuenta Abu Oracle.
Solo el texto del cast, sin comentarios adicionales."""

    if platform == "bluesky":
        return f"""{context_block}

ÁNGULO DE ESTE POST ({style}):
{style_instr}

Redactá un post para Bluesky. Máximo {limit} caracteres.
Podés incluir 1-2 hashtags técnicos: #astrology #mundaneastrology.
Solo el texto, sin comentarios."""

    if platform == "twitter":
        return f"""{context_block}

ÁNGULO DE ESTE POST ({style}):
{style_instr}

Redactá un hilo de Twitter de 3 tweets.
Tweet 1: gancho desde el ángulo indicado (max 280 chars).
Tweet 2: desarrollo — interpretación doctrinal + contexto estadístico (max 280 chars).
Tweet 3: CTA — calcular carta personal en app.abu-oracle.com (max 280 chars).
Formato: tres tweets separados por [TWEET]. Solo el texto, sin numeración."""

    if platform == "instagram":
        return f"""{context_block}

ÁNGULO DE ESTE POST ({style}):
{style_instr}

Redactá una caption de Instagram para una imagen del cielo con esta configuración.
Estructura:
1. Primera línea: gancho visual corto (máx 150 chars)
2. Desarrollo: 3-4 párrafos cortos con el ángulo indicado
3. CTA: invitar a calcular carta en app.abu-oracle.com
4. Hashtags: {' '.join(PLATFORM_HASHTAGS['instagram'])}
Máximo ~{limit} chars en total."""

    if platform == "facebook":
        return f"""{context_block}

ÁNGULO DE ESTE POST ({style}):
{style_instr}

Redactá un post de Facebook sobre esta configuración mundana.
Público: personas interesadas en astrología técnica y ciencia.
Estructura:
- Título en negrita (3-5 palabras)
- Contexto desde el ángulo indicado con datos estadísticos reales
- Interpretación doctrinal según Abu Mashar (2-3 párrafos)
- Implicaciones para los distintos dominios de vida
- CTA a app.abu-oracle.com
Extenso, máximo {limit} chars."""

    if platform == "tiktok":
        return f"""{context_block}

ÁNGULO DE ESTE POST ({style}):
{style_instr}

Escribí el script de voz para un video TikTok de 30-45 segundos.
Formato:
[HOOK] (0-3s): frase de impacto para parar el scroll — desde el ángulo indicado
[DATO] (3-10s): hecho astronómico + estadística real
[DOCTRINA] (10-25s): qué dice Abu Mashar + activación individual/geográfica según el ángulo
[CTA] (25-30s): calcular carta en app.abu-oracle.com
Lenguaje oral, directo. Cada sección entre corchetes."""

    if platform == "reddit":
        return f"""{context_block}

ÁNGULO DE ESTE POST ({style}):
{style_instr}

Redactá un post para r/astrology.
Estructura:
- Título (máx 200 chars): configuración + fecha aproximada + gancho del ángulo
- Cuerpo: 3-4 párrafos. Primero el hecho astronómico con datos estadísticos reales.
  Luego el ángulo indicado desarrollado. Cerrar con preguntas abiertas
  ("¿Qué casa activa esto en tu carta?").
- Al final: "Calculado por Abu Oracle — app.abu-oracle.com"
Formato: primera línea = TÍTULO, resto = CUERPO. Sin markdown excesivo."""

    # fallback
    return f"""{context_block}

ÁNGULO: {style_instr}

Redactá contenido para {platform} sobre esta configuración. Máximo {limit} chars."""


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def generate_post(
    config: dict,
    platform: str,
    history: Optional[dict] = None,
    style: Optional[str] = None,
) -> dict:
    """
    Genera contenido adaptado por plataforma y estilo llamando a Claude Sonnet 4.6.

    Args:
        config:   configuración mundana (del sky_calculator)
        platform: plataforma destino
        history:  contexto histórico opcional (del sky_calculator)
        style:    estilo de contenido (stats|individual|geographic|doctrine).
                  Si None, se selecciona automáticamente por día de la semana.

    Retorna:
        {
            'text':         str,            # texto principal
            'hashtags':     list[str],
            'thread':       list[str]|None, # para Twitter
            'reddit_title': str|None,
            'image_prompt': str,            # prompt para imagen (IG/TikTok/FB)
            'platform':     str,
            'config_type':  str,
            'style':        str,            # estilo usado
        }
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada")

    if style is None:
        style = _select_style(config)

    client = anthropic.Anthropic(api_key=api_key)

    context_block = _build_context_block(config, history)
    user_prompt   = _prompt_for_platform(platform, context_block, style=style)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=_LILLY_PUBLICATION_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = response.content[0].text.strip() if response.content else ""

    # Post-procesar según plataforma
    thread:       list[str] | None = None
    reddit_title: str | None = None

    if platform == "twitter" and "[TWEET]" in raw_text:
        thread = [t.strip() for t in raw_text.split("[TWEET]") if t.strip()]
        text   = thread[0] if thread else raw_text
    elif platform == "reddit":
        lines        = raw_text.split("\n", 1)
        reddit_title = lines[0].strip()
        text         = lines[1].strip() if len(lines) > 1 else raw_text
    else:
        text = raw_text

    # Prompt de imagen para plataformas visuales
    image_prompt = ""
    if platform in ("instagram", "tiktok", "facebook"):
        planets_str  = ", ".join(config.get("planets", []))
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
        "style":        style,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    from sky_calculator import get_current_sky, get_historical_context
    from publication_filter import get_best_configuration, should_publish

    print("=== content_generator.py — test ===\n")
    print(f"Estilos disponibles: {list(CONTENT_STYLES.keys())}")
    print(f"Estilo de hoy (auto): {_select_style({})}\n")

    if not should_publish():
        print("No hay configuraciones que superen el umbral.")
        sys.exit(0)

    config = get_best_configuration()
    if not config:
        print("Sin configuración disponible.")
        sys.exit(0)

    print(f"Configuración: {config['label']}\n")

    platform  = sys.argv[1] if len(sys.argv) > 1 else "bluesky"
    style_arg = sys.argv[2] if len(sys.argv) > 2 else None
    print(f"Plataforma: {platform} | Estilo: {style_arg or 'auto'}\n")

    history = None
    try:
        history = get_historical_context(config.get("type", ""))
    except Exception:
        pass

    result = generate_post(config, platform=platform, history=history, style=style_arg)

    print(f"--- TEXTO (estilo: {result['style']}) ---")
    print(result["text"])
    if result.get("thread"):
        print("\n--- HILO (tweets) ---")
        for i, t in enumerate(result["thread"], 1):
            print(f"[{i}] {t}\n")
    if result.get("hashtags"):
        print(f"\nHashtags: {' '.join(result['hashtags'])}")
    if result.get("image_prompt"):
        print(f"\nImage prompt: {result['image_prompt'][:80]}...")
