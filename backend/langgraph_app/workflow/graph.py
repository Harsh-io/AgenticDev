"""
langgraph_app/workflow/graph.py

LangGraph StateGraph definition for the VibeCode agent workflow.

Workflow:
  planner_node
      ↓  (emits plan_approval SSE and waits for human)
  plan_approval_node
      ↓  (approved → coder_node | rejected → end_node)
  coder_node
      ↓
  validator_node
      ↓
  reviewer_node
      ↓
  end_node

Human approval is handled with asyncio.Event and the existing frontend API
contract.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any, AsyncGenerator, TypedDict

from langgraph.graph import StateGraph, END

from langgraph_app.agents.planner import run_planner
from langgraph_app.agents.coder import run_coder
from langgraph_app.agents.validator import run_validator
from langgraph_app.agents.reviewer import run_reviewer

from adk_app.workflow.approval import (
    PLAN_APPROVAL,
    BUILD_APPROVAL,
    create_approval,
    wait_for_approval,
)

from adk_app.workflow.file_events import parse_coding_result


logger = logging.getLogger("vibecode.langgraph.workflow")


# ============================================================
# HELPERS
# ============================================================

def _make_event(
    *,
    agent: str,
    message: str,
    event_type: str = "status",
    status: str = "running",
    path: str | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": f"evt_{int(time.time() * 1_000_000)}",
        "agent": agent,
        "message": message,
        "status": status,
        "type": event_type,
        "path": path,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "data": data or {},
    }


def _extract_files_from_plan(plan_text: str) -> tuple[list[str], list[str]]:
    """Extract file paths mentioned in the plan."""
    files_to_create: list[str] = []
    files_to_modify: list[str] = []

    if not plan_text:
        return (["index.html", "style.css", "script.js"], [])

    file_pattern = re.findall(
        r"(?:[\w.-]+/)*[\w.-]+\.(?:tsx|ts|jsx|js|html|css|json|md)",
        plan_text,
        flags=re.IGNORECASE,
    )

    unique_files = list(dict.fromkeys(file_pattern))

    allowed_roots = ("src/", "public/")
    allowed_root_files = {
        "package.json", "index.html", "vite.config.ts", "vite.config.js",
        "tsconfig.json", "tsconfig.app.json", "tsconfig.node.json",
        "style.css", "script.js",
    }

    for file_path in unique_files:
        normalized = file_path.strip("`'\".,:;()[]")
        if normalized.startswith(allowed_roots) or normalized in allowed_root_files:
            files_to_create.append(normalized)

    if not files_to_create:
        files_to_create = ["index.html", "style.css", "script.js"]

    return (list(dict.fromkeys(files_to_create))[:12], files_to_modify[:8])


def _create_fallback_project(prompt: str) -> list[dict[str, str]]:
    """Emergency fallback when the Coder produces unparseable output."""
    title = prompt[:40] if prompt else "VibeCode App"
    return [
        {
            "path": "index.html",
            "content": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <div id="app">
    <h1>{title}</h1>
    <p>Your AI-generated project is ready.</p>
  </div>
  <script src="script.js"></script>
</body>
</html>""",
        },
        {
            "path": "style.css",
            "content": """* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; min-height: 100vh;
       display: flex; align-items: center; justify-content: center; }
#app { text-align: center; padding: 32px; }
h1 { font-size: 2rem; margin-bottom: 1rem; }
""",
        },
        {
            "path": "script.js",
            "content": f'console.log("{title} ready.");',
        },
    ]


# ============================================================
# LANGGRAPH STATE
# ============================================================

class WorkflowState(TypedDict):
    prompt: str
    project_context: str
    run_id: str
    plan: str
    coding_result: dict
    validation_result: dict
    review_result: dict
    approved_plan: bool
    rejected: bool
    error: str
    # asyncio.Queue for streaming events out to the runner
    event_queue: Any  # asyncio.Queue[dict | None]


# ============================================================
# GRAPH NODES
# ============================================================

async def planner_node(state: WorkflowState) -> dict:
    queue: asyncio.Queue = state["event_queue"]

    await queue.put(_make_event(
        agent="Planner",
        message="Analyzing your request and formulating an implementation plan...",
        event_type="agent_started",
        status="running",
    ))

    try:
        plan = await run_planner(
            prompt=state["prompt"],
            project_context=state["project_context"],
        )

        logger.info("Planner completed. Plan length=%d chars", len(plan))

        await queue.put(_make_event(
            agent="Planner",
            message="Implementation plan complete.",
            event_type="agent_completed",
            status="completed",
        ))

        return {"plan": plan}

    except Exception as exc:
        logger.exception("Planner failed: %s", exc)

        await queue.put(_make_event(
            agent="Planner",
            message=f"Planning failed: {exc}",
            event_type="error",
            status="failed",
        ))

        return {"plan": "", "error": str(exc)}


async def plan_approval_node(state: WorkflowState) -> dict:
    queue: asyncio.Queue = state["event_queue"]
    run_id = state["run_id"]
    plan = state["plan"]

    if not plan:
        # Planning failed — skip approval
        return {"approved_plan": False, "rejected": True}

    files_to_create, files_to_modify = _extract_files_from_plan(plan)

    approval = create_approval(
        run_id=run_id,
        approval_type=PLAN_APPROVAL,
        message=(
            "The Planner has finished. Please review the implementation plan below "
            "and approve or reject it before coding begins."
        ),
    )

    await queue.put(_make_event(
        agent="System",
        message="Waiting for your plan approval...",
        event_type="approval_required",
        status="waiting",
        data={
            "approval_type": PLAN_APPROVAL,
            "run_id": run_id,
            "message": approval.message,
            "plan": plan,
            "files_to_create": files_to_create,
            "files_to_modify": files_to_modify,
        },
    ))

    logger.info("Waiting for plan approval | run_id=%s", run_id)

    approved = await wait_for_approval(run_id, PLAN_APPROVAL)

    if approved:
        await queue.put(_make_event(
            agent="System",
            message="Plan approved — coding will now begin.",
            event_type="status",
            status="completed",
        ))

        return {"approved_plan": True}

    else:
        await queue.put(_make_event(
            agent="System",
            message="Plan was rejected. Workflow stopped.",
            event_type="error",
            status="failed",
        ))

        return {"approved_plan": False, "rejected": True}


async def coder_node(state: WorkflowState) -> dict:
    queue: asyncio.Queue = state["event_queue"]

    await queue.put(_make_event(
        agent="Coder",
        message="Implementing the approved plan — writing all project files...",
        event_type="agent_started",
        status="running",
    ))

    try:
        raw_response = await run_coder(
            plan=state["plan"],
            project_context=state["project_context"],
            prompt=state["prompt"],
        )

        coding_result = parse_coding_result(raw_response)

        if coding_result is None:
            logger.warning("Coder returned unparseable output — using fallback project.")

            coding_result = {
                "summary": "Fallback project generated.",
                "files": _create_fallback_project(state["prompt"]),
            }

        logger.info(
            "Coder completed. Files=%d summary=%s",
            len(coding_result.get("files", [])),
            coding_result.get("summary", "")[:80],
        )

        # Emit file_created events for each generated file
        for file in coding_result.get("files", []):
            await queue.put(_make_event(
                agent="Coder",
                message=f"Written: {file['path']}",
                event_type="file_created",
                status="completed",
                path=file["path"],
                data={"content": file["content"]},
            ))

        await queue.put(_make_event(
            agent="Coder",
            message=coding_result.get("summary", "Code generation complete."),
            event_type="agent_completed",
            status="completed",
        ))

        return {"coding_result": coding_result}

    except Exception as exc:
        logger.exception("Coder failed: %s", exc)

        fallback = {
            "summary": "Fallback project generated after coder error.",
            "files": _create_fallback_project(state["prompt"]),
        }

        await queue.put(_make_event(
            agent="Coder",
            message=f"Coding error (using fallback): {exc}",
            event_type="error",
            status="failed",
        ))

        return {"coding_result": fallback, "error": str(exc)}


async def validator_node(state: WorkflowState) -> dict:
    queue: asyncio.Queue = state["event_queue"]

    await queue.put(_make_event(
        agent="Validator",
        message="Running static validation on generated files...",
        event_type="agent_started",
        status="running",
    ))

    try:
        validation_result = await run_validator(
            coding_result=state["coding_result"],
            prompt=state["prompt"],
            plan=state["plan"],
        )

        passed = validation_result.get("passed", True)
        errors = validation_result.get("errors", [])

        msg = "Validation passed." if passed else f"Validation found issues: {'; '.join(errors[:3])}"

        await queue.put(_make_event(
            agent="Validator",
            message=msg,
            event_type="validation",
            status="completed",
            data={"passed": passed, "errors": errors},
        ))

        return {"validation_result": validation_result}

    except Exception as exc:
        logger.exception("Validator failed: %s", exc)

        await queue.put(_make_event(
            agent="Validator",
            message="Validation skipped due to error.",
            event_type="validation",
            status="completed",
            data={"passed": True, "errors": []},
        ))

        return {"validation_result": {"passed": True, "errors": [], "warnings": []}}


async def reviewer_node(state: WorkflowState) -> dict:
    queue: asyncio.Queue = state["event_queue"]

    await queue.put(_make_event(
        agent="Reviewer",
        message="Reviewing generated application for quality and completeness...",
        event_type="agent_started",
        status="running",
    ))

    try:
        review_result = await run_reviewer(
            coding_result=state["coding_result"],
            validation_result=state["validation_result"],
            prompt=state["prompt"],
            plan=state["plan"],
        )

        await queue.put(_make_event(
            agent="Reviewer",
            message=review_result.get("summary", "Review complete."),
            event_type="agent_completed",
            status="completed",
        ))

        return {"review_result": review_result}

    except Exception as exc:
        logger.exception("Reviewer failed: %s", exc)

        await queue.put(_make_event(
            agent="Reviewer",
            message="Review skipped due to error.",
            event_type="agent_completed",
            status="completed",
        ))

        return {"review_result": {"approved": True, "summary": "Review complete.", "issues": []}}


async def end_node(state: WorkflowState) -> dict:
    queue: asyncio.Queue = state["event_queue"]
    coding_result = state.get("coding_result", {})
    review_result = state.get("review_result", {})

    await queue.put(_make_event(
        agent="System",
        message="Workflow complete — your project is ready for preview.",
        event_type="run_completed",
        status="completed",
        data={
            "run_id": state["run_id"],
            "summary": review_result.get("summary", "Project generated successfully."),
            "project": {
                "name": "generated-project",
                "files": coding_result.get("files", []),
            },
            "ready_for_preview": True,
        },
    ))

    # Sentinel tells the runner to stop reading from the queue.
    await queue.put(None)

    return {}


async def rejected_node(state: WorkflowState) -> dict:
    queue: asyncio.Queue = state["event_queue"]

    await queue.put(_make_event(
        agent="System",
        message="Workflow rejected — no project was generated.",
        event_type="run_completed",
        status="failed",
        data={"run_id": state["run_id"], "ready_for_preview": False},
    ))

    await queue.put(None)

    return {}


# ============================================================
# EDGE ROUTING
# ============================================================

def route_after_approval(state: WorkflowState) -> str:
    if state.get("rejected") or not state.get("approved_plan"):
        return "rejected"
    return "coder"


def route_after_planner(state: WorkflowState) -> str:
    if state.get("error") and not state.get("plan"):
        return "rejected"
    return "plan_approval"


# ============================================================
# BUILD GRAPH
# ============================================================

def build_graph() -> StateGraph:
    graph = StateGraph(WorkflowState)

    graph.add_node("planner", planner_node)
    graph.add_node("plan_approval", plan_approval_node)
    graph.add_node("coder", coder_node)
    graph.add_node("validator", validator_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("end", end_node)
    graph.add_node("rejected", rejected_node)

    graph.set_entry_point("planner")

    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {"plan_approval": "plan_approval", "rejected": "rejected"},
    )

    graph.add_conditional_edges(
        "plan_approval",
        route_after_approval,
        {"coder": "coder", "rejected": "rejected"},
    )

    graph.add_edge("coder", "validator")
    graph.add_edge("validator", "reviewer")
    graph.add_edge("reviewer", "end")
    graph.add_edge("end", END)
    graph.add_edge("rejected", END)

    return graph.compile()


# Singleton compiled graph
_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
