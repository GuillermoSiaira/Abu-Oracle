import json
import types
import lilly_engine.narrative_engine as ne

class DummyMessage:
    def __init__(self, text):
        self.content = text

class DummyChoice:
    def __init__(self, text):
        self.message = DummyMessage(text)

class DummyResp:
    def __init__(self, text):
        self.choices = [DummyChoice(text)]

class DummyCompletions:
    @staticmethod
    def create(model=None, messages=None, temperature=None, max_tokens=None):
        # Assert prompt assembly basics
        assert isinstance(messages, list) and len(messages) == 2
        system = messages[0]
        user = messages[1]
        assert system["role"] == "system"
        assert user["role"] == "user"
        # Ensure Maestro JSON is passed as user content (stringified JSON)
        assert isinstance(user["content"], str)
        # Return a canned text
        return DummyResp("OK narrative")

class DummyChat:
    completions = DummyCompletions()

class DummyClient:
    chat = DummyChat()

class DummyOpenAI:
    def __call__(self):
        return DummyClient()


def test_generate_narrative_basic_monkeypatch(monkeypatch):
    # Monkeypatch OpenAI class used in module
    monkeypatch.setattr(ne, 'OpenAI', DummyOpenAI())

    maestro = {
        "metadata": {"mode": "persian_cosmology"},
        "year_overview": {"year_element": "water"}
    }
    out = ne.generate_narrative(maestro, language="es")
    assert isinstance(out, str)
    assert out.strip() != ""


def test_generate_narrative_language_switch(monkeypatch):
    captured = {}

    class CapturingCompletions:
        @staticmethod
        def create(model=None, messages=None, temperature=None, max_tokens=None):
            captured['messages'] = messages
            return DummyResp("OK narrative")

    class CapturingChat:
        completions = CapturingCompletions()

    class CapturingClient:
        chat = CapturingChat()

    class CapturingOpenAI:
        def __call__(self):
            return CapturingClient()

    monkeypatch.setattr(ne, 'OpenAI', CapturingOpenAI())

    maestro = {"metadata": {"mode": "persian_cosmology"}}

    ne.generate_narrative(maestro, language="es")
    sys_es = captured['messages'][0]['content']
    assert "LANGUAGE: es" in sys_es

    ne.generate_narrative(maestro, language="en")
    sys_en = captured['messages'][0]['content']
    assert "LANGUAGE: en" in sys_en
