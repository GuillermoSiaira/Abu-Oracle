"""
LLM module for generating astrological interpretations using OpenAI's GPT models.
Supports personalized chart interpretation with transits, events, and focused questions.
Refactored for Persian/Medieval Deterministic Astrology (Abu Oracle v3.0).
"""

import os
import json
import time
import logging
import httpx
from dataclasses import dataclass, asdict
from enum import Enum
from openai import OpenAI
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path

# Import context manager for semantic memory
from .context_manager import (
    get_context,
    save_context,
    format_context_for_prompt
)

# Import knowledge search for semantic axiom matching
from .knowledge import search_embeddings

# Helper to load axioms from Markdown
def load_axioms(path=None, limit=8) -> str:
    use_axioms = os.getenv("LILLY_USE_AXIOMS", "true").lower() != "false"
    if not use_axioms:
        return ""
    if path is None:
        # Use absolute path relative to this file's parent directory
        path = Path(__file__).parent.parent / "data" / "axioms" / "astrological_axioms.md"
    try:
        lines = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                lines.append(line)
                if len(lines) >= limit:
                    break
        result = "\n".join(lines)
        print(f"[INFO] Injected {len(lines)} axioms into prompt")
        return result
    except Exception as e:
        print(f"[WARN] Could not load axioms: {e}")
        return ""


# Lazy OpenAI client initialization
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(
        api_key=api_key,
        timeout=httpx.Timeout(60.0, connect=10.0),
        max_retries=2
    )

def validate_contract(output: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validate the JSON contract expected by frontend and callers.

    Returns (is_valid, errors).
    """
    required_top = ["headline", "narrative", "actions", "astro_metadata"]
    errors: List[str] = []
    for k in required_top:
        if k not in output:
            errors.append(f"missing key: {k}")
    if "actions" in output and not isinstance(output["actions"], list):
        errors.append("actions must be a list")
    if "astro_metadata" in output and not isinstance(output["astro_metadata"], dict):
        errors.append("astro_metadata must be an object")
    # Validate astro_metadata minimum fields if present
    meta = output.get("astro_metadata", {}) if isinstance(output.get("astro_metadata"), dict) else {}
    for mk in ("model", "language"):
        if mk not in meta:
            errors.append(f"astro_metadata missing: {mk}")
    return (len(errors) == 0, errors)

class Language(str, Enum):
    """Supported languages for interpretations."""
    ES = "es"  # Spanish
    EN = "en"  # English
    PT = "pt"  # Portuguese
    FR = "fr"  # French

def detect_language(text: str, fallback: str = "es") -> str:
    """
    Detects language from text using langdetect.
    Falls back to specified language if detection fails.
    
    Args:
        text: Text to analyze
        fallback: Fallback language code (default: 'es')
        
    Returns:
        Language code (es, en, pt, fr)
    """
    if not text or not text.strip():
        return fallback
    
    try:
        from langdetect import detect
        detected = detect(text)
        # Map to supported languages
        if detected in ['es', 'en', 'pt', 'fr']:
            return detected
        return fallback
    except ImportError:
        # langdetect not installed, return fallback
        return fallback
    except Exception:
        # Detection failed
        return fallback

@dataclass
class Profile:
    name: str = "Usuario"
    language: Optional[str] = None  # User's preferred language

@dataclass
class Chart:
    sun: Optional[str] = None
    moon: Optional[str] = None
    asc: Optional[str] = None

@dataclass
class Transit:
    planet: str
    aspect: str
    target: str

@dataclass
class Event:
    type: str
    planet: str
    to: str
    angle: Optional[float] = None
    peak: Optional[str] = None

# Multilingual prompt templates with DETERMINISTIC tones (Updated for v3.0)
PROMPT_TEMPLATES = {
    "es": {
        "intro": "Eres Lilly, la encarnación digital de la tradición astrológica Persa y Medieval (basada en Abu Ma'shar y Al-Biruni). Tu voz es técnica, sobria y determinista. NO eres una terapeuta ni una coach de vida; eres un Oráculo matemático.",
        "instruction": "Genera una interpretación para {name}. Prioriza eventos concretos (enemigos, ascensos, exilios, salud) sobre estados emocionales. Si ves Maléficos (Saturno/Marte) en casas difíciles (6, 8, 12), NO suavices el juicio; describe la restricción o el conflicto real.",
        "format": """Responde en formato JSON con las claves:
- "abu_line": dato técnico crudo (ej: 'Saturno en Casa 12, Peregrino')
- "lilly_line": sentencia del oráculo (ej: 'Enemigos ocultos limitan la libertad')
- "headline": título directo y predictivo
- "narrative": análisis de 4 párrafos. Párrafo 1: Estado del Regente del Ascendente. Párrafo 2: Planetas en Casas Angulares (Acción). Párrafo 3: Planetas en Casas Cadentes/Maléficas (Entropía/Enemigos). Párrafo 4: Síntesis del destino.
- "actions": 3 advertencias o estrategias concretas para mitigar o potenciar la configuración""",
        "data_section": "Datos del Motor de Cálculo (VERDAD ABSOLUTA):",
        "sun": "Sol",
        "moon": "Luna",
        "asc": "Ascendente",
        "transits": "Tránsitos",
        "events": "Eventos",
        "question": "Consulta del Querente",
        "tone": "Nivel de fatalidad solicitado",
        "context": "Memoria de la sesión",
        "none": "ninguno",
        "general": "juicio general"
    },
    "en": {
        "intro": "You are Lilly, operating under Persian/Medieval axioms. Your voice is technical, deterministic, and precise. You represent fate, not psychology.",
        "instruction": "Interpret for {name}. Focus on concrete events. Do NOT sugarcoat Malefics in bad houses (6, 8, 12). Identify the Lord of the Geniture.",
        "format": """Respond in JSON format with these keys:
- "abu_line": technical data point
- "lilly_line": oracular synthesis
- "headline": predictive title
- "narrative": 4 paragraphs analyzing the Lord of Ascendant, Angular planets, and Malefics in bad houses. Be direct.
- "actions": 3 concrete strategies""",
        "data_section": "Calculation Engine Data (ABSOLUTE TRUTH):",
        "sun": "Sun",
        "moon": "Moon",
        "asc": "Ascendant",
        "transits": "Transits",
        "events": "Events",
        "question": "Querent's focus",
        "tone": "Requested rigor",
        "context": "Session memory",
        "none": "none",
        "general": "general judgment"
    },
    "pt": {
        "intro": "Você é Lilly, uma inteligência astrológica operando sob axiomas Persas/Medievais. Sua voz é técnica, determinista e precisa.",
        "instruction": "Gere uma interpretação para {name}. Priorize eventos concretos. Não suavize Maléficos em casas difíceis (6, 8, 12).",
        "format": """Responda em formato JSON com as chaves:
- "abu_line": frase técnica e breve
- "lilly_line": frase oracular
- "headline": título preditivo
- "narrative": texto de 4 parágrafos focando em Regente do Ascendente, Angulares e Maléficos.
- "actions": lista de 3 recomendações práticas""",
        "data_section": "Dados astrológicos:",
        "sun": "Sol",
        "moon": "Lua",
        "asc": "Ascendente",
        "transits": "Trânsitos",
        "events": "Eventos",
        "question": "Pergunta ou foco do usuário",
        "tone": "Tom solicitado",
        "context": "Contexto de conversas anteriores",
        "none": "nenhum",
        "general": "geral"
    },
    "fr": {
        "intro": "Vous êtes Lilly, une intelligence astrologique opérant sous des axiomes Perses/Médiévaux. Votre voix est technique, déterministe et précise.",
        "instruction": "Générez une interprétation pour {name}. Priorisez les événements concrets. Ne pas adoucir les Maléfiques dans les maisons difficiles (6, 8, 12).",
        "format": """Répondez en format JSON avec ces clés:
- "abu_line": ligne technique
- "lilly_line": ligne oraculaire
- "headline": titre prédictif
- "narrative": texte de 4 paragraphes analysant le Maître de l'Ascendant, les planètes Angulaires et les Maléfiques.
- "actions": liste de 3 recommandations pratiques""",
        "data_section": "Données astrologiques:",
        "sun": "Soleil",
        "moon": "Lune",
        "asc": "Ascendant",
        "transits": "Transits",
        "events": "Événements",
        "question": "Question ou focus de l'utilisateur",
        "tone": "Ton demandé",
        "context": "Contexte des conversations précédentes",
        "none": "aucun",
        "general": "général"
    }
}

def build_prompt(
    profile: Union[Profile, Dict[str, Any]],
    chart: Optional[Union[Chart, Dict[str, Any]]] = None,
    transits: Optional[List[Union[Transit, Dict[str, Any]]]] = None,
    events: Optional[List[Union[Event, Dict[str, Any]]]] = None,
    question: Optional[str] = None,
    tone: str = "determinista",
    include_reasoning: bool = True
) -> tuple[str, str]:
    """
    Builds a rich multilingual astrological interpretation prompt.
    Adapts tone based on detected/specified language.
    Includes SYSTEM OVERRIDE for data fidelity.
    """
    # Convert dict inputs to dataclasses if needed
    if isinstance(profile, dict):
        profile = Profile(**profile)
    if isinstance(chart, dict):
        chart = Chart(**chart)
    if transits:
        transits = [
            t if isinstance(t, Transit) else Transit(**t)
            for t in transits
        ]
    if events:
        events = [
            e if isinstance(e, Event) else Event(**e)
            for e in events
        ]

    # Detect language: prefer profile.language, fallback to question detection
    lang_code = "es"  # default
    if profile.language:
        lang_code = profile.language if profile.language in PROMPT_TEMPLATES else "es"
    elif question:
        lang_code = detect_language(question, fallback="es")
    
    # Get template for detected language
    template = PROMPT_TEMPLATES.get(lang_code, PROMPT_TEMPLATES["es"])

    # Extract chart placements
    sun = getattr(chart, "sun", None) if chart else None
    moon = getattr(chart, "moon", None) if chart else None
    asc = getattr(chart, "asc", None) if chart else None

    # Format transit and event strings if present
    transit_text = ', '.join([
        f"{t.planet} {t.aspect} {t.target}"
        for t in (transits or [])
    ]) or template["none"]

    event_text = ', '.join([
        f"{e.type} de {e.planet} hacia {e.to}"
        for e in (events or [])
    ]) or template["none"]

    # Load axioms section
    axioms_section = load_axioms()

    # Build classical references section using semantic search
    query_parts = []
    if transits:
        for t in transits:
            query_parts.append(f"{t.planet} {t.aspect} {t.target}")
    if question:
        query_parts.append(str(question))
    query = " ".join(query_parts).strip() or "astrology"
    refs = search_embeddings(query, top_k=3)
    refs_section = "\n".join(refs)

    # Build the complete prompt using template with SYSTEM OVERRIDE
    prompt = f"""### SYSTEM OVERRIDE: AXIOMATIC MODE
WARNING: You are prone to hallucinating empty houses. 
RULE 1: Scan the "{template['data_section']}" below explicitly.
RULE 2: If the list says "Saturn: House 12", you MUST interpret Saturn in the 12th House. Ignoring this is a critical error.
RULE 3: Do not use modern psychological terms (subconscious, inner child). Use concrete terms (enemies, imprisonment, illness, debts).

{template["intro"]}

{template["instruction"].format(name=profile.name)}

{template["format"]}

Reasoning Axioms:
{axioms_section}

Classical References (William Lilly / Abu Ma'shar):
{refs_section}

{template["data_section"]}
- {template["sun"]}: {sun or template["none"]}
- {template["moon"]}: {moon or template["none"]}
- {template["asc"]}: {asc or template["none"]}
- {template["transits"]}: {transit_text}
- {template["events"]}: {event_text}

{template["question"]}: {question or template["general"]}

{template["tone"]}: {tone}

{template["context"]}:
{format_context_for_prompt(profile.name, limit=2)}

Reglas de estilo:
- Usa lenguaje natural y preciso, sin exageraciones.
- Evita listas en la narrativa; reserva bullets solo para "actions".
- Integra el contexto cuando sea pertinente, sin repetirlo.
"""

    # Add reasoning instruction if enabled
    if include_reasoning:
        prompt += """
Tarea de razonamiento:
1. Antes de escribir tu interpretación final, razona paso a paso usando los axiomas y referencias proporcionados.
2. Explica cómo cada principio clave se aplica a la carta y pregunta actual.
3. Incluye este razonamiento interno como un párrafo breve bajo la clave "reasoning" en la salida JSON.
4. Luego proporciona "headline", "narrative" y "actions".

Responde con JSON válido que incluya: abu_line, lilly_line, reasoning, headline, narrative, actions. No agregues comentarios fuera del JSON.
"""
    else:
        prompt += """
Responde solo con JSON válido. No agregues comentarios fuera del JSON.
"""
    return prompt, lang_code

def generate_interpretation(
    events: List[Dict[str, Any]], 
    lang: Language = Language.ES,
    user_name: str = "Usuario",
    chart_data: Optional[Dict[str, str]] = None,
    question: Optional[str] = None,
    tone: str = "determinista",
    include_reasoning: bool = None
) -> Dict[str, Any]:
    """
    Generates a multilingual interpretation of astrological events using GPT-4.
    Automatically detects language and adapts tone. Saves context to memory.
    """
    if not events:
        raise ValueError("No events provided for interpretation")


    # Lazy client initialization
    try:
        client = get_openai_client()
    except Exception as e:
        raise ValueError(f"OpenAI API key not configured: {str(e)}")

    try:
        # Build profile and chart for prompt
        profile = Profile(name=user_name, language=lang.value if lang else None)
        chart = Chart(**(chart_data or {})) if chart_data else None
        
        # Convert events to Event objects
        event_objs = [Event(**e) if isinstance(e, dict) else e for e in events]
        
        # Check env var for reasoning flag if not explicitly set
        if include_reasoning is None:
            include_reasoning = os.getenv("LILLY_INCLUDE_REASONING", "true").lower() != "false"
        
        # Build prompt with context and get detected language
        prompt_text, detected_lang = build_prompt(
            profile=profile,
            chart=chart,
            events=event_objs,
            question=question,
            tone=tone or "determinista",
            include_reasoning=include_reasoning
        )
        
        # Build system message based on detected language (STRICT MODE)
        system_messages = {
            "es": "Eres Lilly, un motor astrológico determinista basado en axiomas persas. No suavices los aspectos difíciles. Responde JSON válido.",
            "en": "You are Lilly, a deterministic astrological engine based on Persian axioms. Do not sugarcoat hard aspects. Respond valid JSON.",
            "pt": "Você é Lilly, um motor astrológico determinista. Responda em JSON válido.",
            "fr": "Vous êtes Lilly, un moteur astrologique déterministe. Répondez en JSON valide."
        }
        system_msg = system_messages.get(detected_lang, system_messages["es"])
        
        # Get model from environment or use default
        model_name = os.getenv('LILLY_MODEL', 'gpt-4o-mini')
        
        start_ts = time.time()
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7,
            max_tokens=900,
            response_format={"type": "json_object"}
        )

        # Extract content
        content = response.choices[0].message.content

        # Try to parse as JSON first, handling code-fenced blocks
        def _parse_json_from_content(text: str) -> Optional[Dict[str, Any]]:
            try:
                return json.loads(text)
            except Exception:
                pass
            # Strip markdown code fences if present
            stripped = text.strip()
            if stripped.startswith('```'):
                # Remove ```json or ``` and trailing ```
                stripped = stripped.strip('`')
                # Fallback: extract the first JSON object by braces
            # Extract a JSON object by finding outermost braces
            try:
                import re
                m = re.search(r'\{[\s\S]*\}', text)
                if m:
                    return json.loads(m.group(0))
            except Exception:
                return None
            return None

        parsed = _parse_json_from_content(content)
        if parsed is not None:
            headline = parsed.get("headline", "")
            narrative = parsed.get("narrative", "")
            actions = parsed.get("actions", [])
            reasoning = parsed.get("reasoning", "No explicit reasoning provided.")
            abu_line = parsed.get("abu_line", "")
            lilly_line = parsed.get("lilly_line", "")
        else:
            # Fallback to text parsing
            sections = content.split('\n\n')
            headline = sections[0].strip()
            narrative = sections[1].strip() if len(sections) > 1 else ""
            actions = []
            for line in sections[-1].split('\n'):
                if line.strip().startswith('-'):
                    actions.append(line.strip()[2:])
            reasoning = "No explicit reasoning provided."
            abu_line = ""
            lilly_line = ""
        
        # Log reasoning if present
        if reasoning and reasoning != "No explicit reasoning provided.":
            print(f"[INFO] Lilly produced reasoning: {reasoning[:80]}...")
        
        # Normalize and enrich output
        def _normalize_actions(items: Any) -> List[str]:
            out: List[str] = []
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, str):
                        s = it.strip()
                        # Remove generic prefixes occasionally produced by LLMs
                        for pref in ("Reflect on:", "Reflexiona sobre:", "Refletir sobre:", "Réfléchis à :"):
                            if s.lower().startswith(pref.lower()):
                                s = s[len(pref):].strip()
                        if s:
                            out.append(s)
            return out[:6]

        actions = _normalize_actions(actions)
        headline = (headline or "").strip()
        narrative = (narrative or "").strip()
        abu_line = (abu_line or "").strip()
        lilly_line = (lilly_line or "").strip()

        # Enrich astro metadata with usage and runtime
        runtime_ms = int((time.time() - start_ts) * 1000)
        usage = getattr(response, "usage", None)
        usage_dict = {}
        if usage:
            try:
                usage_dict = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", None),
                    "completion_tokens": getattr(usage, "completion_tokens", None),
                    "total_tokens": getattr(usage, "total_tokens", None),
                }
            except Exception:
                usage_dict = {}

        # Save to context memory with detected language
        save_context(
            user=user_name or "anonymous",
            entry={
                "language": detected_lang,
                "chart_summary": chart_data or {},
                "headline": headline,
                "narrative": narrative
            }
        )
                
        return {
            "abu_line": abu_line,
            "lilly_line": lilly_line,
            "headline": headline,
            "narrative": narrative,
            "actions": actions,
            "reasoning": reasoning,
            "astro_metadata": {
                "model": model_name,
                "events_interpreted": len(events),
                "language": detected_lang,  # Include detected language in metadata
                "source": "openai",
                "runtime_ms": runtime_ms,
                **({"usage": usage_dict} if usage_dict else {})
            }
        }

    except Exception as e:
        # Surface as runtime error for upstream fallback (caller will fallback)
        raise RuntimeError(f"OpenAI API error: {str(e)}")