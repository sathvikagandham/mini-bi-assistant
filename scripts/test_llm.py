"""
Confirm the Groq API key works and the LLM classifies correctly.

Run:
    python scripts/test_llm.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config
from app.llm_client import classify_with_llm
from app.intents import classify


def main() -> int:
    print(f"LLM provider: {config.LLM_PROVIDER}")
    key_preview = config.GROQ_API_KEY[:7] + "..." if config.GROQ_API_KEY else "(MISSING)"
    print(f"GROQ_API_KEY: {key_preview}")

    if not config.GROQ_API_KEY or config.GROQ_API_KEY == "your-groq-key-here":
        print("\n❌ GROQ_API_KEY is not set in .env")
        return 1

    print("\n--- Direct LLM classification ---")
    test_questions = [
        "What is the total revenue?",
        "Which product generated the highest revenue?",
        "What is the monthly revenue trend?",
        "Which region generated the highest sales?",
        "How did revenue change between January and June?",
        "Can you suggest a marketing strategy?",
    ]
    for q in test_questions:
        result = classify_with_llm(q)
        status = result if result else "FAILED (would fall back to rules)"
        print(f"  Q: {q}\n     → {status}\n")

    print("--- Full classify() pipeline (LLM → rules fallback) ---")
    for q in test_questions:
        print(f"  Q: {q}\n     → {classify(q)}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())