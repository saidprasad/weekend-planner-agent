"""
AI agent that recommends weekend outdoor activities based on location and weather.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from openai import OpenAI

from weather import Location, DayForecast, weather_summary, geocode, get_forecast


@dataclass
class RecommendationInput:
    """Input for the recommendation agent."""

    location: Location
    forecast: list[DayForecast]
    weekend_days: list[DayForecast]  # subset of forecast (e.g. Sat + Sun)


def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. Create an API key at https://platform.openai.com/api-keys "
            "and set it in your environment or .env file."
        )
    return OpenAI(api_key=api_key)


def _weekend_forecast(forecast: list[DayForecast]) -> list[DayForecast]:
    """
    Return the weekend days from the forecast (Saturday and Sunday).
    Assumes forecast starts from today; we take the first Sat and Sun we find.
    """
    weekend = []
    for d in forecast:
        # ISO date: weekday 5=Saturday, 6=Sunday (Python: Monday=0)
        dt = datetime.strptime(d.date, "%Y-%m-%d")
        if dt.weekday() in (5, 6):
            weekend.append(d)
    # If we have at least 7 days we should get both; otherwise return up to 2 weekend days
    return weekend[:2] if weekend else forecast[:2]


def recommend(input_data: RecommendationInput, model: Optional[str] = None) -> str:
    """
    Call the LLM to generate weekend outdoor activity recommendations
    based on location and local weather.
    """
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    client = _get_client()

    location = input_data.location
    weekend = input_data.weekend_days
    summary = weather_summary(weekend)

    place = f"{location.name}, {location.admin1 or ''}, {location.country}".strip(", ")
    prompt = f"""You are a friendly weekend outdoor activity advisor. Given the location and local weather forecast for the weekend, suggest 3–5 specific outdoor activities that fit the conditions. Be concise and practical.

Location: {place}
Timezone: {location.timezone}

Weekend weather forecast:
{summary}

Consider:
- If it's dry and mild/warm: suggest hiking, biking, parks, beaches, outdoor dining, etc.
- If it's rainy or cold: suggest activities that are still possible (e.g. short walks, covered markets, indoor-outdoor options) or briefly note when to stay in.
- Tailor suggestions to the region (e.g. local parks, trails, or landmarks).
- Mention what to wear or bring (e.g. layers, umbrella) when relevant.

Respond in 1–2 short paragraphs. No bullet list unless you prefer it."""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )
    return response.choices[0].message.content or ""


def get_weekend_recommendation(
    location_query: str,
    model: Optional[str] = None,
) -> str:
    """
    One-shot: geocode location, fetch forecast, pick weekend days, and return
    AI-generated weekend activity recommendations.
    """
    locations = geocode(location_query)
    if not locations:
        return f"Could not find a location for: {location_query!r}. Try a city name or postal code."

    loc = locations[0]
    forecast = get_forecast(loc.latitude, loc.longitude, loc.timezone, days=7)
    weekend = _weekend_forecast(forecast)

    if not weekend:
        weekend = forecast[:2]

    input_data = RecommendationInput(location=loc, forecast=forecast, weekend_days=weekend)
    return recommend(input_data, model=model)
