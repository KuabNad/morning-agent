from html import escape
import re

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
                "text": _format_for_telegram(text),
                "parse_mode": "HTML",
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


def _format_for_telegram(text: str) -> str:
    formatted_lines = []
    link_pattern = re.compile(r"^\s*\(read more\)\s+(https?://\S+)\s*$")

    for line in text.splitlines():
        match = link_pattern.match(line)
        if match:
            url = escape(match.group(1), quote=True)
            formatted_lines.append(f'  <a href="{url}">(read more)</a>')
        else:
            formatted_lines.append(escape(line))

    return "\n".join(formatted_lines)
