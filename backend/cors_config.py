"""
backend/cors_config.py

Centralized and cleaned CORS configuration for AgenticDev API.
"""

from config import FRONTEND_ORIGIN

# Deduplicated, normalized allowed origin list
ALLOWED_ORIGINS = sorted(list({
    FRONTEND_ORIGIN,
    "https://vibe-web-ai.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
}))

ALLOWED_ORIGIN_REGEX = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

