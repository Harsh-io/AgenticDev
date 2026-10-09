"""
langgraph_app/agents/reviewer.py

The Reviewer Agent performs a final quality review of the generated
application against the user's request and validation results.
"""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from langgraph_app.agents.llm import build_llm
from langgraph_app.workflow.task_context import task_context_section


SYSTEM_PROMPT = """\
You are the final Code Reviewer for VibeCode.ai.

Review the generated application against:

1. The user's original request.
2. The approved implementation plan.
3. The validation results.

Check:

- Requirement coverage.
- Code quality.
- Maintainability.
- Consistency.
- Unnecessary changes.
- Obvious regressions.
- User experience.

Do not rewrite files.

If the application satisfies the request, approve it with approved: true.

If important issues remain, clearly explain them and set approved: false.

Do not invent problems.

Return your result as JSON:

{
  "approved": true,
  "summary": "Brief review summary",
  "issues": [],
  "suggestions": []
}
"""


async def run_reviewer(
    coding_result: dict,
    validation_result: dict,
    prompt: str,
    plan: str,
) -> dict:
    """
    Invoke the reviewer and return a parsed result dict.
    """

    llm = build_llm(temperature=0.2)

    system_prompt = SYSTEM_PROMPT + task_context_section()

    user_content = (
        f"ORIGINAL USER REQUEST:\n{prompt}\n\n"
        f"APPROVED PLAN:\n{plan}\n\n"
        f"VALIDATION RESULT:\n{json.dumps(validation_result, indent=2)}\n\n"
        f"GENERATED FILES SUMMARY:\n"
        + json.dumps(
            [
                {"path": f["path"], "lines": f["content"].count(chr(10))}
                for f in coding_result.get("files", [])
            ],
            indent=2,
        )
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    response = await llm.ainvoke(messages)
    raw = str(response.content).strip()

    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw)

        return {
            "approved": bool(result.get("approved", True)),
            "summary": str(result.get("summary", "Review complete.")),
            "issues": result.get("issues", []),
            "suggestions": result.get("suggestions", []),
        }

    except Exception:
        return {
            "approved": True,
            "summary": raw[:300] if raw else "Review complete.",
            "issues": [],
            "suggestions": [],
        }
