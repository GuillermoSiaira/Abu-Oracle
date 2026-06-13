"""
Corrige la 's larga' (ſ) leída como 'f' en el OCR de Christian Astrology.
Regla: si word-con-f no es palabra válida pero word-con-s sí, reemplazar.
Las f legítimas (of, for, fortune, fixed...) se preservan.
"""
import re
import sys
from pathlib import Path
from itertools import combinations

try:
    from spellchecker import SpellChecker
except ImportError:
    print("pip install pyspellchecker"); sys.exit(1)

REPO = Path(__file__).resolve().parents[2]
TXT = REPO / "data" / "doctrinal_corpus" / "christian_astrology_ocr.txt"

spell = SpellChecker()  # diccionario inglés con frecuencias, sin descarga
# Vocabulario astrológico que el dict general puede no tener:
DOMAIN = {
    "ascendant", "significator", "significators", "disposition", "dispositor",
    "retrograde", "combust", "cazimi", "almuten", "antiscion", "antiscions",
    "profection", "firdaria", "decumbiture", "sextile", "trine", "quartile",
    "horary", "querent", "quesited", "hyleg", "alcocoden", "exaltation",
}
KNOWN = set(spell.word_frequency.dictionary.keys()) | DOMAIN

def is_word(w: str) -> bool:
    return w.lower() in KNOWN

def fix_token(word: str) -> str:
    if "f" not in word.lower():
        return word
    if is_word(word):              # f legítima → no tocar
        return word
    idxs = [i for i, c in enumerate(word) if c.lower() == "f"]
    # probar de más reemplazos a menos (ſſ dobles primero)
    for r in range(len(idxs), 0, -1):
        for combo in combinations(idxs, r):
            chars = list(word)
            for i in combo:
                chars[i] = "S" if word[i].isupper() else "s"
            cand = "".join(chars)
            if is_word(cand):
                return cand
    return word

TOKEN = re.compile(r"[A-Za-z]+")

def fix_line(line: str) -> str:
    if line.startswith("--- PAGE "):      # no tocar marcadores
        return line
    return TOKEN.sub(lambda m: fix_token(m.group(0)), line)

def main():
    raw = TXT.read_text(encoding="utf-8")
    fixed = "\n".join(fix_line(ln) for ln in raw.split("\n"))
    TXT.write_text(fixed, encoding="utf-8")
    print(f"[FIX] corregido in-place: {TXT}")

if __name__ == "__main__":
    main()
