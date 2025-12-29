# Multilingual Adaptive Prompts - Lilly Engine

## Overview

Lilly Engine now supports **4 languages** with adaptive tones that match cultural communication styles:

- **Spanish (es)** - Default, introspective and philosophical
- **English (en)** - Practical and analytical  
- **Portuguese (pt)** - Emotional and fluid
- **French (fr)** - Poetic and symbolic

## Language Detection

Language is automatically detected from:

1. **Profile language** (preferred) - Explicitly set by user
2. **Question text** (fallback) - Analyzed using `langdetect`
3. **Default to Spanish** - If detection fails

## Usage Examples

### Explicit Language Setting

```json
POST /api/ai/interpret
{
  "events": [{"cycle": "Saturn Return", "planet": "Saturn"}],
  "language": "en",
  "question": "What does this mean?"
}
```

### Automatic Detection from Question

```json
POST /api/ai/interpret
{
  "events": [{"cycle": "Saturn Return", "planet": "Saturn"}],
  "question": "Qu'est-ce que cela signifie pour moi?"
}
```

The system will detect French from the question and respond accordingly.

## Response Format

All responses include the detected language in metadata:

```json
{
  "headline": "...",
  "narrative": "...",
  "actions": ["...", "...", "..."],
  "astro_metadata": {
    "model": "gpt-4",
    "events_interpreted": 1,
    "language": "fr",
    "source": "openai"
  }
}
```

## Tone Adaptation

Each language uses a culturally appropriate tone:

| Language | Tone | Description |
|----------|------|-------------|
| Spanish | Introspective & Philosophical | Deep reflection, existential themes |
| English | Practical & Analytical | Clear action steps, logical structure |
| Portuguese | Emotional & Fluid | Heart-centered, flowing narrative |
| French | Poetic & Symbolic | Metaphorical, artistic expression |

## Testing

Run multilingual tests:

```bash
python lilly_engine/test_multilingual.py
```

This verifies:
- Language detection accuracy
- Prompt template correctness
- Fallback behavior
- Question-based detection

## Dependencies

- `langdetect>=1.0.9` - For automatic language detection
- `openai>=0.28.0,<1.0.0` - For GPT-4 interpretations

Install with:

```bash
pip install -r lilly_engine/requirements.txt
```

## Implementation Details

- **Prompt templates**: Defined in `lilly_engine/core/llm.py` (`PROMPT_TEMPLATES`)
- **Detection function**: `detect_language(text, fallback="es")`
- **Build function**: `build_prompt()` returns `(prompt, detected_lang)`
- **Memory storage**: Saves language with each context entry

## Fallback Behavior

1. If `langdetect` not installed → Spanish
2. If language not in `[es, en, pt, fr]` → Spanish
3. If detection fails → Spanish
4. If no question and no profile.language → Spanish

## Future Enhancements

- Add Italian (it), German (de)
- Custom tone overrides per user
- Language-specific archetype libraries
- Multi-language conversation memory mixing
