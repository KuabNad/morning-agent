from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import re

import feedparser


@dataclass
class NewsItem:
    title: str
    link: str


@dataclass
class NewsSection:
    name: str
    items: list[NewsItem]


def fetch_news(settings, per_section: int = 3) -> list[NewsSection]:
    sections = [
        ("Canary Islands / Spain", settings.canary_rss_feeds),
        ("Science / Astronomy", settings.science_rss_feeds),
        ("World", settings.world_rss_feeds),
    ]
    return [NewsSection(name, _fetch_section(feeds, per_section)) for name, feeds in sections]


def _fetch_section(feeds: list[str], limit: int) -> list[NewsItem]:
    items: list[NewsItem] = []
    seen_titles: set[str] = set()

    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = _clean_text(getattr(entry, "title", ""))
                if not title or title.lower() in seen_titles:
                    continue
                seen_titles.add(title.lower())
                items.append(NewsItem(title=title, link=getattr(entry, "link", "")))
                if len(items) >= limit:
                    return items
        except Exception:
            continue

    return items


def _clean_text(value: str) -> str:
    value = unescape(value or "")
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value
