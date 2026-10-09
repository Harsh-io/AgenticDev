"""
langgraph_app/workflow/runner.py

Async generator that drives the LangGraph workflow and streams
SSE-compatible event dicts to the FastAPI endpoint.

The runner exposes the workflow event stream consumed by the FastAPI endpoint.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator

from models import ProjectSnapshot

from langgraph_app.workflow.graph import get_compiled_graph, WorkflowState


logger = logging.getLogger("vibecode.langgraph.runner")


# ============================================================
# PROJECT CONTEXT BUILDER
# ============================================================

def _build_project_context(project: ProjectSnapshot | None) -> str:
    if project is None or not project.files:
        return ""

    files = [
        {"path": f.path, "content": f.content}
        for f in project.files
    ]

    return json.dumps(
        {
            "name": project.name,
            "framework": project.framework,
            "entrypoint": project.entrypoint,
            "files": files,
        },
        indent=2,
    )


# ============================================================
# MEMORY STORE
# ============================================================

_session_store: dict[str, dict[str, Any]] = {}


def _record_session_event(session_id: str, event: dict) -> None:
    if session_id not in _session_store:
        _session_store[session_id] = {"events": [], "status": "active"}

    _session_store[session_id]["events"].append(
        {
            "author": event.get("agent", "System"),
            "summary": event.get("message", "")[:150],
            "timestamp": event.get("timestamp", time.strftime("%H:%M:%S")),
        }
    )


async def get_session_memory(session_id: str) -> dict[str, Any]:
    """
    Returns lightweight session memory compatible with the frontend's
    Session memory panel.
    """
    store = _session_store.get(session_id)

    if store is None:
        return {
            "session_id": session_id,
            "status": "initialized",
            "events": [],
            "events_count": 0,
            "state": {},
        }

    events = store.get("events", [])

    return {
        "session_id": session_id,
        "status": "active",
        "events": events[-15:],
        "events_count": len(events),
        "state": {},
    }


# ============================================================
# MAIN WORKFLOW RUNNER
# ============================================================

async def run_langgraph_workflow(
    prompt: str,
    session_id: str,
    project: ProjectSnapshot | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Drive the LangGraph workflow and yield SSE event dicts.

    This generator is consumed by the FastAPI streaming endpoint
    in main.py (same interface as the former run_adk_workflow).
    """

    logger.info(
        "LANGGRAPH RUN START | run_id=%s | prompt=%s",
        session_id,
        prompt[:80],
    )

    project_context = _build_project_context(project)

    # asyncio.Queue bridges the graph (runs in a task) to this generator.
    event_queue: asyncio.Queue[dict | None] = asyncio.Queue()

    initial_state: WorkflowState = {
        "prompt": prompt,
        "project_context": project_context,
        "run_id": session_id,
        "plan": "",
        "coding_result": {},
        "validation_result": {},
        "review_result": {},
        "approved_plan": False,
        "rejected": False,
        "error": "",
        "event_queue": event_queue,
    }

    graph = get_compiled_graph()

    # Run the graph in a background task so we can concurrently
    # read from the queue and yield SSE events.
    async def _run_graph():
        try:
            await graph.ainvoke(initial_state)
        except Exception as exc:
            logger.exception(
                "Graph raised an unhandled exception | run_id=%s",
                session_id,
            )
            await event_queue.put(
                {
                    "id": f"evt_err_{int(time.time()*1_000_000)}",
                    "agent": "System",
                    "message": str(exc),
                    "status": "failed",
                    "type": "error",
                    "path": None,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "data": {},
                }
            )
            await event_queue.put(None)  # sentinel

    graph_task = asyncio.create_task(_run_graph())

    # Read from queue and yield until we receive the sentinel (None).
    while True:
        event = await event_queue.get()

        if event is None:
            # Workflow complete.
            break

        _record_session_event(session_id, event)

        yield event

    # Ensure graph task is fully done.
    try:
        await asyncio.wait_for(graph_task, timeout=5.0)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        pass

    logger.info("LANGGRAPH RUN COMPLETE | run_id=%s", session_id)


# Alias used by main.py
run_adk_workflow = run_langgraph_workflow
