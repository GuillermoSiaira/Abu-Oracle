import logging
import os
import json
from importlib import reload


def test_analyze_logs_blocks(monkeypatch, capsys):
    """Test that /analyze logs a structured 'analyze.blocks' event with timing metrics in verbose mode.
    
    Uses capsys instead of caplog since TestClient runs ASGI in a separate thread where caplog
    cannot capture logs. We parse the JSON lines from stderr instead.
    """
    # Force verbose mode BEFORE any module imports
    monkeypatch.setenv("ABU_VERBOSE", "1")

    # Clear any previously imported abu_engine modules to ensure fresh reload
    import sys
    to_remove = [k for k in sys.modules if k.startswith("abu_engine")]
    for k in to_remove:
        del sys.modules[k]

    # Now import fresh with ABU_VERBOSE=1 in environment
    from fastapi.testclient import TestClient
    import abu_engine.main as main_mod
    app = main_mod.app

    client = TestClient(app)
    payload = {
        "person": {"name": "", "question": ""},
        "birth": {"date": "1990-01-01T12:00:00Z", "lat": -34.6, "lon": -58.4},
        "current": {"lat": -34.6, "lon": -58.4}
    }

    resp = client.post("/analyze", json=payload)
    assert resp.status_code == 200

    # Capture output from TestClient background thread
    captured = capsys.readouterr()
    # TestClient logs go to stderr
    output = captured.err

    # Parse JSON lines to find analyze.blocks event
    import json
    found_event = False
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            log_entry = json.loads(line)
            if log_entry.get("event") == "analyze.blocks":
                meta = log_entry.get("meta", {})
                assert "dur_ms" in meta, f"Expected dur_ms in meta, got: {meta}"
                assert "solar_return_ms" in meta, f"Expected solar_return_ms in new integration"
                found_event = True
                break
        except json.JSONDecodeError:
            continue

    assert found_event, f"Expected analyze.blocks event in logs. Output:\n{output}"