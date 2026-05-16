# Student Rank REST API — a teaching walkthrough

A tiny but complete FastAPI service. You give it a student's `student_id` or
`name` in a JSON body, and it tells you that student's rank (and score, and
the total class size).

By the time you reach the end of this README you should understand:

- what a REST API actually is
- how FastAPI turns a Python function into an HTTP endpoint
- how Pydantic gives you free request validation and auto-generated docs
- what HTTP status codes 200, 404, and 422 mean and when each fires
- how to run a server locally and test it with `curl` and Swagger UI

---

## 1. What is a REST API?

A **REST API** is just a contract between a client (a browser, a mobile app,
another service) and a server, expressed over HTTP. Five ideas matter:

1. **Resources.** Anything addressable: a student, a rank, a list of students.
   Each resource has a URL, e.g. `/students/S003`.
2. **Verbs.** HTTP methods describe the *action* on a resource:
   - `GET` — read (must be safe and side-effect-free)
   - `POST` — create, or invoke an action with a payload
   - `PUT` / `PATCH` — replace / partially update
   - `DELETE` — remove
3. **Representations.** The wire format is usually JSON. The client sends JSON
   in the request body, the server sends JSON in the response body.
4. **Status codes.** Three-digit numbers that tell you what happened:
   - `2xx` success (e.g. `200 OK`, `201 Created`)
   - `4xx` the *client* did something wrong (e.g. `404 Not Found`,
     `422 Unprocessable Entity` for bad input)
   - `5xx` the *server* broke (e.g. `500 Internal Server Error`)
5. **Statelessness.** Each request stands alone. The server doesn't remember
   the previous request from the same client. (Sessions/auth are layered on
   top via tokens or cookies.)

That's it. "REST" is mostly a vocabulary and a few conventions; nothing more.

---

## 2. Why FastAPI?

[FastAPI](https://fastapi.tiangolo.com/) is a modern Python web framework. Its
killer feature for learning is that **your Python type hints become your API
contract**:

- Type-annotate a request body as a Pydantic model → FastAPI validates
  incoming JSON for free and returns a clean `422` if it's malformed.
- Type-annotate the response → FastAPI serializes it for you.
- All of this is reflected in an auto-generated OpenAPI schema, which
  FastAPI serves as a **live, clickable Swagger UI at `/docs`**. You can try
  the API from a web page without writing any client code.

---

## 3. Project layout

```
student-rank-api/
├── README.md          # this file
├── requirements.txt   # fastapi, uvicorn, pytest, httpx
├── students.csv       # sample data (10 rows)
├── main.py            # the API
└── test_main.py       # pytest tests using FastAPI's TestClient
```

The data:

```csv
student_id,name,score
S001,Anita Rao,88.0
S002,Ben Carter,75.5
S003,Alice Kumar,92.5
...
```

Rank is computed at startup by sorting all rows by `score` descending and
assigning rank 1 to the highest, rank 2 to the next, and so on.

---

## 4. Walking through `main.py`

### 4a. The request model

```python
class RankQuery(BaseModel):
    student_id: str | None = None
    name: str | None = None

    @model_validator(mode="after")
    def exactly_one_field(self) -> "RankQuery":
        if bool(self.student_id) == bool(self.name):
            raise ValueError("Provide exactly one of 'student_id' or 'name'.")
        return self
```

`BaseModel` is a Pydantic class. Two things to notice:

- Both fields default to `None`, so the caller may send either one.
- The `@model_validator` runs **after** the per-field validation has
  succeeded, and enforces the "exactly one of" rule across fields. If it
  raises, FastAPI converts the exception into a `422 Unprocessable Entity`
  response automatically.

### 4b. The response model

```python
class RankResponse(BaseModel):
    student_id: str
    name: str
    score: float
    rank: int
    total_students: int
```

This is what the client gets back. Declaring it as `response_model=RankResponse`
on the route tells FastAPI to:

- coerce the dict you return into this exact shape,
- strip any extra keys you accidentally include,
- and document the response in `/docs`.

### 4c. Loading the CSV at startup with `lifespan`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    ranked.extend(_load_and_rank(CSV_PATH))
    yield
    ranked.clear()

app = FastAPI(lifespan=lifespan)
```

Code before `yield` runs once when the app boots; code after `yield` runs
during shutdown. We only want to read and sort the CSV once, not on every
request. `ranked` is a module-level list that the route handler reads from.

### 4d. The route

```python
@app.post("/rank", response_model=RankResponse, tags=["rank"])
def get_rank(query: RankQuery) -> RankResponse:
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
```

Three small but important things:

1. The decorator `@app.post("/rank", ...)` tells FastAPI: when an HTTP
   `POST` arrives at the path `/rank`, call this function.
2. The single function parameter `query: RankQuery` is what makes
   FastAPI parse and validate the request body — purely from the type hint.
3. `raise HTTPException(status_code=404, ...)` is the idiomatic way to
   return an error response from anywhere in the call stack.

---

## 5. Run it

From inside `student-rank-api/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Uvicorn is the ASGI server that actually handles sockets and HTTP; FastAPI is
just the framework. `--reload` restarts on file changes — handy for learning.

Then visit **`http://127.0.0.1:8000/docs`** in your browser. You'll see the
interactive Swagger UI. Click `POST /rank` → "Try it out" → fill in the body
→ "Execute". This is the easiest way to play with the API.

### Or use `curl`

Look up by id:

```bash
curl -s -X POST http://127.0.0.1:8000/rank \
  -H "Content-Type: application/json" \
  -d '{"student_id":"S005"}'
```

Response:

```json
{"student_id":"S005","name":"Mei Chen","score":95.0,"rank":1,"total_students":10}
```

Look up by name (case-insensitive):

```bash
curl -s -X POST http://127.0.0.1:8000/rank \
  -H "Content-Type: application/json" \
  -d '{"name":"alice kumar"}'
```

```json
{"student_id":"S003","name":"Alice Kumar","score":92.5,"rank":2,"total_students":10}
```

Health check:

```bash
curl -s http://127.0.0.1:8000/health
```

```json
{"status":"ok","students_loaded":10}
```

---

## 6. Try breaking it (this is how you learn the status codes)

| What you send                                          | Status | Why                                             |
| ------------------------------------------------------ | -----: | ----------------------------------------------- |
| `{"student_id":"S005"}`                                |    200 | Happy path                                      |
| `{"student_id":"S999"}`                                |    404 | Valid request, but no such student              |
| `{}`                                                   |    422 | Failed the "exactly one of" validator           |
| `{"student_id":"S001","name":"Anita Rao"}`             |    422 | Both fields filled — same validator             |
| `{"student_id":123}`                                   |    422 | `student_id` must be a string                   |
| `not json at all`                                      |    422 | Body isn't parseable as JSON                    |

Notice the clear separation: **422 means the client sent something the server
couldn't even interpret as a valid request**, while **404 means the request
was valid but the resource doesn't exist**.

---

## 7. `GET /students/{id}/rank` vs `POST /rank` — which is "more REST"?

Strictly speaking, since this is a *read* operation, REST conventions prefer
`GET` with the identifier in the URL path:

```
GET /students/S005/rank
```

Reasons `GET` is "more correct" for reads:

- It's idempotent and cacheable.
- The resource is identifiable by URL, so it's bookmarkable / shareable.
- HTTP intermediaries (CDNs, proxies) can cache it.

We chose `POST /rank` because (a) you asked for "an input payload", and (b) it
lets us teach Pydantic body validation cleanly. In real systems `POST` is also
appropriate when:

- the input is too large or too sensitive to put in a URL (e.g. long search
  queries, free-text), or
- the operation has side effects (creating, mutating, charging, sending).

Both are valid. Knowing *why* you'd pick each is the actual lesson.

---

## 8. Run the tests

```bash
source .venv/bin/activate
python -m pytest -v
```

The test file uses `fastapi.testclient.TestClient`, which calls your app
**in-process** — no real HTTP, no port, no separate server. Note the
`with TestClient(app) as client:` form: entering the context manager triggers
the `lifespan` handler so the CSV actually loads before tests run.

---

## 9. Exercises (where to go next)

1. **Add `GET /students`** that returns the full ranked list. Practice
   pagination with `?limit=` and `?offset=` query parameters.
2. **Switch to competition ranking.** Right now two students with the same
   score get sequential ranks; change it so ties share a rank
   (1, 2, 2, 4, ...) — a.k.a. "competition rank" — or "dense rank"
   (1, 2, 2, 3, ...). Add tests for both.
3. **Add an in-memory index by id.** Replace the linear scan in `get_rank`
   with a `dict[str, dict]` lookup so `student_id` queries are O(1). Measure.
4. **Convert to `GET /students/{student_id}/rank`** (path param) and
   `GET /students/by-name/{name}/rank` (also path param), and compare the
   developer experience to the POST version.
5. **Add a `POST /students` endpoint** that accepts a new student and
   re-ranks the in-memory list. Now `POST` is genuinely the right verb —
   you're creating a resource. (Hint: `status_code=201`.)
6. **Add an API key.** Read a header `X-API-Key` via a FastAPI dependency
   and 401 if it's missing/wrong. Welcome to auth.

---

## File reference

- [main.py](main.py) — the API
- [test_main.py](test_main.py) — the tests
- [students.csv](students.csv) — the data
- [requirements.txt](requirements.txt) — pinned dependencies
