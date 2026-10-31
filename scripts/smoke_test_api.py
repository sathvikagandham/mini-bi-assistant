"""
Smoke test: exercise the API end-to-end without a real HTTP server.

Uses FastAPI's TestClient (which runs the app in-process).
Not a substitute for pytest — those come in Phase 7 — but a quick
developer check after every code change.

Run:
    python scripts/smoke_test_api.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def show(label, resp):
    print(f"\n--- {label} ---")
    print(f"    Status: {resp.status_code}")
    print(f"    Body:   {resp.json()}")


def main() -> int:
    # 1. Health
    show("GET /health", client.get("/health"))

    # 2. Each supported question
    questions = [
        "What is the total revenue?",
        "Which product generated the highest revenue?",
        "What is the monthly revenue trend?",
        "Which region generated the highest sales?",
        "How did revenue change between January and June?",
    ]
    for q in questions:
        show(f"POST /ask  '{q}'", client.post("/ask", json={"question": q}))

    # 3. Unsupported question
    show("POST /ask  'tell me a joke'", client.post("/ask", json={"question": "tell me a joke"}))

    # 4. Invalid request (question too short)
    show("POST /ask  ''", client.post("/ask", json={"question": ""}))

    # 5. Comparison with only one month
    show(
        "POST /ask  'compare January'",
        client.post("/ask", json={"question": "compare January"}),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())