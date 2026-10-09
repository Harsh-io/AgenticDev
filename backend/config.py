import os

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# OPENAI (primary model)
# ============================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LangChain ChatOpenAI uses bare model names (no "openai/" prefix)
_raw_openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_MODEL = _raw_openai_model.replace("openai/", "")


# ============================================================
# GROQ (fallback model)
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


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

if not OPENAI_API_KEY:

    raise RuntimeError(
        "OPENAI_API_KEY is not set. "
        "Create a .env file in the backend directory."
    )

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY