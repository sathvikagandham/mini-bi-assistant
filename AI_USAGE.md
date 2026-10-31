# AI Usage & Debugging Document

## AI Tools Used
- **Groq API (Llama 3)**: Used for intent classification.
- **ChatGPT/Claude**: Used as coding assistants for boilerplate and debugging.

## How AI Was Used
- Generated the FastAPI boilerplate and Pydantic schemas.
- Helped write the Pandas 8-step cleaning pipeline.
- **Security**: AI is heavily constrained. The LLM only outputs JSON intents. SQL queries are pre-written and validated. The database is read-only.

## Problems Encountered & Debugged
1. **Proxy Network Timeout**: The college proxy blocked `api.groq.com`. Fixed by routing `httpx.Client` explicitly through the authenticated proxy `studentnet.rgukt.ac.in:3128` using `trust_env=False`.
2. **Retired Model**: `llama-3.1-8b-instant` was decommissioned. The app degraded gracefully to the rule-based layer. Fixed by updating `MODEL` to `openai/gpt-oss-20b`.
3. **PowerShell Quoting**: Nested SQL quotes failed in `python -c`. Fixed by moving verification logic into `scripts/verify.py`.
4. **Truncated LLM Response**: `max_tokens` was too low, cutting off JSON. Increased to 500.

## Known Limitations
- No multi-turn conversation memory.
- Rule-based fallback assumes year 2026 for month names.
- CORS is fully open for local dev.

## Future Improvements
- Use LangChain `create_sql_agent` for ad-hoc exploration.
- Add Docker for deployment.