"""
Test script for context_manager.py
Verifies memory persistence, FIFO behavior, and topic extraction.
"""

import sys
from pathlib import Path

# Add lilly_engine to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lilly_engine.core.context_manager import (
    extract_topics,
    get_context,
    save_context,
    format_context_for_prompt,
    load_memory,
    save_memory,
)

def test_topic_extraction():
    """Test topic extraction from narrative text."""
    print("=== Testing Topic Extraction ===")
    
    text = """
    This period brings Saturn's discipline and Jupiter's expansion into focus.
    You're experiencing transformation and growth, with healing themes emerging.
    The Moon's intuition guides you toward spiritual clarity.
    """
    
    topics = extract_topics(text)
    print(f"Extracted topics: {topics}")
    assert "Saturn" in topics, "Should extract Saturn"
    assert "Jupiter" in topics, "Should extract Jupiter"
    assert "Moon" in topics, "Should extract Moon"
    assert "transformation" in topics, "Should extract transformation"
    assert "growth" in topics, "Should extract growth"
    print("✓ Topic extraction works correctly\n")


def test_save_and_load():
    """Test saving and loading context."""
    print("=== Testing Save and Load ===")
    
    # Save test entry
    test_user = "test_user_123"
    # Ensure clean slate for this user (isolation from prior test runs)
    mem = load_memory()
    if "conversations" in mem and test_user in mem["conversations"]:
        del mem["conversations"][test_user]
        save_memory(mem)
    test_data = {
        "language": "es",
        "chart": {"sun": "Leo", "moon": "Pisces", "asc": "Virgo"},
        "headline": "Tiempo de transformación Saturnina",
        "narrative": "Saturn's return brings discipline and responsibility. Growth awaits."
    }
    
    save_context(test_user, test_data)
    print(f"Saved context for {test_user}")
    
    # Load it back
    contexts = get_context(test_user, limit=2)
    print(f"Loaded {len(contexts)} context(s)")
    
    assert len(contexts) == 1, "Should have 1 entry"
    latest = contexts[0]
    assert latest["name"] == test_user
    assert latest["headline"] == test_data["headline"]
    assert "Saturn" in latest["topics"]
    print(f"Latest entry topics: {latest['topics']}")
    print("✓ Save and load works correctly\n")


def test_fifo_limit():
    """Test FIFO behavior (max 5 entries per user)."""
    print("=== Testing FIFO Limit ===")
    
    test_user = "fifo_test_user"
    
    # Add 7 entries
    for i in range(7):
        save_context(
            test_user,
            {
                "language": "es",
                "chart": {"sun": "Aries", "moon": "Taurus", "asc": "Gemini"},
                "headline": f"Entry {i + 1}",
                "narrative": f"This is entry number {i + 1} with Mars energy."
            }
        )
    
    # Should only keep last 5
    contexts = get_context(test_user, limit=10)
    print(f"After adding 7 entries, stored: {len(contexts)}")
    
    assert len(contexts) == 5, f"Should have max 5 entries, got {len(contexts)}"
    assert contexts[0]["headline"] == "Entry 3", "First should be Entry 3 (FIFO)"
    assert contexts[-1]["headline"] == "Entry 7", "Last should be Entry 7"
    print("✓ FIFO limit works correctly\n")


def test_context_formatting():
    """Test formatted context for prompt injection."""
    print("=== Testing Context Formatting ===")
    
    test_user = "format_test_user"
    
    # Add a couple entries
    for i in range(2):
        save_context(
            test_user,
            {
                "language": "es",
                "chart": {"sun": "Libra", "moon": "Scorpio", "asc": "Capricorn"},
                "headline": f"Headline {i + 1}",
                "narrative": f"Jupiter brings expansion and Venus adds harmony in entry {i + 1}."
            }
        )
    
    formatted = format_context_for_prompt(test_user, limit=2)
    print("Formatted context:")
    print(formatted)
    
    assert "Headline 1" in formatted
    assert "Headline 2" in formatted
    assert "Libra" in formatted
    assert "Jupiter" in formatted or "Venus" in formatted
    print("✓ Context formatting works correctly\n")


if __name__ == "__main__":
    print("Starting context_manager tests...\n")
    
    try:
        test_topic_extraction()
        test_save_and_load()
        test_fifo_limit()
        test_context_formatting()
        
        print("=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
