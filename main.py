from arxiv_group_digest import (
    build_arxiv_group_digest,
    save_group_paper_state,
    select_group_papers,
)
from calendar_events import fetch_today_events
from config import settings
from digest_builder import build_digest
from email_sender import send_email_backup
from news import enrich_arxiv_papers, fetch_group_paper_candidates, fetch_news
from telegram_sender import send_telegram_group_message, send_telegram_message
from weather import fetch_weather


def main() -> None:
    calendar_result = fetch_today_events(settings)
    weather_report = fetch_weather(settings)
    news_sections = fetch_news(settings)

    digest = build_digest(settings, calendar_result, weather_report, news_sections)

    sent_to_telegram = send_telegram_message(settings, digest)
    if sent_to_telegram:
        print("Digest sent to Telegram.")

    if settings.telegram_group_chat_id and settings.openai_api_key:
        candidates = fetch_group_paper_candidates(settings)
        group_papers = enrich_arxiv_papers(select_group_papers(candidates))
        group_digest = build_arxiv_group_digest(settings, group_papers)
        if send_telegram_group_message(settings, group_digest):
            save_group_paper_state(candidates, group_papers)
            print("Spanish arXiv digest sent to Telegram group.")

    send_email_backup(settings, "Morning digest", digest)


if __name__ == "__main__":
    main()
