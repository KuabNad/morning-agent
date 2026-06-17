from calendar_events import fetch_today_events
from config import settings
from digest_builder import build_digest
from email_sender import send_email_backup
from news import fetch_news
from telegram_sender import send_telegram_message
from weather import fetch_weather


def main() -> None:
    calendar_result = fetch_today_events(settings)
    weather_report = fetch_weather(settings)
    news_sections = fetch_news(settings)

    digest = build_digest(settings, calendar_result, weather_report, news_sections)

    sent_to_telegram = send_telegram_message(settings, digest)
    if sent_to_telegram:
        print("Digest sent to Telegram.")

    send_email_backup(settings, "Morning digest", digest)


if __name__ == "__main__":
    main()
