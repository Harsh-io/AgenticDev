"""
langgraph_app/agents/llm.py

Builds the shared LLM with OpenAI as primary and Groq as fallback.
Falls back transparently when the primary model is overloaded or errors.
"""

from __future__ import annotations

import logging

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

from config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
)


logger = logging.getLogger("vibecode.llm")


def build_llm(temperature: float = 0.3):
    """
    Returns a ChatOpenAI instance with Groq as a fallback.

    If GROQ_API_KEY is not set, fallback is skipped and only
    the primary OpenAI model is used.
    """

    primary = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=temperature,
        timeout=120,
    )

    if GROQ_API_KEY:
        fallback = ChatGroq(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            temperature=temperature,
            timeout=120,
        )

        logger.info(
            "LLM configured: primary=%s, fallback=%s",
            OPENAI_MODEL,
            GROQ_MODEL,
        )

        return primary.with_fallbacks([fallback])

    logger.info(
        "LLM configured: primary=%s (no Groq fallback)",
        OPENAI_MODEL,
    )

    return primary
