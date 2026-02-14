#!/usr/bin/env python3
"""
CLI for the weekend outdoor activity recommendation agent.
Usage: python main.py "San Francisco"
       python main.py "London"
       python main.py "90210"
"""

from __future__ import annotations

import argparse
import sys

# Load .env if present (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from agent import get_weekend_recommendation


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Get AI-powered weekend outdoor activity recommendations based on location and local weather."
    )
    parser.add_argument(
        "location",
        type=str,
        help="City name, region, or postal code (e.g. 'San Francisco', 'London', '90210')",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="OpenAI model to use (default: gpt-4o-mini). Overrides OPENAI_MODEL env.",
    )
    args = parser.parse_args()

    try:
        recommendation = get_weekend_recommendation(args.location, model=args.model)
        print(recommendation)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
