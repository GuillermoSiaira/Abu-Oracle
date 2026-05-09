#!/usr/bin/env python3
"""
bv_analyzer.py - Analiza el corpus de experimentos de validacion ciega.

Lee:
  data/blind_validation/BV_index.json
  data/blind_validation/BV_NNN_*.md

Escribe:
  analysis/blind_validation_summary.md
  analysis/blind_validation_data.csv
"""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = REPO_ROOT / "data" / "blind_validation" / "BV_index.json"
BV_DATA_DIR = REPO_ROOT / "data" / "blind_validation"
ANALYSIS_DIR = REPO_ROOT / "analysis"
SUMMARY_PATH = ANALYSIS_DIR / "blind_validation_summary.md"
CSV_PATH = ANALYSIS_DIR / "blind_validation_data.csv"


def parse_bv_markdown(md_path: Path) -> dict:
    """
    Extrae campos clave del markdown de un experimento BV.

    Campos:
      - score: int | None
      - tradition: str | None
      - doctrinal_accuracy: float | None
      - evaluator_notes: str | None
      - lilly_response_length: int
      - has_verification: bool
    """
    text = md_path.read_text(encoding="utf-8")
    result: dict = {
        "score": None,
        "tradition": None,
        "doctrinal_accuracy": None,
        "evaluator_notes": None,
        "lilly_response_length": 0,
        "has_verification": False,
    }

    score_match = re.search(
        r"(?:Score(?:\s+(?:final|cualitativo))?|\*\*Score(?:\s+final)?\:\*\*)"
        r"[\s:*]*(\d)\s*(?:/|de\s*)?5?",
        text,
        re.IGNORECASE,
    )
    if score_match:
        result["score"] = int(score_match.group(1))

    trad_match = re.search(
        r"(?:Tradici[oó]n|tradition)[\s:*]+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ -]+)",
        text,
        re.IGNORECASE,
    )
    if trad_match:
        result["tradition"] = trad_match.group(1).strip().lower()

    prec_match = re.search(
        r"Precisi[oó]n\s+doctrinal[\s:*]+([0-9]+(?:\.[0-9]+)?%?)",
        text,
        re.IGNORECASE,
    )
    if prec_match:
        raw = prec_match.group(1)
        result["doctrinal_accuracy"] = (
            float(raw.rstrip("%")) / 100 if raw.endswith("%") else float(raw)
        )

    verif_text = _extract_section(text, r"Verificaci[oó]n del operador")
    if not verif_text:
        verif_text = _extract_section(text, r"Evaluaci[oó]n por dimensiones del protocolo")
    if not verif_text:
        verif_text = _extract_section(text, r"Inferencias de Lilly vs verificaci[oó]n del operador")
    if verif_text:
        cleaned = _strip_markdown_boilerplate(verif_text)
        result["has_verification"] = len(cleaned) > 30
        result["evaluator_notes"] = cleaned[:300] if cleaned else None

    lilly_text = _extract_section(text, r"Respuesta de Lilly")
    if lilly_text:
        result["lilly_response_length"] = len(lilly_text.strip())

    return result


def load_all_experiments() -> list[dict]:
    """Carga todos los experimentos desde el indice y los markdowns."""
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"BV index not found: {INDEX_PATH}")

    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    experiments = index if isinstance(index, list) else index.get("experiments", [])

    results: list[dict] = []
    for exp in experiments:
        bv_id = exp.get("id", "BV_???")
        alias = exp.get("alias", "unknown")
        status = str(exp.get("status", "unknown")).lower()
        md_path = _find_markdown(bv_id, alias, exp.get("file"))
        parsed = parse_bv_markdown(md_path) if md_path else {}

        score = parsed.get("score")
        if score is None:
            score = _score_from_index(exp)

        results.append(
            {
                "id": bv_id,
                "alias": alias,
                "status": status,
                "score": score,
                "tradition": parsed.get("tradition"),
                "doctrinal_accuracy": parsed.get("doctrinal_accuracy"),
                "has_verification": parsed.get("has_verification", False),
                "lilly_response_length": parsed.get("lilly_response_length", 0),
                "evaluator_notes": parsed.get("evaluator_notes", ""),
                "markdown_path": str(md_path.relative_to(REPO_ROOT)) if md_path else "",
            }
        )

    return results


def write_summary_md(experiments: list[dict]) -> None:
    """Escribe analysis/blind_validation_summary.md con tabla de resultados."""
    ANALYSIS_DIR.mkdir(exist_ok=True)

    completed = [e for e in experiments if e["status"] == "completed"]
    pending = [e for e in experiments if e["status"] != "completed"]
    scores = [e["score"] for e in completed if e["score"] is not None]
    mean_score = sum(scores) / len(scores) if scores else None
    prec_vals = [
        e["doctrinal_accuracy"]
        for e in completed
        if e["doctrinal_accuracy"] is not None
    ]
    mean_prec = sum(prec_vals) / len(prec_vals) if prec_vals else None

    lines = [
        "# Blind Validation - Summary",
        f"*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        f"**Completed experiments:** {len(completed)} / {len(experiments)}",
        f"**Mean score (0-5):** {mean_score:.2f}" if mean_score is not None else "**Mean score:** N/A",
        f"**Mean doctrinal accuracy:** {mean_prec:.2%}"
        if mean_prec is not None
        else "**Mean doctrinal accuracy:** not yet computed",
        "",
        "## Results",
        "",
        "| ID | Alias | Score | Tradition | Doctrinal Acc | Verification | Notes |",
        "|---|---|---|---|---|---|---|",
    ]

    for exp in completed:
        score_str = f"{exp['score']}/5" if exp["score"] is not None else "-"
        prec_str = (
            f"{exp['doctrinal_accuracy']:.0%}"
            if exp["doctrinal_accuracy"] is not None
            else "-"
        )
        notes = _md_cell((exp.get("evaluator_notes") or "")[:100])
        verification = "yes" if exp.get("has_verification") else "no"
        lines.append(
            f"| {exp['id']} | {exp['alias']} | {score_str} | "
            f"{exp['tradition'] or '-'} | {prec_str} | {verification} | {notes} |"
        )

    if pending:
        lines += ["", "## Pending", ""]
        for exp in pending:
            lines.append(f"- {exp['id']} - {exp['alias']} ({exp['status']})")

    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[bv_analyzer] Summary: {SUMMARY_PATH}")


def write_csv(experiments: list[dict]) -> None:
    """Escribe analysis/blind_validation_data.csv para analisis estadistico."""
    ANALYSIS_DIR.mkdir(exist_ok=True)
    fields = [
        "id",
        "alias",
        "status",
        "score",
        "tradition",
        "doctrinal_accuracy",
        "has_verification",
        "lilly_response_length",
        "markdown_path",
    ]

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(experiments)

    print(f"[bv_analyzer] CSV: {CSV_PATH}")


def _extract_section(text: str, heading_pattern: str) -> str:
    match = re.search(
        rf"##\s+{heading_pattern}\s*\n+([\s\S]+?)(?:\n##\s+|\Z)",
        text,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def _strip_markdown_boilerplate(text: str) -> str:
    lines = []
    for line in text.splitlines():
        cleaned = line.strip()
        if not cleaned or set(cleaned) <= {"-", "|", " "}:
            continue
        if "Completar esta seccion" in cleaned or "Completar esta sección" in cleaned:
            continue
        if cleaned.startswith("|") and cleaned.endswith("|"):
            cells = [cell.strip("* ").strip() for cell in cleaned.strip("|").split("|")]
            normalized = [cell.lower() for cell in cells]
            if any(cell in {"dimensión", "dimension", "score", "notas"} for cell in normalized):
                continue
            if len(cells) >= 3:
                lines.append(f"{cells[0]}: {cells[-1]}")
                continue
        lines.append(cleaned)
    return " ".join(lines).strip()


def _find_markdown(bv_id: str, alias: str, filename: object) -> Path | None:
    if isinstance(filename, str) and filename:
        path = BV_DATA_DIR / filename
        if path.exists():
            return path

    md_files = sorted(BV_DATA_DIR.glob(f"{bv_id}_*.md"))
    if md_files:
        return md_files[0]

    slug = re.sub(r"[^a-z0-9]+", "_", alias.lower()).strip("_")
    md_files = sorted(BV_DATA_DIR.glob(f"*{slug}*.md"))
    return md_files[0] if md_files else None


def _score_from_index(exp: dict) -> int | None:
    score = exp.get("score")
    if isinstance(score, dict):
        value = score.get("dimensions_passed")
        return int(value) if isinstance(value, int) else None
    if isinstance(score, int):
        return score
    if isinstance(score, str):
        match = re.search(r"\d", score)
        return int(match.group(0)) if match else None
    return None


def _md_cell(value: str) -> str:
    return value.replace("\n", " ").replace("|", "\\|") or "-"


def main() -> int:
    experiments = load_all_experiments()
    write_summary_md(experiments)
    write_csv(experiments)

    completed = [e for e in experiments if e["status"] == "completed"]
    print(
        f"[bv_analyzer] Done - {len(completed)} completed, "
        f"{len(experiments) - len(completed)} pending"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
