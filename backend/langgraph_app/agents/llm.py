"""
langgraph_app/agents/llm.py

Builds the shared LLM using Groq as the sole inference provider.
"""

from __future__ import annotations

import logging

from langchain_groq import ChatGroq

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
)


logger = logging.getLogger("vibecode.llm")


def build_llm(temperature: float = 0.3) -> ChatGroq:
    """
    Returns a ChatGroq instance for agent inference.
    """
    logger.info(
        "LLM configured: provider=groq, model=%s, temperature=%.2f",
        GROQ_MODEL,
        temperature,
    )

    return ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=temperature,
        timeout=120,
    )
