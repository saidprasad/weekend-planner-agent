"""
Student Rank REST API
=====================

A small FastAPI service that:

1. Loads `students.csv` once at startup
2. Sorts students by score (descending) and assigns each a rank
3. Exposes `POST /rank` which returns a student's rank when given
   either a `student_id` or a `name` in the JSON body

Run locally:

    uvicorn main:app --reload

Then open http://127.0.0.1:8000/docs for the interactive Swagger UI.
"""

from __future__ import annotations

import csv
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Pydantic models
#
# Pydantic models describe the *shape* of data flowing in and out of the API.
# FastAPI uses them to:
#   - validate incoming JSON (returning HTTP 422 automatically on failure)
#   - serialize outgoing responses
#   - generate the OpenAPI schema you see at /docs
# ---------------------------------------------------------------------------


class RankQuery(BaseModel):
    """Incoming request body. Caller must provide exactly one of the fields."""

    student_id: str | None = Field(
        default=None,
        description="Unique student identifier, e.g. 'S003'.",
        examples=["S003"],
    )
    name: str | None = Field(
        default=None,
        description="Full student name (case-insensitive match).",
        examples=["Alice Kumar"],
    )

    @model_validator(mode="after")
    def exactly_one_field(self) -> "RankQuery":
        # XOR: provide one OR the other, not both, not neither.
        if bool(self.student_id) == bool(self.name):
            raise ValueError("Provide exactly one of 'student_id' or 'name'.")
        return self


class RankResponse(BaseModel):
    """Outgoing response body."""

    student_id: str
    name: str
    score: float
    rank: int = Field(description="1 = highest score.")
    total_students: int


# ---------------------------------------------------------------------------
# Data loading
#
# We load and rank the CSV exactly once, when the app starts up, and hold the
# result in memory. For a teaching example this is plenty; in production you'd
# usually read from a database on each request (or cache with TTL).
# ---------------------------------------------------------------------------


CSV_PATH = Path(__file__).parent / "students.csv"

# Module-level list, populated by the lifespan handler below.
ranked: list[dict] = []


def _load_and_rank(csv_path: Path) -> list[dict]:
    """Read the CSV, sort by score descending, attach a 1-based rank to each row.

    Ties are broken by the order they appear after sorting (Python's sort is
    stable). See the README "Exercises" section for how to implement
    competition-style or dense ranking instead.
    """
    with csv_path.open(newline="") as f:
        rows = [
            {
                "student_id": row["student_id"],
                "name": row["name"],
                "score": float(row["score"]),
            }
            for row in csv.DictReader(f)
        ]

    rows.sort(key=lambda r: r["score"], reverse=True)
    for i, row in enumerate(rows, start=1):
        row["rank"] = i
    return rows


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: code before `yield` runs on startup, after on shutdown."""
    ranked.extend(_load_and_rank(CSV_PATH))
    yield
    ranked.clear()


# ---------------------------------------------------------------------------
# The app
# ---------------------------------------------------------------------------


app = FastAPI(
    title="Student Rank API",
    description=(
        "Tiny teaching API. POST a student_id or name and get back their rank "
        "computed from `students.csv`."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness probe. Useful for Docker/Kubernetes and quick smoke tests."""
    return {"status": "ok", "students_loaded": len(ranked)}


@app.post("/rank", response_model=RankResponse, tags=["rank"])
def get_rank(query: RankQuery) -> RankResponse:
    """Return the rank of a single student.

    Lookup is case-insensitive for names and exact-match for ids.
    Returns 404 when no matching student exists.
    """
    for row in ranked:
        matched_by_id = query.student_id and row["student_id"] == query.student_id
        matched_by_name = query.name and row["name"].lower() == query.name.lower()
        if matched_by_id or matched_by_name:
            return RankResponse(
                student_id=row["student_id"],
                name=row["name"],
                score=row["score"],
                rank=row["rank"],
                total_students=len(ranked),
            )

    raise HTTPException(status_code=404, detail="Student not found")
