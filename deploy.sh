#!/usr/bin/env bash
# Deploy the Weekend Planner API to Google Cloud Run.
# Set your project: export GCP_PROJECT_ID=your-project-id
# Or: gcloud config set project your-project-id

set -e
PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
if [[ -z "$PROJECT_ID" ]]; then
  echo "Error: GCP project not set. Use one of:"
  echo "  export GCP_PROJECT_ID=your-project-id"
  echo "  gcloud config set project your-project-id"
  exit 1
fi

SERVICE_NAME="${GCP_SERVICE_NAME:-weekend-planner-api}"
REGION="${GCP_REGION:-us-central1}"

echo "Deploying to project: $PROJECT_ID  service: $SERVICE_NAME  region: $REGION"
# Set OPENAI_API_KEY via Cloud Run console after first deploy, or use:
#   --set-secrets=OPENAI_API_KEY=openai-api-key:latest
# after creating the secret in Secret Manager.
gcloud run deploy "$SERVICE_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --source=. \
  --allow-unauthenticated

echo "Done. Set OPENAI_API_KEY in Cloud Run console (Edit & deploy → Variables) or via Secret Manager."
