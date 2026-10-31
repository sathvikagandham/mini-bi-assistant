"""
Intent definitions + rule-based classifier (LLM fallback).

Public API:
  - SUPPORTED_INTENTS  : set of allowed intent strings
  - classify_with_rules(question) -> {"intent": str, "params": dict}
  - extract_months(text) -> list[str]  (used by rules and by LLM validation)
"""
import re


SUPPORTED_INTENTS = {
    "total_revenue",
    "top_product",
    "monthly_trend",
    "top_region",
    "month_comparison",
    "unsupported",
}


# Map month names (and 3-letter abbreviations) to numeric months
_MONTH_NAMES = {
    "january": "01", "jan": "01",
    "february": "02", "feb": "02",
    "march": "03", "mar": "03",
    "april": "04", "apr": "04",
    "may": "05",
    "june": "06", "jun": "06",
    "july": "07", "jul": "07",
    "august": "08", "aug": "08",
    "september": "09", "sep": "09", "sept": "09",
    "october": "10", "oct": "10",
    "november": "11", "nov": "11",
    "december": "12", "dec": "12",
}

# Matches 4-digit-year + 2-digit-month, e.g. 2026-03
_YEAR_MONTH_PATTERN = re.compile(r"\b(\d{4}-\d{2})\b")

# Data year is 2026 — used only to build YYYY-MM from month names.
# Documented as a limitation of the rule-based fallback (the LLM handles
# arbitrary years). This is fine because this fallback only runs when the
# LLM is unavailable, and the dataset is fixed to 2026.
_DATA_YEAR = "2026"


def extract_months(text: str, max_months: int = 2) -> list[str]:
    """
    Extract YYYY-MM month codes from free text.

    Handles both formats:
      - explicit:  "between 2026-01 and 2026-03"
      - names:     "between January and March"

    Returns at most `max_months` unique codes, in order of appearance.
    """
    found: list[str] = []

    # Pass 1: explicit YYYY-MM codes
    for m in _YEAR_MONTH_PATTERN.findall(text):
        if m not in found:
            found.append(m)

    # Pass 2: month names (only if we still need more)
    if len(found) < max_months:
        for word in re.findall(r"\b[a-z]+\b", text.lower()):
            if word in _MONTH_NAMES:
                code = f"{_DATA_YEAR}-{_MONTH_NAMES[word]}"
                if code not in found:
                    found.append(code)
                    if len(found) >= max_months:
                        break

    return found[:max_months]


def classify_with_rules(question: str) -> dict:
    """
    Keyword-based intent classifier — fallback when the LLM is unavailable.

    Returns {"intent": <label>, "params": {...}}.
    Never raises — always returns a valid intent (at worst "unsupported").
    """
    q = question.lower().strip()

        # --- month_comparison: highest priority, needs two months ---
    # Extract months FIRST, then check if any comparison cue is present.
    # We do NOT require the literal word "month" — real users write
    # "between January and June", not "between two months".
    months = extract_months(question)
    comparison_cues = (
        "compare" in q
        or "comparison" in q
        or "change" in q
        or "difference" in q
        or "between" in q
    )
    if comparison_cues and len(months) == 2:
        return {
            "intent": "month_comparison",
            "params": {"month_a": months[0], "month_b": months[1]},
        }

    # --- total_revenue ---
    if ("total" in q or "overall" in q) and "revenue" in q:
        return {"intent": "total_revenue", "params": {}}

    # --- top_product ---
    if "product" in q and any(w in q for w in ("highest", "top", "best", "most")):
        return {"intent": "top_product", "params": {}}

    # --- monthly_trend ---
    if ("monthly" in q and ("trend" in q or "revenue" in q)) or "by month" in q:
        return {"intent": "monthly_trend", "params": {}}

    # --- top_region ---
    if "region" in q and any(w in q for w in ("highest", "top", "best", "most")):
        return {"intent": "top_region", "params": {}}

    return {"intent": "unsupported", "params": {}}
def classify(question: str) -> dict:
    """
    Public classifier used by the API.

    Order:
      1. Try Groq (LLM). If it returns a valid intent, use it.
      2. Otherwise fall back to rule-based classification.

    This function never raises and always returns a valid intent.
    """
    # Lazy import avoids a circular dependency (llm_client imports intents)
    from app.llm_client import classify_with_llm

    llm_result = classify_with_llm(question)
    if llm_result is not None:
        print(f"[classify] LLM → {llm_result}")
        return llm_result

    rule_result = classify_with_rules(question)
    print(f"[classify] rules → {rule_result}")
    return rule_result