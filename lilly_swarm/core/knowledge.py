# -*- coding: utf-8 -*-
"""
Minimal semantic retrieval for Lilly classical corpus.
Loads data/embeddings.json and provides search_embeddings(query, top_k).
Fallbacks to mock embedding if no OpenAI key.
"""
import os
import json
import numpy as np
import hashlib
from pathlib import Path
from typing import List

EMBEDDINGS_PATH = Path(__file__).parent.parent / "data" / "embeddings.json"

# Load embeddings index
try:
    with open(EMBEDDINGS_PATH, encoding="utf-8") as f:
        _entries = json.load(f)
except Exception:
    _entries = []
    print(f"[WARN] Could not load embeddings from {EMBEDDINGS_PATH}")

# Helper: cosine similarity

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# Embedding backends

def embed_mock(text: str, dim: int = 256) -> List[float]:
    h = hashlib.sha256(text.encode("utf-8")).digest()
    raw = (h * ((dim // len(h)) + 1))[:dim]
    return [b / 255.0 for b in raw]

def embed_openai(text: str, model: str = "text-embedding-3-small") -> List[float]:
    try:
        import openai
    except Exception as e:
        raise RuntimeError("openai package not installed.") from e
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set.")
    openai.api_key = api_key
    resp = openai.Embedding.create(model=model, input=[text])
    return resp["data"][0]["embedding"]

# Main search

def search_embeddings(query: str, top_k: int = 3) -> List[str]:
    """Return top_k most relevant text fragments from the classical corpus."""
    if not _entries:
        print(f"[WARN] No embeddings loaded; returning empty references.")
        return []
    # Choose backend
    if os.getenv("OPENAI_API_KEY"):
        try:
            qvec = embed_openai(query)
        except Exception as e:
            print(f"[WARN] OpenAI embedding failed: {e}; using mock.")
            qvec = embed_mock(query)
    else:
        qvec = embed_mock(query)
    # Compute similarities
    scored = []
    for entry in _entries:
        vec = entry.get("embedding")
        if not vec:
            continue
        score = cosine_similarity(qvec, vec)
        scored.append((score, entry["text"]))
    scored.sort(reverse=True)
    results = [t for _, t in scored[:top_k]]
    print(f"[INFO] Found {len(results)} references for query '{query}'")
    return results
