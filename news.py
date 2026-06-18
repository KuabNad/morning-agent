from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
import re
from urllib.parse import urljoin

import feedparser
import requests


@dataclass
class NewsItem:
    title: str
    link: str


@dataclass
class NewsSection:
    name: str
    items: list[NewsItem]


def fetch_news(settings, per_section: int = 3) -> list[NewsSection]:
    return [
        NewsSection(
            "Spanish politics",
            _fetch_section(settings.spanish_politics_rss_feeds, per_section),
        ),
        NewsSection("Science", _fetch_section(settings.science_rss_feeds, 2)),
        NewsSection(
            "Galaxy evolution papers",
            _fetch_galaxy_papers(settings.arxiv_recent_url, 3),
        ),
        NewsSection(
            "World politics",
            _fetch_section(settings.world_politics_rss_feeds, per_section),
        ),
    ]


def _fetch_section(feeds: list[str], limit: int) -> list[NewsItem]:
    feed_items: list[list[NewsItem]] = []
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            items = [
                NewsItem(
                    title=_clean_text(getattr(entry, "title", "")),
                    link=getattr(entry, "link", ""),
                )
                for entry in feed.entries
                if _is_usable_headline(_clean_text(getattr(entry, "title", "")))
            ]
            if items:
                feed_items.append(items)
        except Exception:
            continue

    items: list[NewsItem] = []
    seen_titles: set[str] = set()
    position = 0
    while feed_items and len(items) < limit:
        found_new_item = False
        for source_items in feed_items:
            if position >= len(source_items):
                continue
            item = source_items[position]
            key = item.title.casefold()
            if key not in seen_titles:
                seen_titles.add(key)
                items.append(item)
                found_new_item = True
                if len(items) >= limit:
                    return items
        if not found_new_item and all(position >= len(source) - 1 for source in feed_items):
            break
        position += 1

    return items


def _fetch_galaxy_papers(recent_url: str, limit: int) -> list[NewsItem]:
    recent_items = _fetch_arxiv_recent(recent_url, limit)
    if recent_items:
        return recent_items
    return _fetch_arxiv_query("cat:astro-ph.GA", limit)


def _fetch_arxiv_recent(recent_url: str, limit: int) -> list[NewsItem]:
    try:
        response = requests.get(
            recent_url,
            headers={"User-Agent": "morning-agent/1.0 (daily astronomy digest)"},
            timeout=20,
        )
        response.raise_for_status()

        parser = _ArxivRecentParser()
        parser.feed(response.text)
        return _unique_items(parser.items, limit)
    except (requests.RequestException, ValueError):
        return []


def _fetch_arxiv_query(query: str, limit: int) -> list[NewsItem]:
    try:
        response = requests.get(
            "https://export.arxiv.org/api/query",
            params={
                "search_query": query,
                "start": 0,
                "max_results": max(limit, 10),
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            },
            headers={"User-Agent": "morning-agent/1.0"},
            timeout=20,
        )
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        items = [
            NewsItem(
                title=_clean_text(getattr(entry, "title", "")),
                link=getattr(entry, "link", ""),
            )
            for entry in feed.entries
            if _clean_text(getattr(entry, "title", ""))
        ]
        return _unique_items(items, limit)
    except requests.RequestException:
        return []


def _unique_items(items: list[NewsItem], limit: int) -> list[NewsItem]:
    unique: list[NewsItem] = []
    seen_titles: set[str] = set()
    for item in items:
        key = item.title.casefold()
        if not item.title or key in seen_titles:
            continue
        seen_titles.add(key)
        unique.append(item)
        if len(unique) >= limit:
            break
    return unique


class _ArxivRecentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.items: list[NewsItem] = []
        self._links: list[str] = []
        self._title_depth = 0
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if self._title_depth:
            self._title_depth += 1
            return

        if tag == "a" and attributes.get("title") == "Abstract":
            href = attributes.get("href") or ""
            if href.startswith("/abs/"):
                self._links.append(urljoin("https://arxiv.org", href))

        classes = (attributes.get("class") or "").split()
        if tag == "div" and "list-title" in classes:
            self._title_depth = 1
            self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._title_depth:
            self._text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self._title_depth:
            return
        self._title_depth -= 1
        if self._title_depth:
            return

        title = re.sub(r"^Title:\s*", "", _clean_text(" ".join(self._text_parts)))
        item_index = len(self.items)
        if title and item_index < len(self._links):
            self.items.append(NewsItem(title=title, link=self._links[item_index]))
        self._text_parts = []


def _clean_text(value: str) -> str:
    value = unescape(value or "")
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _is_usable_headline(title: str) -> bool:
    lowered = title.casefold()
    if not title or "http://" in lowered or "https://" in lowered:
        return False

    letters = [character for character in title if character.isalpha()]
    uppercase_ratio = (
        sum(character.isupper() for character in letters) / len(letters)
        if letters
        else 0
    )
    return len(letters) < 20 or uppercase_ratio < 0.65
