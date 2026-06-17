from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import requests


WEATHER_CODES = {
    0: "Clear sky",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Cloudy",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Dense drizzle",
    56: "Freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Rain showers",
    82: "Heavy rain showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Heavy thunderstorm with hail",
}


@dataclass
class WeatherReport:
    location_name: str
    temperature_c: float | None
    condition: str
    rain_chance: int | None
    wind_kmh: float | None
    practical_sentence: str


def fetch_weather(settings) -> WeatherReport:
    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": settings.latitude,
                "longitude": settings.longitude,
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "hourly": "precipitation_probability,wind_speed_10m",
                "forecast_days": 1,
                "timezone": settings.timezone,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        hourly = data.get("hourly", {})
        condition = WEATHER_CODES.get(current.get("weather_code"), "Weather unavailable")
        rain_chance = _current_or_max_probability(hourly)
        wind_kmh = current.get("wind_speed_10m")
        temperature = current.get("temperature_2m")

        return WeatherReport(
            location_name=settings.location_name,
            temperature_c=temperature,
            condition=condition,
            rain_chance=rain_chance,
            wind_kmh=wind_kmh,
            practical_sentence=_practical_sentence(temperature, rain_chance, wind_kmh, condition),
        )
    except Exception as exc:
        return WeatherReport(
            location_name=settings.location_name,
            temperature_c=None,
            condition="Weather unavailable",
            rain_chance=None,
            wind_kmh=None,
            practical_sentence="Weather service could not be reached; check the forecast before heading out.",
        )


def _current_or_max_probability(hourly: dict) -> int | None:
    probabilities = hourly.get("precipitation_probability") or []
    times = hourly.get("time") or []
    if not probabilities:
        return None

    current_hour = datetime.now().strftime("%Y-%m-%dT%H:00")
    if current_hour in times:
        index = times.index(current_hour)
        return probabilities[index]

    return max(probabilities[:12]) if probabilities else None


def _practical_sentence(
    temperature_c: float | None,
    rain_chance: int | None,
    wind_kmh: float | None,
    condition: str,
) -> str:
    if rain_chance is not None and rain_chance >= 60:
        return "Carry a light rain layer if you are out for long."
    if wind_kmh is not None and wind_kmh >= 30:
        return "Expect a breezy day, especially in exposed areas."
    if temperature_c is not None and temperature_c >= 27:
        return "Good morning for errands or a run before the day heats up."
    if "Clear" in condition or "clear" in condition or "cloud" in condition.lower():
        return "Good morning for a walk or run before the day gets busy."
    return "A steady day for simple plans; check again before heading out."
