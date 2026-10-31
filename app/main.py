"""
FastAPI backend for the Mini BI Assistant.

Endpoints:
  GET  /health   — liveness + row count
  POST /ask      — take a question, return answer + data + table

This step uses the RULE-BASED classifier only.
Step 4 will add the Groq LLM in front, keeping rules as fallback.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app import config
from app.analytics import format_answer
from app.db import get_readonly_connection, row_count
from app.intents import classify, SUPPORTED_INTENTS
from app.queries import run_query
from app.schemas import AskRequest, AskResponse


app = FastAPI(
    title="Mini AI BI Assistant",
    version="0.1.0",
    description="Ask natural-language questions about sales data.",
)

# CORS: allow Streamlit (localhost:8501) to call this API (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    """Redirect the root URL to the Swagger UI documentation."""
    return RedirectResponse(url="/docs")

@app.get("/health")
def health():
    """Liveness check + confirm DB is loaded."""
    return {"status": "ok", "rows_in_db": row_count()}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """
    Classify the question → run the matching SQL → format the answer.
    """
    # --- 1. Classify ---
    result = classify(req.question)
    intent = result["intent"]
    params = result.get("params", {})

    # --- 2. Guard: intent must be in the whitelist ---
    if intent not in SUPPORTED_INTENTS or intent == "unsupported":
        raise HTTPException(
            status_code=400,
            detail=(
                "Sorry, I couldn't understand that question. "
                "Try asking about: total revenue, top product, "
                "monthly trend, top region, or comparison between two months."
            ),
        )

    # --- 3. Query ---
    conn = get_readonly_connection()
    try:
        rows = run_query(conn, intent, params)
    except ValueError as e:
        # From run_query: bad intent, bad month format, missing params
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

    # --- 4. Format ---
    answer, data, supporting = format_answer(intent, rows, params)

    return AskResponse(
        answer=answer,
        intent=intent,
        data=data,
        supporting_table=supporting,
    )


@app.on_event("startup")
def _startup_banner():
    """Log one line at startup so you can see it in the uvicorn console."""
    print(f"[startup] DB: {config.DB_PATH}")
    try:
        print(f"[startup] Rows in DB: {row_count()}")
    except Exception as e:
        print(f"[startup] WARNING: DB not initialised ({e}) — run scripts/init_db.py")