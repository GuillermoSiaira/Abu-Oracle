# -*- coding: utf-8 -*-
"""
Generate embeddings index for Lilly classical corpus.

Usage (PowerShell):
  python lilly_engine/scripts/generate_embeddings.py \
    --corpus lilly_engine/data/lilly_corpus \
    --output lilly_engine/data/embeddings.json \
    --backend auto

Backends:
- auto: use OpenAI if OPENAI_API_KEY available, else mock embeddings
- openai: force OpenAI (will error if no key)
- mock: deterministic hash-based vectors (dev only, no semantic meaning)

The resulting JSON has a list of entries:
  [{ id, text, source, section, embedding: [float,...] }]

Note: For OpenAI, set OPENAI_API_KEY in your environment.
"""

from __future__ import annotations
import os
import json
import argparse
import pathlib
import re
import hashlib
from typing import Iterable, List, Dict, Any

# ------------- Text loading & chunking -------------

def iter_text_files(root: pathlib.Path) -> Iterable[pathlib.Path]:
    for p in root.rglob("*.txt"):
        if p.is_file():
            yield p

def clean_text(s: str) -> str:
    # Basic normalization; extend as needed
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def chunk_text(text: str, max_chars: int = 1400) -> List[str]:
    # Simple greedy chunking by paragraphs/sentences
    text = text.strip()
    if not text:
        return []
    chunks: List[str] = []
    buf = []
    current = 0
    for sent in re.split(r"(?<=[\.!?])\s+", text):
        if current + len(sent) + 1 > max_chars and buf:
            chunks.append(" ".join(buf))
            buf = [sent]
            current = len(sent) + 1
        else:
            buf.append(sent)
            current += len(sent) + 1
    if buf:
        chunks.append(" ".join(buf))
    return [c.strip() for c in chunks if c.strip()]

# ------------- Embedding backends -------------

def embed_mock(texts: List[str], dim: int = 256) -> List[List[float]]:
    vecs: List[List[float]] = []
    for t in texts:
        h = hashlib.sha256(t.encode("utf-8")).digest()
        # Repeat hash to fill dim
        raw = (h * ((dim // len(h)) + 1))[:dim]
        # Normalize to [0,1]
        vec = [b / 255.0 for b in raw]
        vecs.append(vec)
    return vecs

def embed_openai(texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
    try:
        import openai
    except Exception as e:
        raise RuntimeError("openai package not installed. Add it to requirements or use --backend mock.") from e

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    openai.api_key = api_key

    # Batch call (naive). For large corpora, implement paging & retry.
    resp = openai.Embedding.create(model=model, input=texts)
    data = resp.get("data", [])
    if len(data) != len(texts):
        raise RuntimeError("Embedding count mismatch")
    return [row["embedding"] for row in data]

# ------------- Main pipeline -------------

def build_index(corpus_dir: pathlib.Path, backend: str = "auto", model: str | None = None) -> List[Dict[str, Any]]:
    files = list(iter_text_files(corpus_dir))
    entries: List[Dict[str, Any]] = []

    for f in files:
        raw = f.read_text(encoding="utf-8", errors="ignore")
        text = clean_text(raw)
        chunks = chunk_text(text, max_chars=1400)
        if not chunks:
            continue
        # Choose backend
        be = backend
        if be == "auto":
            be = "openai" if os.getenv("OPENAI_API_KEY") else "mock"

        if be == "openai":
            vecs = embed_openai(chunks, model=model or "text-embedding-3-small")
        elif be == "mock":
            vecs = embed_mock(chunks, dim=256)
        else:
            raise ValueError(f"Unknown backend: {backend}")

        for i, (chunk, vec) in enumerate(zip(chunks, vecs)):
            entries.append({
                "id": f"{f.stem}#{i}",
                "text": chunk,
                "source": str(f.relative_to(corpus_dir)),
                "section": i,
                "embedding": vec,
            })
    return entries

# ------------- CLI -------------

def main():
    ap = argparse.ArgumentParser(description="Generate embeddings index for Lilly classical corpus")
    ap.add_argument("--corpus", type=str, default="lilly_engine/data/lilly_corpus", help="Corpus root directory")
    ap.add_argument("--output", type=str, default="lilly_engine/data/embeddings.json", help="Output JSON file")
    ap.add_argument("--backend", type=str, choices=["auto", "openai", "mock"], default="auto", help="Embedding backend")
    ap.add_argument("--model", type=str, default=None, help="Embedding model name (for OpenAI backend)")
    args = ap.parse_args()

    corpus_dir = pathlib.Path(args.corpus).resolve()
    if not corpus_dir.exists():
        raise SystemExit(f"Corpus directory not found: {corpus_dir}")

    entries = build_index(corpus_dir, backend=args.backend, model=args.model)

    out_path = pathlib.Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")

    print(f"Saved {len(entries)} entries to {out_path}")
    if args.backend != "openai":
        print("Note: Non-OpenAI backend used. Embeddings are mock (not semantic).")

if __name__ == "__main__":
    main()
