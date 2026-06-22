from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
import re
from urllib.parse import urljoin

import requests


BIBLE_GATEWAY_URL = "https://www.biblegateway.com/"
FALLBACK_TEXT = "Teach us to number our days, that we may gain a heart of wisdom."
FALLBACK_REFERENCE = "Psalm 90:12"


@dataclass
class DailyVerse:
    text: str
    reference: str
    translation: str = ""
    link: str = ""


def fetch_daily_verse() -> DailyVerse:
    try:
        response = requests.get(
            BIBLE_GATEWAY_URL,
            headers={"User-Agent": "morning-agent/1.0"},
            timeout=20,
        )
        response.raise_for_status()

        parser = _BibleGatewayVerseParser()
        parser.feed(response.text)
        if parser.text and parser.reference:
            return DailyVerse(
                text=parser.text,
                reference=parser.reference,
                translation=parser.translation,
                link=parser.link,
            )
    except (requests.RequestException, ValueError):
        pass

    return DailyVerse(text=FALLBACK_TEXT, reference=FALLBACK_REFERENCE)


class _BibleGatewayVerseParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text = ""
        self.reference = ""
        self.translation = ""
        self.link = ""
        self._citation_depth = 0
        self._verse_depth = 0
        self._link_depth = 0
        self._current_link = ""
        self._citation_parts: list[str] = []
        self._link_parts: list[str] = []
        self._verse_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)

        if self._verse_depth:
            self._verse_depth += 1
        elif tag == "div" and attributes.get("id") == "verse-text":
            self._verse_depth = 1

        if self._citation_depth:
            self._citation_depth += 1
        elif tag == "span" and "citation" in (attributes.get("class") or "").split():
            self._citation_depth = 1
            self._citation_parts = []

        if tag == "a" and not self.reference:
            href = attributes.get("href") or ""
            if "/passage/?search=" in href:
                self._link_depth = 1
                self._current_link = urljoin(BIBLE_GATEWAY_URL, href)
                self._link_parts = []
        elif self._link_depth:
            self._link_depth += 1

    def handle_data(self, data: str) -> None:
        if self._verse_depth:
            self._verse_parts.append(data)
        if self._citation_depth:
            self._citation_parts.append(data)
        if self._link_depth:
            self._link_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._verse_depth:
            self._verse_depth -= 1
            if not self._verse_depth:
                self.text = _clean_text(" ".join(self._verse_parts))

        if self._citation_depth:
            self._citation_depth -= 1
            if not self._citation_depth:
                self.reference = _clean_text(" ".join(self._citation_parts))

        if self._link_depth:
            self._link_depth -= 1
            if not self._link_depth and tag == "a":
                link_text = _clean_text(" ".join(self._link_parts))
                translation = re.search(r"\(([^)]+)\)", link_text)
                self.translation = translation.group(1) if translation else ""
                self.link = self._current_link


def _clean_text(value: str) -> str:
    value = unescape(value or "")
    return re.sub(r"\s+", " ", value).strip()
