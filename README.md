# Mini AI Business Intelligence Assistant

A working prototype that answers natural-language questions about sales data using a secure, two-layer AI architecture.

## Setup
1. `python -m venv .venv`
2. `.\.venv\Scripts\Activate.ps1` (Windows)
3. `pip install -r requirements.txt`
4. Set `GROQ_API_KEY` in `.env` (copy `.env.example`)
5. `python scripts/init_db.py` (loads CSV to SQLite)

## Run
Terminal 1 (Backend): `uvicorn app.main:app --reload`
Terminal 2 (Frontend): `streamlit run ui/streamlit_app.py`
API Docs: `http://127.0.0.1:8000/docs`

## Architecture
- **CSV -> SQLite**: Cleaned via Pandas (48 valid rows, 3 excluded: Returned, Zero-Qty, Missing Price).
- **Backend (FastAPI)**: `POST /ask` endpoint validates input via Pydantic.
- **AI Layer (Groq)**: `llama-3.1-8b-instant` (or `gpt-oss-20b`) classifies intent into whitelisted categories. **LLM never writes SQL**.
- **Fallback**: Rule-based keyword classifier if LLM fails.
- **Database**: Queried via read-only SQLite connection (`?mode=ro`). Destructive queries are impossible.

## Testing
Run `pytest tests/test_api.py -v`.