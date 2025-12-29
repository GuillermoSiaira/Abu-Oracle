"""
Context manager for Lilly's semantic memory.
Handles storage and retrieval of conversation history with topic extraction.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import List, Dict, Any, Optional

# Thread lock for safe concurrent access to memory file
_memory_lock = Lock()

# Planetary and astrological keywords for topic extraction
PLANETARY_KEYWORDS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", 
    "Uranus", "Neptune", "Pluto", "Chiron", "Node", "Ascendant", "Midheaven"
]

ARCHETYPE_KEYWORDS = [
    # English
    "growth", "transformation", "discipline", "freedom", "intuition",
    "power", "healing", "responsibility", "change", "rebirth", "clarity",
    "expansion", "restriction", "innovation", "spirituality", "identity",
    # Spanish
    "crecimiento", "transformación", "disciplina", "libertad", "intuición",
    "poder", "sanación", "responsabilidad", "cambio", "renacimiento", "claridad",
    "expansión", "restricción", "innovación", "espiritualidad", "identidad"
]


def get_memory_path() -> Path:
    """Return the absolute path to the semantic memory file (memory.json)."""
    return Path(__file__).parent.parent / "data" / "memory.json"


def extract_topics(text: str) -> List[str]:
    """Extract relevant themes from text via simple keyword regex.

    Uses a small curated set of planetary and archetypal keywords to detect
    recurring themes. Case-insensitive and de-duplicated.

    Args:
        text: Narrative/headline text.

    Returns:
        Sorted list of unique topic strings found in the text.
    """
    topics = set()
    text_lower = text.lower()
    
    # Extract planetary keywords (case-insensitive)
    for planet in PLANETARY_KEYWORDS:
        pattern = rf'\b{re.escape(planet)}\b'
        if re.search(pattern, text, re.IGNORECASE):
            topics.add(planet)
    
    # Extract archetype keywords
    for archetype in ARCHETYPE_KEYWORDS:
        pattern = rf'\b{re.escape(archetype)}\b'
        if re.search(pattern, text_lower):
            topics.add(archetype)
    
    return sorted(list(topics))


def load_memory() -> Dict[str, List[Dict[str, Any]]]:
    """Load the entire semantic memory from disk (creating the file if absent).

    Returns:
        A dictionary with the shape { "conversations": { <user>: [entries...] } }
    """
    memory_path = get_memory_path()
    
    # Ensure directory exists
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    
    with _memory_lock:
        if not memory_path.exists():
            # Create empty memory file
            initial_data = {"conversations": {}}
            with open(memory_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
            return initial_data
        
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure conversations key exists
                if "conversations" not in data:
                    data["conversations"] = {}
                return data
        except (json.JSONDecodeError, IOError):
            # Return empty structure on error
            return {"conversations": {}}


def save_memory(data: Dict[str, Any]) -> None:
    """Persist the entire memory structure to disk (thread-safe).

    Gracefully ignores IO errors to avoid crashing the service.

    Args:
        data: Complete memory dictionary to save.
    """
    memory_path = get_memory_path()
    
    with _memory_lock:
        try:
            with open(memory_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            # Silently ignore write errors; callers should proceed without blocking
            pass


def get_context(user: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Load the last N entries for a given user (default: 3).

    Args:
        user: User identifier (profile.name or "anonymous").
        limit: Max number of entries to return.

    Returns:
        A list of memory entries (most recent last).
    """
    memory = load_memory()
    user_history = memory.get("conversations", {}).get(user, [])
    return user_history[-limit:] if user_history else []


def save_context(user: str, entry: Dict[str, Any], max_entries: int = 5) -> None:
    """Append a new interpretation entry to memory and cap at 5 per user.

    This function is thread-safe and resilient to disk errors.

    Args:
        user: User identifier (profile.name or "anonymous").
        entry: Interpretation result or payload. Expected keys:
            - language: str
            - headline: str
            - narrative: str (used for topic extraction)
            - chart_summary: dict with { sun, moon, asc } (optional)
        max_entries: Maximum entries to keep per user (FIFO), default 5.
    """
    memory = load_memory()

    # Extract topics from narrative/headline
    text_to_analyze = f"{entry.get('headline', '')} {entry.get('narrative', '')}"
    topics = extract_topics(text_to_analyze)

    # Normalize chart summary field
    chart = entry.get("chart_summary") or entry.get("chart") or {}
    chart_summary = {
        "sun": chart.get("sun") if isinstance(chart, dict) else getattr(chart, "sun", None),
        "moon": chart.get("moon") if isinstance(chart, dict) else getattr(chart, "moon", None),
        "asc": chart.get("asc") if isinstance(chart, dict) else getattr(chart, "asc", None),
    }

    # Build stored entry (include both 'user' and 'name' for backward-compat)
    stored = {
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "name": user,  # backward compatibility for existing readers/tests
        "language": entry.get("language", "es"),
        "headline": entry.get("headline", ""),
        "topics": topics,
        "chart_summary": chart_summary,
    }

    # Get or create user's conversation list
    conversations = memory.setdefault("conversations", {})
    user_history = conversations.get(user, [])

    # Add new entry and enforce FIFO
    user_history.append(stored)
    if len(user_history) > max_entries:
        user_history = user_history[-max_entries:]

    conversations[user] = user_history
    memory["conversations"] = conversations

    save_memory(memory)


def format_context_for_prompt(user: str, limit: int = 2) -> str:
    """
    Formats previous context as a string ready for prompt injection.
    
    Args:
        user: User identifier
        limit: Number of previous entries to include
        
    Returns:
        Formatted string with previous conversation context
    """
    entries = get_context(user, limit)
    
    if not entries:
        return "- No hay conversaciones previas"
    
    formatted = []
    for entry in entries:
        chart = entry.get("chart_summary", {})
        topics_str = ", ".join(entry.get("topics", [])[:5])  # Show top 5 topics
        
        formatted.append(
            f"- {entry['timestamp'][:10]}: {entry['headline']}\n"
            f"  Sol: {chart.get('sun', 'N/A')}, Luna: {chart.get('moon', 'N/A')}, Asc: {chart.get('asc', 'N/A')}\n"
            f"  Temas: {topics_str or 'general'}"
        )
    
    return "\n".join(formatted)
