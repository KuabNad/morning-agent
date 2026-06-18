import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


DEFAULT_SPANISH_POLITICS_FEEDS = [
    (
        "https://news.google.com/rss/search"
        "?q=politica+espanola+when:1d+-site:facebook.com+-site:marca.com"
        "&hl=es&gl=ES&ceid=ES:es"
    ),
]

DEFAULT_SCIENCE_FEEDS = [
    "https://www.sciencedaily.com/rss/top/science.xml",
    "https://www.nasa.gov/news-release/feed/",
]

DEFAULT_WORLD_POLITICS_FEEDS = [
    (
        "https://news.google.com/rss/search"
        "?q=international+government+election+diplomacy+when:1d"
        "&hl=en-US&gl=US&ceid=US:en"
    ),
]


def get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_str(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or default


@dataclass(frozen=True)
class Settings:
    location_name: str = get_str("LOCATION_NAME", "Santa Cruz de Tenerife")
    latitude: float = get_float("LATITUDE", 28.4636)
    longitude: float = get_float("LONGITUDE", -16.2518)
    timezone: str = get_str("TIMEZONE", "Atlantic/Canary")

    telegram_bot_token: str = get_str("TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = get_str("TELEGRAM_CHAT_ID")

    openai_api_key: str = get_str("OPENAI_API_KEY")
    openai_model: str = get_str("OPENAI_MODEL", "gpt-4o-mini")

    email_enabled: bool = get_bool("EMAIL_ENABLED", False)
    smtp_host: str = get_str("SMTP_HOST")
    smtp_port: int = get_int("SMTP_PORT", 587)
    smtp_user: str = get_str("SMTP_USER")
    smtp_password: str = get_str("SMTP_PASSWORD")
    email_from: str = get_str("EMAIL_FROM")
    email_to: str = get_str("EMAIL_TO")

    google_calendar_id: str = get_str("GOOGLE_CALENDAR_ID")
    google_service_account_json: str = get_str("GOOGLE_SERVICE_ACCOUNT_JSON")

    spanish_politics_rss_feeds: list[str] = None
    science_rss_feeds: list[str] = None
    world_politics_rss_feeds: list[str] = None
    benty_fields_url: str = get_str(
        "BENTY_FIELDS_URL",
        "https://www.benty-fields.com/daily_arXiv_results",
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "spanish_politics_rss_feeds",
            get_list("SPANISH_POLITICS_RSS_FEEDS", DEFAULT_SPANISH_POLITICS_FEEDS),
        )
        object.__setattr__(self, "science_rss_feeds", get_list("SCIENCE_RSS_FEEDS", DEFAULT_SCIENCE_FEEDS))
        object.__setattr__(
            self,
            "world_politics_rss_feeds",
            get_list("WORLD_POLITICS_RSS_FEEDS", DEFAULT_WORLD_POLITICS_FEEDS),
        )


settings = Settings()
