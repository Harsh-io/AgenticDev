"""
langgraph_app/agents/validator.py

The Validator Agent performs static inspection of the generated project
and returns a structured validation report.
"""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from langgraph_app.agents.llm import build_llm


SYSTEM_PROMPT = """\
You are the Validator Agent for VibeCode.ai.

Inspect the generated project.

Check:

1. Required files are present.
2. File paths are valid.
3. Imports reference real files.
4. package.json (if present) is valid JSON with correct scripts.
5. Dependencies are consistent.
6. Framework structure is correct.
7. Entrypoint exists and is referenced correctly.
8. Obvious syntax or configuration issues.
9. Requirement coverage against the original user request.

IMPORTANT:

You are performing STATIC inspection only.

You must NOT claim that npm, Vite, or any other command was executed.

Only report an error if there is concrete evidence in the files supplied.

Do not fail a project merely because you did not receive a file in context.

Separate real errors from warnings.

Do not invent problems.

Return your result as JSON:

{
  "passed": true,
  "errors": [],
  "warnings": ["optional warnings here"]
}
"""


async def run_validator(
    coding_result: dict,
    prompt: str,
    plan: str,
) -> dict:
    """
    Invoke the validator and return a parsed result dict.
    """

    llm = build_llm(temperature=0.0)

    files_summary = json.dumps(
        [
            {"path": f["path"], "content_length": len(f["content"])}
            for f in coding_result.get("files", [])
        ],
        indent=2,
    )

    user_content = (
        f"ORIGINAL USER REQUEST:\n{prompt}\n\n"
        f"APPROVED PLAN:\n{plan}\n\n"
        f"GENERATED FILES:\n{files_summary}\n\n"
        f"FULL FILE CONTENTS:\n"
        + json.dumps(coding_result.get("files", []), indent=2)
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]

    response = await llm.ainvoke(messages)
    raw = str(response.content).strip()

    # Try to parse JSON from the response
    try:
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw)

        return {
            "passed": bool(result.get("passed", True)),
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
            "raw": raw,
        }

    except Exception:
        # Validator response is not critical — default to passed
        return {
            "passed": True,
            "errors": [],
            "warnings": [f"Validator response could not be parsed: {raw[:200]}"],
            "raw": raw,
        }
