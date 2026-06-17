from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
import json
from zoneinfo import ZoneInfo


@dataclass
class CalendarEvent:
    start: str
    title: str


@dataclass
class CalendarResult:
    configured: bool
    events: list[CalendarEvent]
    message: str = ""


def fetch_today_events(settings) -> CalendarResult:
    if not settings.google_calendar_id or not settings.google_service_account_json:
        return CalendarResult(configured=False, events=[], message="No calendar configured yet.")

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        timezone = ZoneInfo(settings.timezone)
        today = datetime.now(timezone).date()
        start_of_day = datetime.combine(today, time.min, tzinfo=timezone).isoformat()
        end_of_day = datetime.combine(today, time.max, tzinfo=timezone).isoformat()

        info = json.loads(settings.google_service_account_json)
        credentials = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        )
        service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        result = (
            service.events()
            .list(
                calendarId=settings.google_calendar_id,
                timeMin=start_of_day,
                timeMax=end_of_day,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = [_parse_event(item, timezone) for item in result.get("items", [])]
        return CalendarResult(configured=True, events=[event for event in events if event])
    except Exception as exc:
        return CalendarResult(
            configured=False,
            events=[],
            message=f"Calendar is configured but could not be loaded: {exc}",
        )


def _parse_event(item: dict, timezone: ZoneInfo) -> CalendarEvent | None:
    title = item.get("summary", "Untitled event")
    start = item.get("start", {})

    if "dateTime" in start:
        start_dt = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00")).astimezone(timezone)
        start_text = start_dt.strftime("%H:%M")
    elif "date" in start:
        start_text = "All day"
    else:
        return None

    return CalendarEvent(start=start_text, title=title)
