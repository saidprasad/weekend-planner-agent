"""
Weather and geocoding via Open-Meteo (free, no API key required).
"""

from __future__ import annotations

import requests
from dataclasses import dataclass
from typing import Optional


GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class Location:
    """Resolved location from geocoding."""

    name: str
    latitude: float
    longitude: float
    timezone: str
    country: str
    admin1: Optional[str] = None


@dataclass
class DayForecast:
    """Daily weather summary for one day."""

    date: str
    temp_max_c: float
    temp_min_c: float
    precipitation_mm: float
    weather_code: int  # WMO code


def geocode(location_query: str, count: int = 1) -> list[Location]:
    """
    Resolve a place name or postal code to coordinates and timezone.
    Returns a list of matching locations (best match first).
    """
    resp = requests.get(
        GEOCODE_URL,
        params={"name": location_query, "count": count, "language": "en"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results") or []
    return [
        Location(
            name=r["name"],
            latitude=r["latitude"],
            longitude=r["longitude"],
            timezone=r["timezone"],
            country=r["country"],
            admin1=r.get("admin1"),
        )
        for r in results
    ]


def get_forecast(latitude: float, longitude: float, timezone: str, days: int = 7) -> list[DayForecast]:
    """
    Fetch daily forecast for the next `days` days (includes weekend).
    """
    resp = requests.get(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "forecast_days": days,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    daily = data["daily"]
    n = len(daily["time"])
    return [
        DayForecast(
            date=daily["time"][i],
            temp_max_c=daily["temperature_2m_max"][i],
            temp_min_c=daily["temperature_2m_min"][i],
            precipitation_mm=daily["precipitation_sum"][i],
            weather_code=daily["weathercode"][i],
        )
        for i in range(n)
    ]


def weather_summary(forecasts: list[DayForecast]) -> str:
    """
    Build a human/LLM-friendly summary of the forecast (e.g. for weekend days).
    """
    lines = []
    for d in forecasts:
        precip = "rain/snow expected" if d.precipitation_mm > 0.5 else "dry"
        lines.append(
            f"{d.date}: {d.temp_min_c:.0f}–{d.temp_max_c:.0f}°C, {precip} ({d.precipitation_mm:.1f} mm)"
        )
    return "\n".join(lines)
