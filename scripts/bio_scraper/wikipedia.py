"""Download and clean Wikipedia articles for LLM extraction."""
from __future__ import annotations
import logging
import re

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_WIKI_API = "https://{lang}.wikipedia.org/api/rest_v1/page/html/{title}"
_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "AIOracleBioScraper/1.0 (research; contact@ai-oracle.dev)",
    "Accept": "text/html",
})


def fetch_article(title: str, lang: str = "en") -> str:
    """Download a Wikipedia article and return clean plain text."""
    url = _WIKI_API.format(lang=lang, title=title)
    resp = _SESSION.get(url, timeout=30)
    resp.raise_for_status()
    return _html_to_text(resp.text)


def _html_to_text(html: str) -> str:
    """Strip HTML tags and clean up Wikipedia article text."""
    soup = BeautifulSoup(html, "lxml")

    # Remove navigation, references, infoboxes by tag name/class
    for tag_name in ["table", "style", "script", "sup"]:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for class_name in ["reflist", "navbox", "sidebar", "infobox",
                       "mw-editsection", "reference", "mw-references-wrap",
                       "hatnote", "shortdescription"]:
        for tag in soup.find_all(class_=class_name):
            tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Truncate to ~12k chars to stay within LLM context
    if len(text) > 12000:
        text = text[:12000] + "\n[...truncado a 12 000 caracteres]"

    return text
