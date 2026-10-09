"""
langgraph_app/workflow/task_context.py

Reads task.txt from the project root so agents can verify
their output against the original task specification.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache


logger = logging.getLogger("vibecode.task_context")

# Resolve task.txt relative to this file's location:
# langgraph_app/workflow/task_context.py → ../../.. → project root
_TASK_FILE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "task.txt",
)


@lru_cache(maxsize=1)
def load_task_spec() -> str:
    """
    Load the contents of task.txt once and cache the result.
    Returns an empty string if the file does not exist.
    """
    path = os.path.normpath(_TASK_FILE)

    try:
        with open(path, encoding="utf-8") as f:
            content = f.read().strip()
            logger.info("task.txt loaded (%d chars) from %s", len(content), path)
            return content
    except FileNotFoundError:
        logger.debug("task.txt not found at %s — skipping task context.", path)
        return ""
    except Exception as exc:
        logger.warning("Could not read task.txt: %s", exc)
        return ""


def task_context_section() -> str:
    """
    Returns a formatted section to append to agent system prompts
    when task.txt is available, so agents can self-verify completion.
    """
    spec = load_task_spec()

    if not spec:
        return ""

    return f"""

---
ORIGINAL TASK SPECIFICATION (task.txt):

{spec}
---

Verify that your output satisfies the requirements above.
"""
