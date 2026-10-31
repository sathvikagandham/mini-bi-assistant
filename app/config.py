"""
Central configuration.

Loads environment variables from .env (project root)
and resolves all paths to absolute, so scripts work
regardless of the current working directory.
"""
from pathlib import Path
import os

from dotenv import load_dotenv

# Project root = parent of app/ (i.e. mini-bi-assistant/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env once, at import time
load_dotenv(PROJECT_ROOT / ".env")

# --- LLM Configuration ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# --- Paths (absolute, resolved) ---
DB_PATH  = PROJECT_ROOT / os.getenv("DB_PATH",  "data/sales.db")
CSV_PATH = PROJECT_ROOT / os.getenv("CSV_PATH", "data/sales.csv")