"""Structured logging utilities for Abu Engine.

Activación modo verbose:
  Setear ABU_VERBOSE=1 para emitir líneas JSON con estructura:
    {"ts": ISO8601, "level": "INFO", "event": "...", "meta": {...}}

Por defecto (ABU_VERBOSE distinto de 1) se usa formato compacto de texto.
Evita duplicar handlers si uvicorn ya configuró logging.
"""
from __future__ import annotations

import logging
import sys
import os
import json
from datetime import datetime, timezone
from typing import Any, Dict

VERBOSE = os.getenv("ABU_VERBOSE", "0") == "1"

class JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: Dict[str, Any] = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "event": getattr(record, "event", record.getMessage().split(" ")[0] if record.getMessage() else "log"),
            "meta": {}
        }
        # If extra meta dict provided
        meta = getattr(record, "meta", None)
        if isinstance(meta, dict):
            payload["meta"] = meta
        else:
            # Fallback: include full message under msg
            payload["meta"] = {"msg": record.getMessage()}
        return json.dumps(payload, ensure_ascii=False)


def init_logging(verbose: bool | None = None) -> None:
    """Initialize logging configuration.

    verbose: override env flag for tests.
    """
    # Always re-read env var to catch changes from tests
    if verbose is None:
        verbose = os.getenv("ABU_VERBOSE", "0") == "1"

    root = logging.getLogger()
    # Avoid duplicating handlers if already configured
    # If already initialized with the same mode, no-op; otherwise reconfigure
    if getattr(root, "_abu_logging_initialized", False):  # type: ignore[attr-defined]
        current_mode = getattr(root, "_abu_logging_verbose_mode", None)  # type: ignore[attr-defined]
        if current_mode == verbose:
            return
        # Reconfigure: remove existing handlers to apply new formatter/mode
        for h in list(root.handlers):
            root.removeHandler(h)

    # Remove default handlers added by uvicorn/basicConfig to control formatting
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler()
    if verbose:
        handler.setFormatter(JsonLineFormatter())
        root.setLevel(logging.INFO)
    else:
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        root.setLevel(logging.INFO)

    root.addHandler(handler)
    # Flags to avoid unnecessary re-init and track mode
    root._abu_logging_initialized = True  # type: ignore[attr-defined]
    root._abu_logging_verbose_mode = verbose  # type: ignore[attr-defined]


def log_event(event: str, meta: Dict[str, Any], level: int = logging.INFO) -> None:
    """Helper to emit structured event log respecting verbose mode.

    Ensures JSON line output includes explicit JSON even in fallback mode so tests expecting
    '"event": "..."' can still match when ABU_VERBOSE=1. When verbose is disabled, we now
    serialize a compact JSON object for consistency rather than the prior free-form string.
    """
    # Use root logger to ensure pytest's caplog can capture it
    logger = logging.getLogger()
    # Re-read env var to catch changes from tests
    verbose = os.getenv("ABU_VERBOSE", "0") == "1"
    if verbose:
        # In verbose mode, log via the logger with extra fields so JsonLineFormatter can format it
        # This ensures caplog (pytest logging capture) gets the JSON output
        logger.log(level, event, extra={"event": event, "meta": meta})
    else:
        # Emit compact JSON (non-verbose) to keep parsing simple for downstream tooling
        try:
            line = json.dumps({"event": event, "meta": meta}, ensure_ascii=False)
        except Exception:
            line = f"{event} {meta}"
        logger.log(level, line)
