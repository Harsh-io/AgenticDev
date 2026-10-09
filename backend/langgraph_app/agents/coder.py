"""
langgraph_app/agents/coder.py

The Coding Agent takes the approved plan and the project context,
then produces a complete JSON response with all project files.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from langgraph_app.agents.llm import build_llm
from langgraph_app.workflow.task_context import task_context_section


SYSTEM_PROMPT = """\
You are the Coding Agent for VibeCode.ai.

Implement the approved implementation plan.

Return ONLY valid JSON using this exact structure:

{
  "summary": "short implementation summary",
  "files": [
    {
      "path": "index.html",
      "content": "complete file content"
    }
  ]
}

Rules:

1. Return complete file contents.
2. Never return placeholder code.
3. Never use TODO implementation placeholders.
4. Create every required file.
5. Keep dependencies minimal.
6. Preserve existing functionality when editing an existing project.
7. Do not modify unrelated files.
8. Make the project immediately runnable.
9. Use vanilla HTML + CSS + JS for browser projects unless the approved plan specifies otherwise.
10. Ensure all imports reference real files.
11. Ensure the application has a valid entrypoint.
12. Return only files that need to be created or modified.

IMPORTANT:

- Do NOT use markdown fences.
- Do NOT add explanations outside the JSON.
- The backend parses your response automatically.
"""


async def run_coder(plan: str, project_context: str, prompt: str) -> str:
    """
    Invoke the coder and return the raw JSON string response.
    """

    llm = build_llm(temperature=0.1)

    system_prompt = SYSTEM_PROMPT + task_context_section()

    user_content = (
        f"ORIGINAL USER REQUEST:\n{prompt}\n\n"
        f"APPROVED IMPLEMENTATION PLAN:\n{plan}"
    )

    if project_context.strip():
        user_content += f"\n\nEXISTING PROJECT CONTEXT:\n{project_context}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    response = await llm.ainvoke(messages)

    return str(response.content)
