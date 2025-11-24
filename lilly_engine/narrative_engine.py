from typing import Dict, Any
import json
import os

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # Will be monkeypatched in tests or available in runtime


# Deterministic, sectioned prompt enforcing strict contract and style
SYSTEM_PROMPT = (
    "You are a Narrative Engine for Persian-medieval astrology.\n"
    "STRICT CONTRACT:\n"
    "- Read ONLY the provided JSON Maestro.\n"
    "- NEVER infer new calculations, positions, aspects, dignities, or timings.\n"
    "- NEVER contradict the Maestro.\n"
    "- Use ONLY concepts present in the Maestro; avoid non-Persian frameworks unless explicitly present.\n"
    "- Deterministic structure and section order. Return a single plain text block.\n"
    "LANGUAGE MODE: Use the language code provided (es|en|pt).\n"
    "STRUCTURE (fixed order, always include headers):\n"
    "1) Opening Overview – interpret year_element, tone, reference Ascendant RS and Sun RS.\n"
    "2) Elemental Dynamics – interpret elemental dominance and mention angular planets.\n"
    "3) Lord of the Year – nature, house influence, amplified topics.\n"
    "4) Timing Layer – profections (year + monthly), Fardars (major+sub), lunar mansion.\n"
    "5) Solar Return Overlay – RS themes and any RS–Natal interplay present.\n"
    "6) Critical Days and Transits – timing anchors with context (list what exists).\n"
    "7) Closing Summary – highlight core themes; avoid danger predictions or non-sourced advice.\n"
    "STYLE:\n"
    "- es: sobrio, elegante, neutro-cultural.\n"
    "- en: concise, classical-poetic.\n"
    "- pt: suave, fluido.\n"
)


def _language_tag(language: str) -> str:
    lang = (language or "es").lower()
    if lang not in {"es", "en", "pt"}:
        lang = "es"
    return lang


def generate_narrative(maestro: Dict[str, Any], language: str) -> str:
    """
    Produce a structured narrative strictly from JSON Maestro using OpenAI Chat Completions API.
    Returns a single text block string.
    """
    lang = _language_tag(language)

    maestro_json_string = json.dumps(maestro, ensure_ascii=False)

    # Assemble messages
    system_msg = SYSTEM_PROMPT + f"\nLANGUAGE: {lang}\n"
    user_msg = maestro_json_string


    def get_narrative_client():
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        return OpenAI(api_key=api_key)

    client = get_narrative_client()
    model = os.getenv("OPENAI_NARRATIVE_MODEL", "gpt-4o-mini")

    # Use standard Chat Completions API
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.7,
        max_tokens=2000,
    )

    # Extract text from response
    if resp.choices and len(resp.choices) > 0:
        text = resp.choices[0].message.content
        if isinstance(text, str) and text.strip():
            return text

    # As a last resort, return empty string to keep contract
    return ""
