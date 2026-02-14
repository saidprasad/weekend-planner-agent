"""Unit tests for agent module (weekend selection, recommend, get_weekend_recommendation)."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from weather import Location, DayForecast
from agent import (
    RecommendationInput,
    _weekend_forecast,
    recommend,
    get_weekend_recommendation,
)


def _forecast_for_dates(dates: list[str]) -> list[DayForecast]:
    """Build minimal DayForecast list for given ISO dates."""
    return [
        DayForecast(date=d, temp_max_c=15.0, temp_min_c=5.0, precipitation_mm=0.0, weather_code=0)
        for d in dates
    ]


# --- _weekend_forecast ---


def test_weekend_forecast_picks_saturday_sunday():
    # 2026-02-14 is Sat, 2026-02-15 is Sun
    forecast = _forecast_for_dates(
        ["2026-02-12", "2026-02-13", "2026-02-14", "2026-02-15", "2026-02-16", "2026-02-17", "2026-02-18"]
    )
    weekend = _weekend_forecast(forecast)
    assert len(weekend) == 2
    assert weekend[0].date == "2026-02-14"
    assert weekend[1].date == "2026-02-15"


def test_weekend_forecast_only_weekdays_falls_back_to_first_two():
    # Mon–Fri only
    forecast = _forecast_for_dates(
        ["2026-02-09", "2026-02-10", "2026-02-11", "2026-02-12", "2026-02-13"]
    )
    weekend = _weekend_forecast(forecast)
    assert len(weekend) == 2
    assert weekend[0].date == "2026-02-09"
    assert weekend[1].date == "2026-02-10"


def test_weekend_forecast_empty_falls_back():
    forecast = _forecast_for_dates(["2026-02-09", "2026-02-10"])
    weekend = _weekend_forecast(forecast)
    assert len(weekend) == 2
    assert weekend[0].date == "2026-02-09" and weekend[1].date == "2026-02-10"


def test_weekend_forecast_single_day_returns_one():
    forecast = _forecast_for_dates(["2026-02-14"])  # Saturday
    weekend = _weekend_forecast(forecast)
    assert len(weekend) == 1
    assert weekend[0].date == "2026-02-14"


# --- recommend (mocked OpenAI client) ---


@pytest.fixture
def sample_location():
    return Location(
        name="San Francisco",
        latitude=37.77,
        longitude=-122.42,
        timezone="America/Los_Angeles",
        country="United States",
        admin1="California",
    )


@pytest.fixture
def sample_input(sample_location):
    weekend = _forecast_for_dates(["2026-02-14", "2026-02-15"])
    forecast = _forecast_for_dates(
        ["2026-02-12", "2026-02-13", "2026-02-14", "2026-02-15", "2026-02-16", "2026-02-17", "2026-02-18"]
    )
    return RecommendationInput(location=sample_location, forecast=forecast, weekend_days=weekend)


def test_recommend_returns_message_content(sample_input):
    mock_choice = MagicMock()
    mock_choice.message.content = "Try hiking in Golden Gate Park."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("agent._get_client", return_value=mock_client):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=False):
            result = recommend(sample_input, model="gpt-4o-mini")
    assert result == "Try hiking in Golden Gate Park."
    mock_client.chat.completions.create.assert_called_once()
    call_kw = mock_client.chat.completions.create.call_args[1]
    assert call_kw["model"] == "gpt-4o-mini"
    assert len(call_kw["messages"]) == 1
    assert "San Francisco" in call_kw["messages"][0]["content"]
    assert "2026-02-14" in call_kw["messages"][0]["content"]


def test_recommend_empty_content_returns_empty_string(sample_input):
    mock_choice = MagicMock()
    mock_choice.message.content = None
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("agent._get_client", return_value=mock_client):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=False):
            result = recommend(sample_input)
    assert result == ""


def test_get_client_raises_without_api_key():
    from agent import _get_client
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        with pytest.raises(ValueError) as exc_info:
            _get_client()
        assert "OPENAI_API_KEY" in str(exc_info.value)


# --- get_weekend_recommendation (mocked geocode, get_forecast, recommend) ---


def test_get_weekend_recommendation_unknown_location():
    with patch("agent.geocode", return_value=[]):
        result = get_weekend_recommendation("Nowhereville")
    assert "Could not find a location" in result
    assert "Nowhereville" in result


def test_get_weekend_recommendation_success():
    loc = Location(
        name="London",
        latitude=51.51,
        longitude=-0.13,
        timezone="Europe/London",
        country="United Kingdom",
        admin1="England",
    )
    forecast = _forecast_for_dates(
        ["2026-02-12", "2026-02-13", "2026-02-14", "2026-02-15", "2026-02-16", "2026-02-17", "2026-02-18"]
    )

    with patch("agent.geocode", return_value=[loc]):
        with patch("agent.get_forecast", return_value=forecast):
            with patch("agent.recommend", return_value="Visit Hyde Park and the South Bank.") as rec_mock:
                result = get_weekend_recommendation("London")
    assert result == "Visit Hyde Park and the South Bank."
    rec_mock.assert_called_once()
    input_data = rec_mock.call_args[0][0]
    assert input_data.location.name == "London"
    assert len(input_data.weekend_days) == 2
    assert input_data.weekend_days[0].date == "2026-02-14"
    assert input_data.weekend_days[1].date == "2026-02-15"


def test_get_weekend_recommendation_passes_model():
    loc = Location(
        name="Paris",
        latitude=48.85,
        longitude=2.35,
        timezone="Europe/Paris",
        country="France",
        admin1=None,
    )
    forecast = _forecast_for_dates(
        ["2026-02-12", "2026-02-13", "2026-02-14", "2026-02-15", "2026-02-16", "2026-02-17", "2026-02-18"]
    )

    with patch("agent.geocode", return_value=[loc]):
        with patch("agent.get_forecast", return_value=forecast):
            with patch("agent.recommend", return_value="Seine cruise.") as rec_mock:
                get_weekend_recommendation("Paris", model="gpt-4o")
    rec_mock.assert_called_once()
    assert rec_mock.call_args[1]["model"] == "gpt-4o"
