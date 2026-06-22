from html import escape
import re

import requests


def send_telegram_message(settings, text: str) -> bool:
    return _send_to_chat(settings, settings.telegram_chat_id, text, "private")


def send_telegram_group_message(settings, text: str) -> bool:
    if not settings.telegram_group_chat_id or not text:
        return False
    return _send_to_chat(settings, settings.telegram_group_chat_id, text, "group")


def _send_to_chat(settings, chat_id: str, text: str, destination: str) -> bool:
    if not settings.telegram_bot_token or not chat_id:
        print(text)
        return False

    try:
        for chunk in _split_message(text):
            response = requests.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                data={
                    "chat_id": chat_id,
                    "text": _format_for_telegram(chunk),
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
            response.raise_for_status()
        return True
    except Exception as exc:
        print(f"Telegram {destination} send failed: {exc}")
        print(text)
        return False


def _format_for_telegram(text: str) -> str:
    formatted_lines = []
    link_pattern = re.compile(
        r"^\s*\((read more|open in BibleGateway)\)\s+(https?://\S+)\s*$"
    )

    for line in text.splitlines():
        match = link_pattern.match(line)
        if match:
            label = escape(match.group(1))
            url = escape(match.group(2), quote=True)
            formatted_lines.append(f'  <a href="{url}">({label})</a>')
        else:
            formatted_lines.append(escape(line))

    return "\n".join(formatted_lines)


def _split_message(text: str, limit: int = 3800) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        if len(paragraph) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long_paragraph(paragraph, limit))
            continue

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = paragraph

    if current:
        chunks.append(current)
    return chunks


def _split_long_paragraph(paragraph: str, limit: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for line in paragraph.splitlines():
        if len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(
                line[index : index + limit]
                for index in range(0, len(line), limit)
            )
            continue

        candidate = f"{current}\n{line}".strip() if current else line
        if len(candidate) <= limit:
            current = candidate
        else:
            chunks.append(current)
            current = line

    if current:
        chunks.append(current)
    return chunks
