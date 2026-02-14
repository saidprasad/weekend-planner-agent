"""
Flask API for the weekend outdoor activity recommendation agent.
"""

from __future__ import annotations

import os
from typing import Optional

from flask import Flask, request, jsonify

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from agent import get_weekend_recommendation

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    """Liveness/readiness check for GCP Cloud Run."""
    return jsonify({"status": "ok"}), 200


@app.route("/recommend", methods=["GET", "POST"])
def recommend():
    """
    Get weekend outdoor activity recommendations for a location.

    GET:  /recommend?location=San+Francisco&model=gpt-4o-mini
    POST: body {"location": "San Francisco", "model": "gpt-4o-mini"} (model optional)
    """
    if request.method == "GET":
        location = request.args.get("location")
        model = request.args.get("model") or None
    else:
        body = request.get_json(silent=True) or {}
        location = body.get("location")
        model = body.get("model")

    if not location or not str(location).strip():
        return jsonify({
            "error": "Missing required field: location",
            "usage": "GET /recommend?location=San+Francisco or POST /recommend with JSON {\"location\": \"San Francisco\"}",
        }), 400

    location = str(location).strip()
    model = str(model).strip() if model else None

    try:
        recommendation = get_weekend_recommendation(location, model=model)
        return jsonify({"location": location, "recommendation": recommendation}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "0") == "1")
