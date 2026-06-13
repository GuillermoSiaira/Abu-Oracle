"""
RAG module for doctrinal astrology texts.
Extracts chunks from PDFs, indexes with BM25, and retrieves relevant passages.
"""

import re
import json
import pickle
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None


REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = REPO_ROOT / "data" / "doctrinal_corpus"
ASTRO_TEXTS_DIR = REPO_ROOT / "astro-texts"

# Fuentes del corpus. "tradition" permite filtrar retrieval por escuela.
# Triage 2026-06-10: solo PDFs con capa de texto utilizable (>200 chars/pág).
# Excluidos (escaneo sin OCR): Royal Art, Star Names,
# Siddhantas, History of Astronomy in India, Palmistry, White Magic, etc.
# Excluido (OCR latín renacentista ilegible): astronomicum_cesareum.pdf.
# Lilly entra vía el HTML de archive.org (ed. Zadkiel 1852, texto limpio).
CORPUS_SOURCES = [
    # ── Occidental: helenística + Lilly ──
    {
        "path": ASTRO_TEXTS_DIR / "Ptolomeo Claudius - Tetrabiblos.pdf",
        "author": "Claudius Ptolemy",
        "book": "Tetrabiblos",
        "short": "Tet",
        "tradition": "helenistica",
    },
    {
        "path": ASTRO_TEXTS_DIR / "Full text of _An Introduction To Astrology_.html",
        "author": "William Lilly",
        "book": "An Introduction to Astrology (ed. Zadkiel 1852)",
        "short": "IA",
        "tradition": "occidental-lilly",
        "type": "html_pre",
    },
    {
        "path": CORPUS_DIR / "christian_astrology_ocr.txt",
        "author": "William Lilly",
        "book": "Christian Astrology (1647) — pág. de PDF",
        "short": "CA",
        "tradition": "occidental-lilly",
        "type": "ocr_txt",
    },
    # ── Persa/árabe: Al-Biruni ──
    {
        "path": ASTRO_TEXTS_DIR / "Al Biruni - Cronology of Ancient Nations.pdf",
        "author": "Al-Biruni",
        "book": "Chronology of Ancient Nations",
        "short": "CAN",
        "tradition": "persa",
    },
    {
        "path": ASTRO_TEXTS_DIR / "Al Biruni's India_E.Sachau_Hist_Doc.pdf",
        "author": "Al-Biruni",
        "book": "India (trad. Sachau)",
        "short": "Ind",
        "tradition": "persa",
    },
    {
        "path": ASTRO_TEXTS_DIR / "Al-Biruni_Canon_Masudicus_Vol3_Intro_Analysis.pdf",
        "author": "Al-Biruni",
        "book": "Canon Masudicus Vol. 3",
        "short": "CM3",
        "tradition": "persa",
    },
    # ── Jyotish (védica) ──
    {
        "path": ASTRO_TEXTS_DIR / "Jyotish_1994_ S-R-N-Murthy_Phala Jyotish_Interpretative Astrology_according to classics.pdf",
        "author": "S.R.N. Murthy",
        "book": "Phala Jyotish",
        "short": "PJ",
        "tradition": "jyotish",
    },
    {
        "path": ASTRO_TEXTS_DIR / "Jyotish_2017-S.P. Bhagat_Significance of Stellar Astrology.pdf",
        "author": "S.P. Bhagat",
        "book": "Significance of Stellar Astrology",
        "short": "SSA",
        "tradition": "jyotish",
    },
    {
        "path": ASTRO_TEXTS_DIR / "Jyotish_How to read a horoscope by P.V.R. Rayudu.pdf",
        "author": "P.V.R. Rayudu",
        "book": "How to Read a Horoscope",
        "short": "HRH",
        "tradition": "jyotish",
    },
    # ── Armónica / pitagórica ──
    {
        "path": ASTRO_TEXTS_DIR / "lambdoma-akroasis000kays.pdf",
        "author": "Hans Kayser",
        "book": "Akroasis",
        "short": "Akr",
        "tradition": "armonica",
    },
    {
        "path": ASTRO_TEXTS_DIR / "Lambdoma-lehrbuch1950hanskayser.pdf",
        "author": "Hans Kayser",
        "book": "Lehrbuch der Harmonik (1950, alemán)",
        "short": "LH",
        "tradition": "armonica",
    },
    {
        "path": ASTRO_TEXTS_DIR / "bsb11329250.pdf",
        "author": "(BSB, armónica s.XIX, alemán)",
        "book": "Harmonik BSB-11329250",
        "short": "HBS",
        "tradition": "armonica",
    },
    {
        "path": ASTRO_TEXTS_DIR / "pythagoraslife1979gorm.pdf",
        "author": "Peter Gorman",
        "book": "Pythagoras: A Life",
        "short": "PyL",
        "tradition": "pitagorica",
    },
]

TYPE_QUERIES = {
    "conjunction_JS": "júpiter saturno conjunción gran conjunción planetas aspectos",
    "conjunction_MS": "marte saturno conjunción maléfico adverso planetas",
    "conjunction_MJ": "marte júpiter conjunción planetas beneficio",
    "opposition_MS":  "marte saturno oposición maléfico adverso planetas",
    "opposition_MJ":  "marte júpiter oposición aspectos planetas",
    "square_MS":      "marte saturno cuadratura maléfico adverso planetas",
    "square_MJ":      "marte júpiter cuadratura planetas aspectos",
    "trine_MS":       "marte saturno trino planetas aspectos benéfico",
    "stellium":       "planetas signo conjunción múltiples varios",
    "mercury_retrograde": "mercurio retrógrado estación retrogradación movimiento",
    "mercury_direct":     "mercurio directo estación planetas movimiento",
}

_index: Any = None
_chunks: list[dict] = []


def _iter_pdf_pages(path: Path):
    """Yield (page_num, text) for each page of a PDF."""
    doc = fitz.open(path)
    try:
        for page_num in range(doc.page_count):
            text = doc[page_num].get_text("text")
            if text.strip():
                yield page_num + 1, text
    finally:
        doc.close()


def _iter_html_pre_pages(path: Path):
    """
    Yield (page_num, text) from an archive.org "Full text" HTML.
    The book text lives inside <pre>; original page numbers appear as
    standalone numeric lines, which we use as page boundaries so citations
    keep pointing to the printed page.
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<pre>(.*?)</pre>", raw, re.DOTALL)
    body = m.group(1) if m else raw
    page_num = 1
    buf: list[str] = []
    for line in body.split("\n"):
        stripped = line.strip()
        if re.fullmatch(r"\d{1,4}", stripped):
            if buf:
                yield page_num, "\n".join(buf)
                buf = []
            try:
                page_num = int(stripped)
            except ValueError:
                pass
            continue
        buf.append(line)
    if buf:
        yield page_num, "\n".join(buf)


def _iter_ocr_pages(path: Path):
    """
    Yield (page_num, text) from an OCR text file.
    Pages are separated by --- PAGE N --- markers.
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    parts = re.split(r"--- PAGE (\d+) ---", raw)
    
    for i in range(1, len(parts), 2):
        try:
            page_num = int(parts[i])
            text = parts[i+1].strip()
            if text:
                yield page_num, text
        except (ValueError, IndexError):
            continue


def _extract_chunks(source: dict) -> list[dict]:
    """Extract paragraph-sized chunks from a single source (PDF or HTML)."""
    if not source["path"].exists():
        print(f"[RAG] Fuente no encontrada: {source['path']}")
        return []

    source_type = source.get("type", "pdf")
    if source_type == "pdf" and fitz is None:
        print(f"[RAG] fitz not installed, skipping {source['path']}")
        return []

    chunks: list[dict] = []

    def emit(current: list[str], page_num: int) -> None:
        para = re.sub(r"\s+", " ", " ".join(current)).strip()
        if 120 <= len(para) <= 900:
            chunks.append({
                "author": source["author"],
                "book": source["book"],
                "short": source["short"],
                "tradition": source.get("tradition", ""),
                "page": page_num,
                "text": para,
            })

    try:
        if source_type == "html_pre":
            pages = _iter_html_pre_pages(source["path"])
        elif source_type == "ocr_txt":
            pages = _iter_ocr_pages(source["path"])
        else:
            pages = _iter_pdf_pages(source["path"])

        for page_num, text in pages:
            # Group lines into paragraph-sized chunks
            current: list[str] = []
            current_len = 0
            for line in text.split("\n"):
                line = line.strip()
                # Skip noise: very short lines (headers, page numbers, footers)
                if len(line) < 15:
                    # Short line may be a paragraph break — emit if we have content
                    if current_len >= 120:
                        emit(current, page_num)
                    current = []
                    current_len = 0
                    continue

                current.append(line)
                current_len += len(line) + 1

                # Emit at sentence boundary once target size reached, or at hard cap
                if (current_len >= 400 and line.rstrip().endswith((".", ";", ":", "!"))) or current_len >= 850:
                    emit(current, page_num)
                    current = []
                    current_len = 0

            # Emit remainder
            if current_len >= 120:
                emit(current, page_num)
    except Exception as e:
        print(f"[RAG] Error reading {source['path']}: {e}")

    return chunks


def _tokenize(text: str) -> list[str]:
    """Tokenize text for BM25."""
    tokens = re.findall(r"\b[a-záéíóúüñ]+\b", text.lower())
    return tokens


def build_index() -> tuple[Any, list[dict]]:
    """Build BM25 index from all corpus sources."""
    if BM25Okapi is None:
        raise ImportError("rank_bm25 not installed")

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    chunks = []
    for source in CORPUS_SOURCES:
        source_chunks = _extract_chunks(source)
        chunks.extend(source_chunks)

    if not chunks:
        print("[RAG] No chunks extracted from PDFs")
        return None, []

    # Build BM25 index
    tokenized_chunks = [_tokenize(c["text"]) for c in chunks]
    bm25_index = BM25Okapi(tokenized_chunks)

    # Save to disk
    with open(CORPUS_DIR / "chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    with open(CORPUS_DIR / "index.pkl", "wb") as f:
        pickle.dump(bm25_index, f)

    print(f"[RAG] Índice construido: {len(chunks)} chunks")
    return bm25_index, chunks


def load_index() -> tuple[Any, list[dict]]:
    """Load index from disk or build if not exists."""
    if (CORPUS_DIR / "index.pkl").exists() and (CORPUS_DIR / "chunks.json").exists():
        try:
            with open(CORPUS_DIR / "index.pkl", "rb") as f:
                bm25_index = pickle.load(f)

            with open(CORPUS_DIR / "chunks.json", "r", encoding="utf-8") as f:
                chunks = json.load(f)

            return bm25_index, chunks
        except Exception as e:
            print(f"[RAG] Error loading cached index: {e}")

    return build_index()


def _ensure_loaded() -> None:
    """Ensure index is loaded."""
    global _index, _chunks
    if _index is None:
        _index, _chunks = load_index()


def build_retrieval_query(config: dict) -> str:
    """Build retrieval query from config."""
    config_type = config.get("type", "")

    # Check if type is in predefined queries
    if config_type in TYPE_QUERIES:
        query = TYPE_QUERIES[config_type]
    else:
        # Build from planets and label
        planets = " ".join(config.get("planets", []))
        label = config.get("label", "")
        query = f"{planets} {label}"

    # Add ingress if applicable
    if "ingress" in config_type.lower():
        query += " ingress"

    return query.strip()


def retrieve(config: dict, k: int = 3) -> list[str]:
    """Retrieve top-k doctrinal passages for a configuration."""
    try:
        _ensure_loaded()

        if _index is None or len(_chunks) == 0:
            return []

        query = build_retrieval_query(config)
        tokens = _tokenize(query)

        if not tokens:
            return []

        scores = _index.get_scores(tokens)

        # Get top-k indices with score > 0
        top_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:k]
        top_indices = [i for i in top_indices if scores[i] > 0]

        passages = []
        for idx in top_indices:
            chunk = _chunks[idx]
            text = chunk["text"]

            # Truncate text
            if len(text) > 350:
                text_display = text[:350] + "..."
            else:
                text_display = text

            passage = f'[{chunk["short"]}, {chunk["book"]}, p.{chunk["page"]}] "{text_display}"'
            passages.append(passage)

        return passages

    except Exception as e:
        print(f"[RAG] Error in retrieve(): {e}")
        return []


def rebuild_index() -> None:
    """Rebuild index from scratch."""
    try:
        if (CORPUS_DIR / "index.pkl").exists():
            (CORPUS_DIR / "index.pkl").unlink()
        if (CORPUS_DIR / "chunks.json").exists():
            (CORPUS_DIR / "chunks.json").unlink()
        build_index()
    except Exception as e:
        print(f"[RAG] Error rebuilding index: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        print("[RAG] Construyendo índice desde PDFs...")
        build_index()
        _ensure_loaded()
        print(f"[RAG] Índice construido. Chunks totales: {len(_chunks)}")
    elif len(sys.argv) > 1:
        query_arg = " ".join(sys.argv[1:])
        _ensure_loaded()

        if _index is None:
            print("[RAG] No index available")
            sys.exit(1)

        # Test retrieval
        tokens = _tokenize(query_arg)
        scores = _index.get_scores(tokens)
        top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]

        print(f"\nResults for: {query_arg}\n")
        for i in top:
            c = _chunks[i]
            print(f"[{c['short']}, p.{c['page']}] score={scores[i]:.2f}")
            print(c["text"][:300])
            print()
    else:
        print("Usage: python doctrinal_rag.py build | python doctrinal_rag.py <query>")
