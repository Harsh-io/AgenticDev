import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


# ============================================================
# GROQ (sole inference provider)
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")


# ============================================================
# FRONTEND
# ============================================================

FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN",
    "http://localhost:5173",
)


# ============================================================
# VALIDATION
# ============================================================

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. "
        "Please configure GROQ_API_KEY in your .env file."
    )

os.environ["GROQ_API_KEY"] = GROQ_API_KEY
os.environ["GROQ_MODEL"] = GROQ_MODEL