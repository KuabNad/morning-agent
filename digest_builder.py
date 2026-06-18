from __future__ import annotations

import re

REFLECTION = "Teach us to number our days, that we may gain a heart of wisdom. — Psalm 90:12"


def build_digest(settings, calendar_result, weather_report, news_sections) -> str:
    base_digest = _build_template_digest(calendar_result, weather_report, news_sections)

    if not settings.openai_api_key:
        return base_digest

    try:
        return _polish_with_openai(settings, base_digest)
    except Exception as exc:
        print(f"OpenAI polishing failed: {exc}")
        return base_digest


def _build_template_digest(calendar_result, weather_report, news_sections) -> str:
    lines = ["Good morning Kuba 👋", "", "🗓 Today"]
    lines.extend(_calendar_lines(calendar_result))

    lines.extend(["", "🌤 Weather", _weather_line(weather_report), weather_report.practical_sentence])

    lines.extend(["", "📰 News"])
    for section in news_sections:
        lines.append(f"{section.name}:")
        if section.items:
            for item in section.items:
                lines.append(f"* {item.title}")
                if item.link:
                    lines.append(f"  (read more) {item.link}")
        else:
            lines.append("* No items available right now.")
        lines.append("")

    lines.extend(["✅ Suggested priorities"])
    lines.extend(_priority_lines(calendar_result, weather_report))

    lines.extend(["", "🙏 Reflection", f"“{REFLECTION}”"])
    return "\n".join(lines).strip()


def _calendar_lines(calendar_result) -> list[str]:
    if not calendar_result.configured:
        return [calendar_result.message or "No calendar configured yet."]
    if not calendar_result.events:
        return ["No calendar items today."]

    lines = [f"You have {len(calendar_result.events)} calendar item(s):"]
    for event in calendar_result.events:
        lines.append(f"* {event.start} — {event.title}")
    return lines


def _weather_line(weather_report) -> str:
    pieces = [weather_report.condition]
    if weather_report.temperature_c is not None:
        pieces.append(f"{round(weather_report.temperature_c)}°C")
    if weather_report.rain_chance is not None:
        pieces.append(f"{weather_report.rain_chance}% rain chance")
    if weather_report.wind_kmh is not None:
        pieces.append(f"wind {round(weather_report.wind_kmh)} km/h")
    return ", ".join(pieces) + "."


def _priority_lines(calendar_result, weather_report) -> list[str]:
    priorities = []
    if calendar_result.configured and calendar_result.events:
        priorities.append("Review today's appointments and prepare anything needed before the first one.")
    else:
        priorities.append("Choose the one task that would make the day feel meaningfully complete.")

    if weather_report.rain_chance is not None and weather_report.rain_chance >= 50:
        priorities.append("Plan outdoor movement early or keep it flexible around the rain.")
    else:
        priorities.append("Take a short walk or run while the morning is still fresh.")

    priorities.append("Leave one quiet block for reflection, planning, or focused work.")
    return [f"{index}. {item}" for index, item in enumerate(priorities, start=1)]


def _polish_with_openai(settings, base_digest: str) -> str:
    from openai import OpenAI

    links: list[str] = []

    def replace_link(match: re.Match) -> str:
        links.append(match.group(1))
        return f"(read more) __READ_MORE_LINK_{len(links)}__"

    prompt_digest = re.sub(
        r"\(read more\)\s+(https?://\S+)",
        replace_link,
        base_digest,
    )

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You polish a concise plain-text morning digest for Telegram. "
                    "Keep all section headings exactly as provided. Preserve every "
                    "'(read more) URL' line exactly, including its URL and position. "
                    "Keep it warm, practical, short, and do not invent facts."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Polish this digest and improve the Suggested priorities based only on the facts present. "
                    "Return only the final digest.\n\n"
                    f"{prompt_digest}"
                ),
            },
        ],
        temperature=0.4,
        max_tokens=900,
    )
    polished_digest = response.choices[0].message.content.strip()

    for index, link in enumerate(links, start=1):
        placeholder = f"__READ_MORE_LINK_{index}__"
        if placeholder not in polished_digest:
            raise ValueError("OpenAI response removed a news link")
        polished_digest = polished_digest.replace(placeholder, link)

    return polished_digest
