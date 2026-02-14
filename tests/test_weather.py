"""Unit tests for weather module (geocoding, forecast, weather_summary)."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
import requests

from weather import (
    GEOCODE_URL,
    FORECAST_URL,
    Location,
    DayForecast,
    geocode,
    get_forecast,
    weather_summary,
)


# --- weather_summary (pure function, no I/O) ---


def test_weather_summary_empty():
    assert weather_summary([]) == ""


def test_weather_summary_single_day_dry():
    fc = [DayForecast("2026-02-14", 18.0, 8.0, 0.0, 0)]
    assert weather_summary(fc) == "2026-02-14: 8–18°C, dry (0.0 mm)"


def test_weather_summary_single_day_rain():
    fc = [DayForecast("2026-02-15", 12.0, 5.0, 10.5, 80)]
    assert "rain/snow expected" in weather_summary(fc)
    assert "10.5 mm" in weather_summary(fc)


def test_weather_summary_precip_threshold():
    # exactly 0.5 mm is "dry" (condition is > 0.5)
    fc = [DayForecast("2026-02-16", 15.0, 7.0, 0.5, 3)]
    assert "dry" in weather_summary(fc)


def test_weather_summary_multiple_days():
    fc = [
        DayForecast("2026-02-14", 18.0, 8.0, 0.0, 0),
        DayForecast("2026-02-15", 12.0, 5.0, 2.0, 61),
    ]
    out = weather_summary(fc)
    assert "2026-02-14" in out and "2026-02-15" in out
    assert out.count("\n") == 1


# --- geocode (mocked HTTP) ---


def test_geocode_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "name": "San Francisco",
                "latitude": 37.77,
                "longitude": -122.42,
                "timezone": "America/Los_Angeles",
                "country": "United States",
                "admin1": "California",
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("weather.requests.get", return_value=mock_response) as get_mock:
        locations = geocode("San Francisco", count=1)
        assert len(locations) == 1
        loc = locations[0]
        assert loc.name == "San Francisco"
        assert loc.latitude == 37.77
        assert loc.longitude == -122.42
        assert loc.timezone == "America/Los_Angeles"
        assert loc.country == "United States"
        assert loc.admin1 == "California"
        get_mock.assert_called_once()
        call_kw = get_mock.call_args[1]
        assert call_kw["params"]["name"] == "San Francisco"
        assert call_kw["params"]["count"] == 1


def test_geocode_empty_results():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = MagicMock()

    with patch("weather.requests.get", return_value=mock_response):
        locations = geocode("Nowhereville")
        assert locations == []


def test_geocode_no_results_key():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_response.raise_for_status = MagicMock()

    with patch("weather.requests.get", return_value=mock_response):
        locations = geocode("Xyz")
        assert locations == []


def test_geocode_http_error():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")

    with patch("weather.requests.get", return_value=mock_response):
        with pytest.raises(requests.HTTPError):
            geocode("San Francisco")


# --- get_forecast (mocked HTTP) ---


def test_get_forecast_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "daily": {
            "time": ["2026-02-14", "2026-02-15"],
            "temperature_2m_max": [16.0, 14.0],
            "temperature_2m_min": [7.0, 6.0],
            "precipitation_sum": [0.0, 5.2],
            "weathercode": [0, 61],
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch("weather.requests.get", return_value=mock_response) as get_mock:
        forecasts = get_forecast(37.77, -122.42, "America/Los_Angeles", days=7)
        assert len(forecasts) == 2
        assert forecasts[0].date == "2026-02-14"
        assert forecasts[0].temp_max_c == 16.0
        assert forecasts[0].temp_min_c == 7.0
        assert forecasts[0].precipitation_mm == 0.0
        assert forecasts[0].weather_code == 0
        assert forecasts[1].precipitation_mm == 5.2
        get_mock.assert_called_once()
        call_kw = get_mock.call_args[1]
        assert call_kw["params"]["latitude"] == 37.77
        assert call_kw["params"]["longitude"] == -122.42
        assert call_kw["params"]["timezone"] == "America/Los_Angeles"
        assert call_kw["params"]["forecast_days"] == 7


def test_get_forecast_http_error():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404")

    with patch("weather.requests.get", return_value=mock_response):
        with pytest.raises(requests.HTTPError):
            get_forecast(0, 0, "UTC", days=7)
