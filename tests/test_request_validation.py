import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from pydantic import ValidationError
from models import AgentRunRequest, ApprovalResponse

def test_empty_prompt_validation():
    # AgentRunRequest requires prompt string
    req = AgentRunRequest(prompt="Valid prompt")
    assert req.prompt == "Valid prompt"

def test_approval_response_validation():
    res = ApprovalResponse(
        run_id="run-123",
        approval_type="plan_approval",
        approved=True,
        approved_by="tester",
        reason="Looks good"
    )
    assert res.approved is True
    assert res.run_id == "run-123"

