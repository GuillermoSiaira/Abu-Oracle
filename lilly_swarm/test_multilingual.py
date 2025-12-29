"""
Test multilingual adaptive prompts in Lilly Engine.
Verifies language detection and tone adaptation.
"""

import sys
from pathlib import Path

# Add lilly_engine to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lilly_engine.core.llm import (
    Language,
    Profile,
    Chart,
    Event,
    build_prompt,
    detect_language
)

def test_language_detection():
    """Test language detection from text."""
    print("=== Testing Language Detection ===")
    
    tests = [
        ("¿Cómo influye Saturno en mi vida?", "es"),
        ("How does Saturn influence my life?", "en"),
        ("Como Saturno influencia minha vida?", "pt"),
        ("Comment Saturne influence-t-il ma vie?", "fr"),
        ("", "es"),  # Empty should fallback to Spanish
    ]
    
    for text, expected in tests:
        detected = detect_language(text)
        status = "✓" if detected == expected else "✗"
        print(f"{status} '{text[:40]}...' → {detected} (expected: {expected})")
    
    print()


def test_prompt_templates():
    """Test prompt generation in different languages."""
    print("=== Testing Multilingual Prompts ===")
    
    languages = ["es", "en", "pt", "fr"]
    
    for lang in languages:
        print(f"\n--- {lang.upper()} ---")
        
        profile = Profile(name="TestUser", language=lang)
        chart = Chart(sun="Leo", moon="Pisces", asc="Virgo")
        events = [Event(type="Saturn Return", planet="Saturn", to="Natal Saturn", angle=0)]
        
        prompt, detected_lang = build_prompt(
            profile=profile,
            chart=chart,
            events=events,
            question="What does this mean for me?"
        )
        
        # Check key phrases
        key_phrases = {
            "es": ["Lilly", "inteligencia astrológica", "introspectivo", "filosófico"],
            "en": ["Lilly", "astrological intelligence", "practical", "analytical"],
            "pt": ["Lilly", "inteligência astrológica", "emocional", "fluido"],
            "fr": ["Lilly", "intelligence astrologique", "poétique", "symbolique"]
        }
        
        found_phrases = [p for p in key_phrases[lang] if p.lower() in prompt.lower()]
        
        print(f"Detected language: {detected_lang}")
        print(f"Key phrases found: {len(found_phrases)}/{len(key_phrases[lang])}")
        print(f"Sample: {prompt[:200]}...")
        
        if detected_lang == lang and len(found_phrases) >= 2:
            print("✓ Prompt correctly generated")
        else:
            print("✗ Issue with prompt generation")
    
    print()


def test_language_fallback():
    """Test fallback to Spanish when language not specified."""
    print("=== Testing Language Fallback ===")
    
    profile = Profile(name="TestUser")  # No language specified
    chart = Chart(sun="Aries")
    events = [Event(type="Jupiter Transit", planet="Jupiter", to="Sun")]
    
    prompt, detected_lang = build_prompt(
        profile=profile,
        chart=chart,
        events=events
    )
    
    if detected_lang == "es" and "Lilly" in prompt and "inteligencia astrológica" in prompt:
        print("✓ Correctly falls back to Spanish")
    else:
        print(f"✗ Fallback failed, detected: {detected_lang}")
    
    print()


def test_question_based_detection():
    """Test language detection from question text."""
    print("=== Testing Question-Based Language Detection ===")
    
    test_cases = [
        ("What is my future?", "en"),
        ("¿Cuál es mi futuro?", "es"),
        ("Qual é o meu futuro?", "pt"),
        ("Quel est mon avenir?", "fr"),
    ]
    
    for question, expected_lang in test_cases:
        profile = Profile(name="TestUser")  # No language in profile
        chart = Chart(sun="Gemini")
        events = [Event(type="Transit", planet="Mars", to="Moon")]
        
        prompt, detected_lang = build_prompt(
            profile=profile,
            chart=chart,
            events=events,
            question=question
        )
        
        status = "✓" if detected_lang == expected_lang else "✗"
        print(f"{status} Question: '{question}' → {detected_lang} (expected: {expected_lang})")
    
    print()


if __name__ == "__main__":
    print("Starting multilingual adaptive prompts tests...\n")
    
    try:
        test_language_detection()
        test_prompt_templates()
        test_language_fallback()
        test_question_based_detection()
        
        print("=" * 60)
        print("✓ All multilingual tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
