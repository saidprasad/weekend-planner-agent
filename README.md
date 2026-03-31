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

## Deploy to GCP (Cloud Run)

**Where to add your Google Cloud project details:**

1. **Option A – Environment variable (recommended)**  
   In `.env` (or your shell), set:
   ```bash
   GCP_PROJECT_ID=your-google-cloud-project-id
   ```
   Then run `./deploy.sh`; it uses `GCP_PROJECT_ID` for the deploy.

2. **Option B – gcloud default**  
   Set the active project once:
   ```bash
   gcloud config set project your-google-cloud-project-id
   ```
   Then run `./deploy.sh` (it will use the configured project if `GCP_PROJECT_ID` is not set).

3. **Option C – Per-command**  
   Pass the project on each deploy:
   ```bash
   gcloud run deploy weekend-planner-api --project=your-project-id --source=. --region=us-central1 --allow-unauthenticated
   ```

**Steps:**

1. Install [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) and run `gcloud auth login` and `gcloud auth application-default login`.
2. Enable APIs: `gcloud services enable run.googleapis.com cloudbuild.googleapis.com --project=YOUR_PROJECT_ID`
3. Set `GCP_PROJECT_ID` in `.env` (see `.env.example`) or run `gcloud config set project YOUR_PROJECT_ID`.
4. Run `./deploy.sh`. After the first deploy, set `OPENAI_API_KEY` in the Cloud Run console (Edit & deploy → Variables and secrets).

Optional: set `GCP_REGION` (default `us-central1`) or `GCP_SERVICE_NAME` (default `weekend-planner-api`) before running `deploy.sh`.

## Tests

Install dependencies (including pytest), then run:

```bash
pip install -r requirements.txt
python -m pytest
```

Tests cover: `weather` (geocode, get_forecast, weather_summary with mocked HTTP), `agent` (weekend selection, recommend with mocked OpenAI, get_weekend_recommendation), and the CLI in `main.py`.

## License

Use and modify as you like. Weather data from Open-Meteo; see their terms for usage.
