import requests


def send_telegram_message(settings, text: str) -> bool:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        print(text)
        return False

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
            data={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        response.raise_for_status()
        return True
    except Exception as exc:
        print(f"Telegram send failed: {exc}")
        print(text)
        return False
