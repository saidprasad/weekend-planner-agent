"""
Tests for the Student Rank API.

`fastapi.testclient.TestClient` lets us call the app in-process, so we don't
need a running uvicorn server. The `with TestClient(app) as client:` form is
important: it triggers the lifespan handler, which is what loads our CSV.
"""

from fastapi.testclient import TestClient

from main import app


# Top-3 expected from students.csv:
#   1. Mei Chen      (S005, 95.0)
#   2. Alice Kumar   (S003, 92.5)
#   3. Sofia Rossi   (S009, 90.0)
# Total students in the file: 10


def test_health() -> None:
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["students_loaded"] == 10


def test_lookup_by_id_returns_correct_rank() -> None:
    with TestClient(app) as client:
        resp = client.post("/rank", json={"student_id": "S005"})
    assert resp.status_code == 200
    assert resp.json() == {
        "student_id": "S005",
        "name": "Mei Chen",
        "score": 95.0,
        "rank": 1,
        "total_students": 10,
    }


def test_lookup_by_name_is_case_insensitive() -> None:
    with TestClient(app) as client:
        resp = client.post("/rank", json={"name": "alice kumar"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["student_id"] == "S003"
    assert body["rank"] == 2


def test_unknown_student_returns_404() -> None:
    with TestClient(app) as client:
        resp = client.post("/rank", json={"student_id": "S999"})
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Student not found"}


def test_empty_payload_returns_422() -> None:
    with TestClient(app) as client:
        resp = client.post("/rank", json={})
    assert resp.status_code == 422


def test_both_fields_returns_422() -> None:
    with TestClient(app) as client:
        resp = client.post(
            "/rank",
            json={"student_id": "S001", "name": "Anita Rao"},
        )
    assert resp.status_code == 422
