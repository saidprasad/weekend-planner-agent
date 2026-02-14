# Weekend Planner Agent

An AI agent that recommends **weekend outdoor activities** based on your **location** and **local weather conditions**. It uses real weather data (Open-Meteo) and an LLM to suggest activities that fit the forecast.

## Features

- **Location-aware**: Enter a city name, region, or postal code; the agent resolves it and fetches local weather.
- **Weather-driven**: Uses the upcoming weekend forecast (temperature, precipitation) to tailor suggestions.
- **Outdoor focus**: Suggests activities that suit the conditions (e.g. hiking in dry weather, covered options when it rains).

## Setup

1. **Clone and install dependencies**

   ```bash
   cd weekend-planner-agent
   python3 -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set your OpenAI API key**

   Get a key at [OpenAI API keys](https://platform.openai.com/api-keys), then:

   ```bash
   cp .env.example .env
   # Edit .env and set OPENAI_API_KEY=sk-...
   ```

   Or export in your shell:

   ```bash
   export OPENAI_API_KEY=sk-...
   ```

   Weather and geocoding use [Open-Meteo](https://open-meteo.com/) and do **not** require an API key.

## Usage

From the project root:

```bash
python main.py "San Francisco"
python main.py "London"
python main.py "90210"
```

Optional: use a different model (default is `gpt-4o-mini`):

```bash
python main.py "Tokyo" --model gpt-4o
```

## Project layout

| File        | Purpose |
|------------|---------|
| `weather.py` | Geocoding and weather forecast via Open-Meteo (free, no key). |
| `agent.py`   | Recommendation logic: builds prompt from location + weekend forecast, calls OpenAI. |
| `main.py`    | CLI: accepts a location string and prints the recommendation. |

## Environment variables

| Variable        | Required | Description |
|----------------|----------|-------------|
| `OPENAI_API_KEY` | Yes      | OpenAI API key for the recommendation LLM. |
| `OPENAI_MODEL`   | No       | Model name (default: `gpt-4o-mini`). |

## Tests

Install dependencies (including pytest), then run:

```bash
pip install -r requirements.txt
python -m pytest
```

Tests cover: `weather` (geocode, get_forecast, weather_summary with mocked HTTP), `agent` (weekend selection, recommend with mocked OpenAI, get_weekend_recommendation), and the CLI in `main.py`.

## License

Use and modify as you like. Weather data from Open-Meteo; see their terms for usage.
