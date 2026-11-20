"""
langgraph_app/workflow/session_memory.py

Typed data models and helpers for agent workflow session memory.
"""

from typing import Any, TypedDict


class SessionEventRecord(TypedDict):
    author: str
    summary: str
    timestamp: str


class SessionMemoryState(TypedDict):
    session_id: str
    status: str
    events: list[SessionEventRecord]
    events_count: int
    state: dict[str, Any]

