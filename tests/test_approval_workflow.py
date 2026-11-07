import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from adk_app.workflow.approval import (
    create_approval,
    get_approval,
    resolve_approval,
    approval_to_dict,
)

def test_approval_lifecycle():
    run_id = "test-run-lifecycle"
    approval = create_approval(
        run_id=run_id,
        approval_type="plan_approval",
        message="Plan: 1. index.html 2. app.js",
    )
    assert approval.run_id == run_id
    assert approval.status == "pending"

    # Fetch approval
    fetched = get_approval(run_id, "plan_approval")
    assert fetched is not None
    assert fetched.run_id == run_id

    # Resolve approval
    resolved = resolve_approval(run_id, "plan_approval", approved=True, approved_by="tester", reason="Approved")
    assert resolved.status == "approved"
    assert get_approval(run_id, "plan_approval").status == "approved"
