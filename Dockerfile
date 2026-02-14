# Weekend Planner Agent API - for GCP Cloud Run
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Exclude dev/test deps for smaller image (optional: use requirements-prod.txt if you prefer)
RUN pip uninstall -y pytest 2>/dev/null || true

COPY weather.py agent.py app.py ./

# Cloud Run expects PORT env (default 8080)
ENV PORT=8080
EXPOSE 8080

# Run with gunicorn for production
CMD exec gunicorn --bind :${PORT} --workers 1 --threads 8 --timeout 120 app:app
