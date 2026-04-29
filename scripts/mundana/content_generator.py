"""
content_generator.py — Genera contenido diferenciado para RRSS.

DOS MODOS:
  mundana  — posts sobre configuraciones planetarias activas (event-driven)
  doctrine — posts sobre la arquitectura y resultados del sistema HF_v6
             (fuente: presentación "De la Adivinación Discreta a la Física de Campos")

ESTILOS MUNDANA (rotan automáticamente por día de la semana):
  stats       — liderado por la evidencia estadística (p-value, densidad, corpus)
  individual  — cómo activa cartas específicas según ascendente/casas
  geographic  — ángulo Harmony Field: dónde en el mundo importa esto
  doctrine    — interpretación doctrinal pura: Abu Mashar, Bonatti, Lilly 1647

IDIOMAS soportados: es | en | fr | pt  (env var LANG o parámetro lang=)

Plataformas soportadas:
  farcaster (320), twitter (hilo 3 tweets), bluesky (300),
  instagram (caption larga), facebook (post extenso), tiktok (script),
  reddit (post + título)

Uso:
  from content_generator import generate_post, generate_doctrine_post, get_doctrine_slide
  # Mundana
  result = generate_post(config, platform='bluesky', lang='en')
  # Doctrine
  slide  = get_doctrine_slide()
  result = generate_doctrine_post(slide, platform='bluesky', lang='en')
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import anthropic
from anthropic import AnthropicVertex
from image_generator import generate_sky_diagram

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

# ---------------------------------------------------------------------------
# Slide Concepts — fuente de posts doctrinales sobre el sistema HF_v6
# Cada entry es un concepto publicable independiente de eventos astronómicos.
# Extraídos de "De la Adivinación Discreta a la Física de Campos Continuos"
# ---------------------------------------------------------------------------

SLIDE_CONCEPTS: list[dict] = [
    {
        "id": "epistemological_leap",
        "title_es": "Del símbolo al campo",
        "title_en": "From Symbol to Field",
        "core_claim_es": (
            "La astrología tradicional no falló por sus premisas — falló por su tecnología. "
            "Ptolomeo y Lilly operaban con tablas estáticas, divisiones rígidas y puntos discretos "
            "porque no existía otra opción. Abu Oracle resuelve el mismo problema con campos "
            "escalares continuos matemáticamente diferenciables sobre 9.425 coordenadas terrestres."
        ),
        "core_claim_en": (
            "Traditional astrology didn't fail because of its premises — it failed because of its technology. "
            "Ptolemy and Lilly worked with static tables, rigid divisions, and discrete points "
            "because no alternative existed. Abu Oracle solves the same problem with continuous "
            "scalar fields mathematically differentiable across 9,425 Earth coordinates."
        ),
        "key_contrast_es": "Tablas estáticas → Campo escalar continuo",
        "key_contrast_en": "Static tables → Continuous scalar field",
        "slide_ref": 1,
    },
    {
        "id": "discrete_model_collapse",
        "title_es": "El universo no opera por compartimentos",
        "title_en": "The universe doesn't operate in compartments",
        "core_claim_es": (
            "La física real opera a través de gradientes electromagnéticos y campos escalares "
            "matemáticamente diferenciables. El modelo discreto (signos de 30°, casas con bordes duros) "
            "era una aproximación limitada por la tecnología disponible. "
            "Un planeta a 29°59' de un signo no 'cambia de comportamiento' al cruzar los 30°."
        ),
        "core_claim_en": (
            "Real physics operates through electromagnetic gradients and mathematically differentiable "
            "scalar fields. The discrete model (30° signs, hard-bordered houses) was an approximation "
            "limited by available technology. "
            "A planet at 29°59' of a sign doesn't 'change behavior' when it crosses 30°."
        ),
        "key_contrast_es": "Compartimentos estancos → Gradientes continuos",
        "key_contrast_en": "Rigid compartments → Continuous gradients",
        "slide_ref": 2,
    },
    {
        "id": "toroidal_cosmology",
        "title_es": "Los planetas como osciladores",
        "title_en": "Planets as oscillators",
        "core_claim_es": (
            "Bajo el modelo toroidal: el universo es un campo electromagnético continuo. "
            "Los planetas no influyen por 'magia a distancia' — operan como magnetorquers naturales "
            "que alteran la densidad, fase y vibración del medio local. "
            "La luz no es un proyectil en el vacío — es la tasa de inducción de este campo cosmológico. "
            "Bajo este modelo, la astrología deja de ser adivinación para convertirse en "
            "modulación de frecuencia pura."
        ),
        "core_claim_en": (
            "Under the toroidal model: the universe is a continuous electromagnetic field. "
            "Planets don't influence through 'action at a distance magic' — they operate as natural "
            "magnetorquers altering the local density, phase, and vibration of the medium. "
            "Light is not a projectile in a vacuum — it is the induction rate of this cosmological field. "
            "Under this model, astrology ceases to be divination and becomes pure frequency modulation."
        ),
        "key_contrast_es": "Magia a distancia → Modulación de frecuencia",
        "key_contrast_en": "Action at a distance → Frequency modulation",
        "slide_ref": 3,
    },
    {
        "id": "hf_spectrum_analyzer",
        "title_es": "El fin de la AstroCartografía tradicional",
        "title_en": "The end of traditional AstroCartography",
        "core_claim_es": (
            "La AstroCartografía tradicional dibuja líneas abstractas en mapas 2D. "
            "El Harmony Field (HF_v6) mide la impedancia y resonancia real de un individuo "
            "contra el flujo electromagnético del campo planetario local. "
            "Es una función matemática continua sobre 9.425 puntos terrestres — "
            "no líneas proyectivas, sino densidad de campo diferenciable. "
            "El objetivo: identificar nodos de densidad magnética óptimos para "
            "facilitar la expresión del potencial latente."
        ),
        "core_claim_en": (
            "Traditional AstroCartography draws abstract lines on 2D maps. "
            "The Harmony Field (HF_v6) measures the real impedance and resonance of an individual "
            "against the local planetary electromagnetic flow. "
            "It is a continuous mathematical function across 9,425 Earth coordinates — "
            "not projective lines, but differentiable field density. "
            "The goal: identify optimal magnetic density nodes to facilitate expression of latent potential."
        ),
        "key_contrast_es": "Líneas abstractas → Campo escalar diferenciable",
        "key_contrast_en": "Abstract lines → Differentiable scalar field",
        "slide_ref": 5,
    },
    {
        "id": "signal_decoupling",
        "title_es": "Por qué HF_v5 falló — y cómo se corrigió",
        "title_en": "Why HF_v5 failed — and how it was fixed",
        "core_claim_es": (
            "HF_v5 introdujo la Dignidad Esencial dentro del Kernel de Aspecto. El resultado: "
            "mezclar geometría espacial con valoración cualitativa invirtió la señal. "
            "La solución de HF_v6: dos mecanismos arquitectónicamente separados e independientes. "
            "Mecanismo 1 — Geometría Pura (señal posicional): kernels gaussianos sobre separación angular. "
            "Mecanismo 2 — Cualidad Modulada (volumen y contenido): dignidades × angularidad. "
            "La separación no fue conveniencia de ingeniería — fue corrección doctrinal fundamentada en Ptolomeo."
        ),
        "core_claim_en": (
            "HF_v5 introduced Essential Dignity inside the Aspect Kernel. The result: "
            "mixing spatial geometry with qualitative valuation inverted the signal. "
            "HF_v6 solution: two architecturally separated, mathematically independent mechanisms. "
            "Mechanism 1 — Pure Geometry (positional signal): Gaussian kernels on angular separation. "
            "Mechanism 2 — Modulated Quality (volume and content): dignities × angularity. "
            "The separation wasn't engineering convenience — it was doctrinal correction grounded in Ptolemy."
        ),
        "key_contrast_es": "Señal mezclada (v5) → Mecanismos desacoplados (v6)",
        "key_contrast_en": "Mixed signal (v5) → Decoupled mechanisms (v6)",
        "slide_ref": 6,
    },
    {
        "id": "pure_geometry",
        "title_es": "La geometría natal como señal física",
        "title_en": "Natal geometry as a physical signal",
        "core_claim_es": (
            "Los aspectos entre planetas no son buenas o malas 'energías'. "
            "Son hechos geométricos de la carta natal — resonancias astronómicas neutras "
            "calculadas mediante kernels gaussianos sobre separación angular. "
            "Sin signo moral: conjunciones, trígonos, cuadraturas y oposiciones son igualmente reales. "
            "La conjunción posee el peso máximo absoluto (w_c = +2.5), operando como "
            "la línea base de la topografía del campo escalar. "
            "Los pesos son diferenciados, no moralizados."
        ),
        "core_claim_en": (
            "Aspects between planets are not good or bad 'energies'. "
            "They are geometric facts of the natal chart — neutral astronomical resonances "
            "calculated through Gaussian kernels on angular separation. "
            "No moral sign: conjunctions, trines, squares, and oppositions are equally real. "
            "The conjunction carries the maximum absolute weight (w_c = +2.5), operating as "
            "the baseline of the scalar field topography. "
            "Weights are differentiated, not moralized."
        ),
        "key_contrast_es": "Aspectos buenos/malos → Resonancias gaussianas neutras",
        "key_contrast_en": "Good/bad aspects → Neutral Gaussian resonances",
        "slide_ref": 7,
    },
    {
        "id": "modulated_quality",
        "title_es": "Dignidad esencial: el volumen del pico",
        "title_en": "Essential dignity: the volume of the peak",
        "core_claim_es": (
            "Mecanismo 2 del HF_v6: la dignidad esencial modula el volumen de la señal geométrica. "
            "Sistema D4 estricto de Ptolomeo: Domicilio (+5) · Exaltación (+4) · Peregrine (0) · "
            "Detrimento (-4) · Caída (-5). "
            "Regla operativa: un planeta Peregrine (0) anula la contribución al pico. "
            "Un planeta en Detrimento o Caída genera matemáticamente un valle de adversidad — "
            "no una predicción, sino una topografía del campo. "
            "Ejemplo: Júpiter en domicilio al MC → pico máximo. Marte en detrimento al ASC → valle."
        ),
        "core_claim_en": (
            "HF_v6 Mechanism 2: essential dignity modulates the volume of the geometric signal. "
            "Ptolemy's strict D4 system: Domicile (+5) · Exaltation (+4) · Peregrine (0) · "
            "Detriment (-4) · Fall (-5). "
            "Operative rule: a Peregrine planet (0) cancels the contribution to the peak. "
            "A planet in Detriment or Fall mathematically generates an adversity valley — "
            "not a prediction, but a field topography. "
            "Example: Jupiter domicile at MC → maximum peak. Mars detriment at ASC → valley."
        ),
        "key_contrast_es": "Valoración cualitativa subjetiva → Puntuación D4 matemática",
        "key_contrast_en": "Subjective qualitative valuation → Mathematical D4 scoring",
        "slide_ref": 8,
    },
    {
        "id": "domain_specificity",
        "title_es": "El campo global es ruido blanco",
        "title_en": "The global field is white noise",
        "core_claim_es": (
            "Si preguntas por la totalidad de los planetas, el campo global mezcla todas las frecuencias. "
            "Cohen's d global: +0.193. Ruido estadístico. "
            "El universo es sordo a preguntas inespecíficas. "
            "Axioma 8: cada dominio humano está regido por un subset específico de significadores de casa. "
            "Filtrar el modelo por esta intención no es una optimización de UX — "
            "es un Requisito Epistémico. "
            "Carrera (H10), amor (H07), hogar (H04): cada uno tiene su subset planetario, "
            "su propia topografía, su propia señal."
        ),
        "core_claim_en": (
            "Ask about all planets simultaneously, and the global field mixes all frequencies. "
            "Global Cohen's d: +0.193. Statistical noise. "
            "The universe is deaf to unspecific questions. "
            "Axiom 8: each human domain is governed by a specific subset of house significators. "
            "Filtering the model by this intention is not a UX optimization — "
            "it is an Epistemic Requirement. "
            "Career (H10), love (H07), home (H04): each has its own planetary subset, "
            "its own topography, its own signal."
        ),
        "key_contrast_es": "Campo global (ruido) → Subset de dominio (señal)",
        "key_contrast_en": "Global field (noise) → Domain subset (signal)",
        "slide_ref": 9,
    },
    {
        "id": "temporal_convergence",
        "title_es": "El Firdaria como amplificador del campo",
        "title_en": "Firdaria as field amplifier",
        "core_claim_es": (
            "Axioma 9.4: el espacio geográfico por sí solo indica potencial latente, "
            "no manifestación. "
            "Cuando el período planetario activo (Firdaria) cruza con el subset "
            "de significadores del dominio, HF_v6 aplica un amplificador matemático extremo (w=2.0). "
            "Ptolomeo: 'cuando los señores de los tiempos coinciden con los señores del evento, "
            "el efecto es extremo y sin aleación.' "
            "El Triángulo de Activación: Potencial Natal × Resonancia Geográfica × Activación Temporal."
        ),
        "core_claim_en": (
            "Axiom 9.4: geographic space alone indicates latent potential, not manifestation. "
            "When the active planetary period (Firdaria) intersects with the domain's "
            "significator subset, HF_v6 applies an extreme mathematical amplifier (w=2.0). "
            "Ptolemy: 'when the lords of the times coincide with the lords of the event, "
            "the effect is extreme and unmixed.' "
            "The Activation Triangle: Natal Potential × Geographic Resonance × Temporal Activation."
        ),
        "key_contrast_es": "Potencial latente → Manifestación activada",
        "key_contrast_en": "Latent potential → Activated manifestation",
        "slide_ref": 10,
    },
    {
        "id": "empirical_falsifiability",
        "title_es": "Los números: el data drop",
        "title_en": "The numbers: the data drop",
        "core_claim_es": (
            "Falsabilidad empírica estricta sobre 527 eventos biográficos verificados "
            "de 26 sujetos históricos. "
            "HF_v3 (sin desacoplamiento, sin filtro de dominio): "
            "H07 Relaciones d=+0.055 | H10 Carrera d=+0.056. Prácticamente cero. "
            "HF_v6 (mecanismos desacoplados + filtro Firdaria + especificidad de dominio): "
            "H07 Relaciones d=+0.587 | H10 Carrera d=+0.702. Efecto grande. "
            "La hipótesis doctrinal fue validada. "
            "Aislar la geometría de la dignidad, e interceptarla con especificidad "
            "espacial y temporal, genera una separación empírica radical."
        ),
        "core_claim_en": (
            "Strict empirical falsifiability on 527 verified biographical events "
            "from 26 historical subjects. "
            "HF_v3 (no decoupling, no domain filter): "
            "H07 Relationships d=+0.055 | H10 Career d=+0.056. Practically zero. "
            "HF_v6 (decoupled mechanisms + Firdaria filter + domain specificity): "
            "H07 Relationships d=+0.587 | H10 Career d=+0.702. Large effect. "
            "The doctrinal hypothesis was validated. "
            "Isolating geometry from dignity, and intersecting it with spatial "
            "and temporal specificity, produces a radical empirical separation."
        ),
        "key_contrast_es": "v3: d≈0 → v6: d=0.587–0.702 (efecto grande)",
        "key_contrast_en": "v3: d≈0 → v6: d=0.587–0.702 (large effect)",
        "slide_ref": 11,
    },
    {
        "id": "three_pillars",
        "title_es": "Tres preguntas, una plataforma",
        "title_en": "Three questions, one platform",
        "core_claim_es": (
            "Abu Oracle no interpreta símbolos estáticos ni emite adivinaciones. "
            "Computa campos escalares continuos, detecta convergencias espaciotemporales, "
            "y correlaciona resultados con eventos históricos reales. "
            "Pilar 1 — Dimensión Espacial: ¿Dónde? (Harmony Field v6). "
            "Pilar 2 — Dimensión Temporal: ¿Cuándo y por qué? (Grafo biográfico + Activación Firdaria). "
            "Pilar 3 — Validación Empírica: ¿Es falsable? (Estadística Bayesiana/Frecuentista). "
            "Es la formalización matemática y física definitiva de la tradición."
        ),
        "core_claim_en": (
            "Abu Oracle doesn't interpret static symbols or issue divinations. "
            "It computes continuous scalar fields, detects spatiotemporal convergences, "
            "and correlates results against real historical events. "
            "Pillar 1 — Spatial Dimension: Where? (Harmony Field v6). "
            "Pillar 2 — Temporal Dimension: When and why? (Biographical graph + Firdaria Activation). "
            "Pillar 3 — Empirical Validation: Is it falsifiable? (Bayesian/Frequentist Statistics). "
            "It is the definitive mathematical and physical formalization of the tradition."
        ),
        "key_contrast_es": "Adivinación → Plataforma de inteligencia transdisciplinaria",
        "key_contrast_en": "Divination → Transdisciplinary intelligence platform",
        "slide_ref": 12,
    },
]


def get_doctrine_slide(day_override: int | None = None) -> dict:
    """
    Selecciona el slide doctrinal del día, rotando con período de 3 días.
    Con 11 slides → ciclo completo en 33 días.
    """
    now = datetime.now(timezone.utc)
    day_of_year = now.timetuple().tm_yday if day_override is None else day_override
    return SLIDE_CONCEPTS[(day_of_year // 3) % len(SLIDE_CONCEPTS)]


# ---------------------------------------------------------------------------
# Idiomas soportados
# ---------------------------------------------------------------------------

_LANG_NAMES = {
    "es": "Spanish",
    "en": "English",
    "fr": "French",
    "pt": "Portuguese (Brazilian)",
}


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
# System prompt de Lilly (para publicaciones) — con soporte multilingüe
# ---------------------------------------------------------------------------

def _lilly_system(lang: str = "es") -> str:
    """Retorna el system prompt en el idioma indicado."""
    lang_name = _LANG_NAMES.get(lang, "Spanish")
    return f"""You are Lilly, Abu Oracle's interpretation engine.

Abu Oracle is not a horoscope app. It is a computational astrological engine grounded in
Hellenistic-Persian doctrine (Abu Mashar, Bonatti, William Lilly 1647) and empirically validated
against 527 historical biographical events from 26 subjects (years 8–2069).

WHAT SETS US APART (weave into your voice, don't list mechanically):

1. REAL STATISTICS — our claims carry p-values, historical densities, and measurable corpora.
   We don't interpret "energies" — we calculate correlations over data.
   Example: Jupiter-Saturn conjunction → density 4.3× baseline, p=5×10⁻⁶.

2. INDIVIDUAL ACTIVATION — any mundane configuration maps onto the user's natal chart.
   Abu Oracle calculates exactly which house, which lord, which temporal technique
   is activated for each specific chart. The collective sky is context; the natal chart is the key.

3. HARMONY FIELD (geographic field) — unique system computing where in the world each
   configuration resonates most for each natal chart. Not astrocartography lines —
   a continuous scalar field with statistical grounding.
   HF_v6 results: H07 Relationships Cohen's d=+0.587 | H10 Career d=+0.702 (large effect).

4. TEMPORAL CONVERGENCE — Abu Oracle detects when annual profection + Firdaria period
   + slow transit converge on the same domain simultaneously. A single transit is context;
   the convergence of three temporal techniques is signal.

ABSOLUTE CONSTRAINTS:
- No predicting specific disasters or generating fear
- No naming specific individuals or making individual forecasts
- No certainty claims ("it will happen") — always conditional or historical framing
- Statistics you cite come from the context block — never invent or exaggerate numbers
- Forbidden words: "energy", "vibration", "manifest", "the universe speaks to you", "align"

VOICE:
- Direct, intelligent, slightly archaic. Rigor is the signature.
- Technical nomenclature when it adds precision: "applying conjunction", "domicile",
  "significator", "orb", "p-value", "historical density", "lord of the year"
- The post must feel like nothing else on any other account. Because statistically
  validated against 527 events — it cannot be found elsewhere.

LANGUAGE: Write the entire post in {lang_name}. All text, hashtags context, and calls to action
must be in {lang_name}. Never mix languages within a single post.
"""

# Keep backward-compatible reference
_LILLY_PUBLICATION_SYSTEM = _lilly_system("es")


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

def _prompt_for_platform(
    platform: str,
    context_block: str,
    style: str = "doctrine",
    lang: str = "es",
) -> str:
    limit       = PLATFORM_LIMITS.get(platform, 300)
    style_info  = CONTENT_STYLES.get(style, CONTENT_STYLES["doctrine"])
    style_instr = style_info["instruction"]

    if platform == "farcaster":
        return f"""{context_block}

ANGLE FOR THIS POST ({style}):
{style_instr}

Write a Farcaster cast. Max {limit} characters. No hashtags.
Start with planet symbols or emoji. Doctrinal, intelligent voice.
Do NOT include URL at the end — the cast is published from the Abu Oracle account.
Output only the cast text, no additional comments."""

    if platform == "bluesky":
        return f"""{context_block}

ANGLE FOR THIS POST ({style}):
{style_instr}

Write a Bluesky post. Max {limit} characters.
You may include 1-2 technical hashtags: #astrology #mundaneastrology.
Output only the text, no additional comments."""

    if platform == "twitter":
        return f"""{context_block}

ANGLE FOR THIS POST ({style}):
{style_instr}

Write a Twitter thread of 3 tweets.
Tweet 1: hook from the indicated angle (max 280 chars).
Tweet 2: development — doctrinal interpretation + statistical context (max 280 chars).
Tweet 3: CTA — calculate personal chart at app.abu-oracle.com (max 280 chars).
Format: three tweets separated by [TWEET]. Output text only, no numbering."""

    if platform == "instagram":
        return f"""{context_block}

ANGLE FOR THIS POST ({style}):
{style_instr}

Write an Instagram caption for a sky image showing this configuration.
Structure:
1. First line: short visual hook (max 150 chars)
2. Development: 3-4 short paragraphs with the indicated angle
3. CTA: invite to calculate chart at app.abu-oracle.com
4. Hashtags: {' '.join(PLATFORM_HASHTAGS['instagram'])}
Max ~{limit} chars total."""

    if platform == "facebook":
        return f"""{context_block}

ANGLE FOR THIS POST ({style}):
{style_instr}

Write a Facebook post about this mundane configuration.
Audience: people interested in technical astrology and science.
Structure:
- Bold title (3-5 words)
- Context from the indicated angle with real statistical data
- Doctrinal interpretation per Abu Mashar (2-3 paragraphs)
- Implications for different life domains
- CTA to app.abu-oracle.com
Extended, max {limit} chars."""

    if platform == "tiktok":
        return f"""{context_block}

ANGLE FOR THIS POST ({style}):
{style_instr}

Write the voice script for a 30-45 second TikTok video.
Format:
[HOOK] (0-3s): impact phrase to stop the scroll — from the indicated angle
[DATA] (3-10s): astronomical fact + real statistic
[DOCTRINE] (10-25s): what Abu Mashar says + individual/geographic activation per the angle
[CTA] (25-30s): calculate chart at app.abu-oracle.com
Spoken language, direct. Each section in brackets."""

    if platform == "reddit":
        return f"""{context_block}

ANGLE FOR THIS POST ({style}):
{style_instr}

Write a post for r/astrology.
Structure:
- Title (max 200 chars): configuration + approximate date + angle hook
- Body: 3-4 paragraphs. First the astronomical fact with real statistical data.
  Then the indicated angle developed. Close with open questions
  ("What house does this activate in your chart?").
- At the end: "Calculated by Abu Oracle — app.abu-oracle.com"
Format: first line = TITLE, rest = BODY. No excessive markdown."""

    # fallback
    return f"""{context_block}

ANGLE: {style_instr}

Write content for {platform} about this configuration. Max {limit} chars."""


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def generate_post(
    config: dict,
    platform: str,
    history: Optional[dict] = None,
    style: Optional[str] = None,
    lang: str = "es",
) -> dict:
    """
    Genera contenido mundano adaptado por plataforma, estilo e idioma.

    Args:
        config:   configuración mundana (del sky_calculator)
        platform: plataforma destino
        history:  contexto histórico opcional (del sky_calculator)
        style:    estilo de contenido (stats|individual|geographic|doctrine).
                  Si None, se selecciona automáticamente por día de la semana.
        lang:     idioma de salida (es|en|fr|pt). Default: "es".

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
            'lang':         str,
        }
    """
    if style is None:
        style = _select_style(config)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = (
        AnthropicVertex(
            project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", "abu-oracle"),
            region=os.environ.get("VERTEX_REGION", "us-east5"),
        )
        if not api_key
        else anthropic.Anthropic(api_key=api_key)
    )

    context_block = _build_context_block(config, history)
    user_prompt   = _prompt_for_platform(platform, context_block, style=style, lang=lang)

    # Retry con backoff para rate limits (429) de Vertex AI
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=_lilly_system(lang),
                messages=[{"role": "user", "content": user_prompt}],
            )
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                wait = 30 * (attempt + 1)
                print(f"[content] Rate limit — reintentando en {wait}s (intento {attempt + 1}/3)")
                time.sleep(wait)
            else:
                raise

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

    # Generar imagen del diagrama de cielo
    image_bytes: bytes | None = None
    image_alt:   str  | None = None
    try:
        image_bytes = generate_sky_diagram(config)
        image_alt   = f"{config.get('config_type', 'configuración')} — {config.get('exact_date', '')}"
    except Exception as e:
        print(f"[WARNING] No se pudo generar imagen: {e}")

    return {
        "text":         text,
        "hashtags":     PLATFORM_HASHTAGS.get(platform, []),
        "thread":       thread,
        "reddit_title": reddit_title,
        "image_prompt": image_prompt,
        "image_bytes":  image_bytes,
        "image_alt":    image_alt,
        "platform":     platform,
        "config_type":  config.get("type", ""),
        "style":        style,
        "lang":         lang,
    }


# ---------------------------------------------------------------------------
# generate_doctrine_post — posts sobre el sistema HF_v6 (sin evento mundano)
# ---------------------------------------------------------------------------

def _doctrine_prompt_for_platform(
    platform: str,
    slide: dict,
    lang: str = "es",
) -> str:
    """Prompt para posts de doctrina del sistema, basados en slides de presentación."""
    limit  = PLATFORM_LIMITS.get(platform, 300)
    key    = "en" if lang == "en" else "es"
    title  = slide.get(f"title_{key}", slide.get("title_es", ""))
    claim  = slide.get(f"core_claim_{key}", slide.get("core_claim_es", ""))
    contrast = slide.get(f"key_contrast_{key}", slide.get("key_contrast_es", ""))

    base = f"""SLIDE CONCEPT:
Title: {title}
Core claim: {claim}
Key contrast: {contrast}

Abu Oracle empirical results to cite when relevant:
- H07 Relationships: Cohen's d = +0.587 (HF_v6) vs +0.055 (HF_v3)
- H10 Career: Cohen's d = +0.702 (HF_v6) vs +0.056 (HF_v3)
- Dataset: 527 verified biographical events, 26 historical subjects
- Jupiter-Saturn conjunction: density 4.3× baseline, p=5×10⁻⁶
"""

    if platform == "farcaster":
        return f"""{base}
Write a Farcaster cast presenting this concept. Max {limit} characters. No hashtags.
Voice: direct, scientific, slightly archaic. Not preachy — state the claim and the evidence.
The concept must stand alone without requiring knowledge of astrology.
No URL at end."""

    if platform == "bluesky":
        return f"""{base}
Write a Bluesky post presenting this concept. Max {limit} characters.
1-2 hashtags max: #astrology #harmonicfield or similar.
Hook: one line that makes a physicist or data scientist stop scrolling.
Include the key empirical numbers when they strengthen the argument.
End with app.abu-oracle.com"""

    if platform == "twitter":
        return f"""{base}
Write a Twitter thread of 3 tweets presenting this concept.
Tweet 1: the claim — make it provocative but precise (max 280 chars).
Tweet 2: the evidence — Cohen's d numbers, contrast with v3 if relevant (max 280 chars).
Tweet 3: the implication + CTA to app.abu-oracle.com (max 280 chars).
Format: three tweets separated by [TWEET]. No numbering."""

    if platform == "instagram":
        return f"""{base}
Write an Instagram caption presenting this concept for a scientific-aesthetic visual post.
Structure:
1. Hook line (max 120 chars) — make it quotable
2. 3-4 short paragraphs developing the concept with empirical backing
3. Question to the reader: what does this change for how you think about astrology?
4. CTA: app.abu-oracle.com
5. Hashtags: #abuoracle #astrology #harmonicfield #physics #data
Max {limit} chars."""

    if platform == "reddit":
        return f"""{base}
Write a Reddit post for r/astrology or r/DataIsBeautiful presenting this concept.
Structure:
- Title (max 200 chars): provocative, data-forward
- Body: 3-4 paragraphs. Lead with the empirical result, then explain the mechanism.
  Be precise with numbers. Invite skeptical discussion.
  Close: "More at Abu Oracle — app.abu-oracle.com"
Format: first line = TITLE, rest = BODY."""

    # fallback
    return f"""{base}
Write a {platform} post about this concept. Max {limit} chars. End with app.abu-oracle.com"""


def generate_doctrine_post(
    slide: dict,
    platform: str,
    lang: str = "es",
) -> dict:
    """
    Genera un post de doctrina del sistema HF_v6 a partir de un slide concept.
    No requiere configuración mundana activa.

    Args:
        slide:    entrada de SLIDE_CONCEPTS
        platform: plataforma destino
        lang:     idioma de salida (es|en|fr|pt)

    Retorna mismo shape que generate_post() con config_type="doctrine_{slide_id}"
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = (
        AnthropicVertex(
            project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", "abu-oracle"),
            region=os.environ.get("VERTEX_REGION", "us-east5"),
        )
        if not api_key
        else anthropic.Anthropic(api_key=api_key)
    )

    user_prompt = _doctrine_prompt_for_platform(platform, slide, lang=lang)

    for attempt in range(3):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=_lilly_system(lang),
                messages=[{"role": "user", "content": user_prompt}],
            )
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                wait = 30 * (attempt + 1)
                print(f"[doctrine] Rate limit — reintentando en {wait}s (intento {attempt + 1}/3)")
                time.sleep(wait)
            else:
                raise

    raw_text = response.content[0].text.strip() if response.content else ""

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

    slide_id = slide.get("id", "unknown")
    print(f"[doctrine] Slide: {slide_id} | Platform: {platform} | Lang: {lang} | {len(text)} chars")

    return {
        "text":         text,
        "hashtags":     PLATFORM_HASHTAGS.get(platform, []),
        "thread":       thread,
        "reddit_title": reddit_title,
        "image_prompt": "",
        "image_bytes":  None,
        "image_alt":    None,
        "platform":     platform,
        "config_type":  f"doctrine_{slide_id}",
        "style":        "doctrine",
        "lang":         lang,
        "slide_id":     slide_id,
    }


# ---------------------------------------------------------------------------
# Showcase caption (para showcase_publisher.py)
# ---------------------------------------------------------------------------

DOMAIN_LABELS: dict[str, str] = {
    "global": "Campo Global",
    "h1":  "Identidad",
    "h2":  "Recursos",
    "h4":  "Hogar",
    "h5":  "Creatividad",
    "h6":  "Trabajo y Salud",
    "h7":  "Amor y Relaciones",
    "h9":  "Expansión",
    "h10": "Carrera",
}

SUBJECT_NAMES: dict[str, str] = {
    "einstein": "Albert Einstein",
    "freud":    "Sigmund Freud",
    "jung":     "Carl Jung",
    "tesla":    "Nikola Tesla",
    "gandhi":   "Mahatma Gandhi",
    "frida":    "Frida Kahlo",
    "picasso":  "Pablo Picasso",
    "vangogh":  "Vincent van Gogh",
    "borges":   "Jorge Luis Borges",
    "bowie":    "David Bowie",
}

SHOWCASE_LIMITS: dict[str, int] = {
    "bluesky":   280,
    "twitter":   220,
    "instagram": 400,
}


def generate_showcase_caption(
    subject_slug: str,
    domain: str,
    top3_cities: list[str],
    lang: str = "es",
    platform: str = "bluesky",
) -> str:
    """
    Genera una caption para el mapa HF de un sujeto histórico usando Claude Sonnet 4.6.

    Args:
        subject_slug: slug del sujeto (ej: "einstein")
        domain:       dominio HF (ej: "h10", "global")
        top3_cities:  lista de hasta 3 ciudades top (puede estar vacía)
        lang:         idioma ("es" | "en")
        platform:     plataforma destino (determina límite de caracteres)

    Returns:
        Texto generado por Claude (str)
    """
    nombre_real  = SUBJECT_NAMES.get(subject_slug, subject_slug.capitalize())
    dominio_label = DOMAIN_LABELS.get(domain, domain)
    limite       = SHOWCASE_LIMITS.get(platform, 280)

    ciudades_str = (
        ", ".join(top3_cities) if top3_cities
        else ("desconocidas en este momento" if lang == "es" else "not available")
    )

    if lang == "es":
        user_prompt = (
            f"Eres Lilly, astrólogo del sistema Abu Oracle. "
            f"Describe el mapa del Harmony Field (HF) de {nombre_real} "
            f"para el dominio '{dominio_label}' en máximo {limite} caracteres. "
            f"Menciona las 3 mejores ciudades: {ciudades_str}. "
            f"Cierra con una pregunta al lector sobre su propia carta. "
            f"Tono: directo, doctrinal, sin emojis excesivos. "
            f"Termina con: app.abu-oracle.com"
        )
    else:
        user_prompt = (
            f"You are Lilly, the astrologer of Abu Oracle. "
            f"Describe the Harmony Field (HF) map of {nombre_real} "
            f"for the domain '{dominio_label}' in at most {limite} characters. "
            f"Mention the 3 best cities: {ciudades_str}. "
            f"Close with a question to the reader about their own chart. "
            f"Tone: direct, doctrinal, no excessive emojis. "
            f"End with: app.abu-oracle.com"
        )

    api_key_sc = os.environ.get("ANTHROPIC_API_KEY")
    client_sc = (
        AnthropicVertex(
            project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", "abu-oracle"),
            region=os.environ.get("VERTEX_REGION", "us-east5"),
        )
        if not api_key_sc
        else anthropic.Anthropic(api_key=api_key_sc)
    )
    response = client_sc.messages.create(
        model=MODEL,
        max_tokens=512,
        system=_LILLY_PUBLICATION_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text.strip() if response.content else ""


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
