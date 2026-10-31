"""
Groq LLM wrapper. Single responsibility: turn a question into an intent.
"""
import json
import os

import httpx
from groq import Groq

from app import config
from app.intents import SUPPORTED_INTENTS, extract_months

MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You are an intent classifier for a sales BI assistant.
Classify the user's question into EXACTLY one of these intents:

  total_revenue    - total revenue overall
  top_product      - which product generated the highest revenue
  monthly_trend    - revenue trend over months
  top_region       - which region generated the highest sales
  month_comparison - how revenue changed between two months
  unsupported      - anything else

If intent is "month_comparison", also extract two month codes in YYYY-MM format
into params as: {"month_a": "YYYY-MM", "month_b": "YYYY-MM"}.
If the user names months without a year, assume the year is 2026.
Otherwise params must be {}.

Return ONLY valid JSON. No markdown. No explanation. No extra text.

Example output: {"intent": "total_revenue", "params": {}}
Example output: {"intent": "month_comparison", "params": {"month_a": "2026-01", "month_b": "2026-06"}}
"""

_client = None

def _get_client():
    global _client
    if _client is None:
        if not config.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set in .env")

        proxy = (
            os.environ.get("HTTPS_PROXY")
            or os.environ.get("https_proxy")
            or os.environ.get("HTTP_PROXY")
            or os.environ.get("http_proxy")
        )

        if proxy:
            http_client = httpx.Client(
                proxy=proxy,
                timeout=15.0,
                trust_env=False,
            )
            _client = Groq(api_key=config.GROQ_API_KEY, http_client=http_client)
            print(f"[llm] Using proxy: {proxy.split('@')[-1]}")
        else:
            _client = Groq(api_key=config.GROQ_API_KEY)
            print("[llm] No proxy configured — using direct connection")

    return _client

def _is_valid_month(value) -> bool:
    import re
    if not isinstance(value, str):
        return False
    return bool(re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value))

def classify_with_llm(question: str) -> dict | None:
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0,
            max_tokens=500,
            timeout=10.0,
        )
    except Exception as e:
        print(f"[llm] Groq call failed: {type(e).__name__}: {e}")
        return None

    raw = (response.choices[0].message.content or "").strip()

    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        print(f"[llm] Non-JSON response: {raw[:200]!r}")
        return None

    if not isinstance(parsed, dict):
        return None

    intent = parsed.get("intent")
    params = parsed.get("params", {}) or {}

    if intent not in SUPPORTED_INTENTS:
        print(f"[llm] Rejected non-whitelist intent: {intent!r}")
        return None

    if intent == "month_comparison":
        ma, mb = params.get("month_a"), params.get("month_b")
        if not _is_valid_month(ma) or not _is_valid_month(mb):
            recovered = extract_months(question)
            if len(recovered) == 2:
                params = {"month_a": recovered[0], "month_b": recovered[1]}
            else:
                print(f"[llm] month_comparison missing valid months: {params}")
                return None

    if intent != "month_comparison":
        params = {}

    return {"intent": intent, "params": params}