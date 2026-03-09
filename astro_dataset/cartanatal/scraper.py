from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Iterable, List, Optional, Set
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://carta-natal.es/"
DEFAULT_MIN_INTERVAL = 2.0  # seconds between requests


class CartanatalClient:
    def __init__(
        self,
        *,
        cache_dir: Path,
        min_interval: float = DEFAULT_MIN_INTERVAL,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.cache_dir = cache_dir
        self.min_interval = min_interval
        self.session = session or requests.Session()
        self._last_request_ts: Optional[float] = None
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _rate_limit(self) -> None:
        if self._last_request_ts is None:
            return
        elapsed = time.monotonic() - self._last_request_ts
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

    def _fetch_network(self, url: str) -> str:
        self._rate_limit()
        resp = self.session.get(url, timeout=15)
        self._last_request_ts = time.monotonic()
        resp.raise_for_status()
        return resp.text

    def fetch(self, url: str, cache_path: Path) -> str:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        if cache_path.exists():
            return cache_path.read_text(encoding="utf-8", errors="ignore")
        html = self._fetch_network(url)
        cache_path.write_text(html, encoding="utf-8")
        return html

    @staticmethod
    def _hash_url(url: str) -> str:
        return hashlib.sha1(url.encode("utf-8")).hexdigest()

    def crawl_ids(self, start_url: str = urljoin(BASE_URL, "astrodata/famosos/")) -> List[int]:
        seen: Set[int] = set()
        letters = self._discover_letter_urls(start_url)
        for letter_url in letters:
            letter = self._extract_letter(letter_url)
            current_url = letter_url
            page_idx = 1
            while current_url:
                cache_file = self.cache_dir / "pages" / f"{letter}_page_{page_idx}.html"
                html = self.fetch(current_url, cache_file)
                new_ids = self._extract_ids(html)
                seen.update(new_ids)
                next_link = self._find_next_link(html, current_url)
                if next_link:
                    current_url = next_link
                    page_idx += 1
                else:
                    break
        return sorted(seen)

    def _discover_letter_urls(self, start_url: str) -> List[str]:
        """Return list of URLs for each letter page (A-Z)."""
        html = self.fetch(start_url, self.cache_dir / "pages" / "letters_index.html")
        soup = BeautifulSoup(html, "lxml")
        urls: Set[str] = set([start_url])
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "astrodata/famosos/?letra=" in href:
                urls.add(urljoin(start_url, href))
        return sorted(urls)

    @staticmethod
    def _extract_letter(url: str) -> str:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        letter = qs.get("letra", ["A"])[0]
        return letter or "A"

    @staticmethod
    def _extract_ids(html: str) -> Iterable[int]:
        soup = BeautifulSoup(html, "lxml")
        ids: Set[int] = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "carta.php?id=" in href:
                try:
                    part = href.split("id=")[-1]
                    ids.add(int(part))
                except ValueError:
                    continue
        return ids

    def _find_next_link(self, html: str, base_url: str) -> Optional[str]:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            if "Siguiente" in a.get_text(strip=True):
                return urljoin(base_url, a["href"])
        return None

    def fetch_profile(self, profile_id: int) -> str:
        url = urljoin(BASE_URL, f"astrodata/famosos/carta.php?id={profile_id}")
        cache_file = self.cache_dir / "profiles" / f"{profile_id}.html"
        return self.fetch(url, cache_file)
