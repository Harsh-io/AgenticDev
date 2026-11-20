import json
import httpx

def test_rejection_workflow():
    client = httpx.Client(base_url="http://localhost:8000", timeout=60.0)
    
    with client.stream(
        "POST",
        "/api/agent/run/stream",
        json={"prompt": "create a tiny react counter"},
        headers={"Origin": "http://localhost:5174"}
    ) as response:
        assert response.status_code == 200
        
        run_id = None
        coder_seen = False
        workflow_failed = False
        
        for line in response.iter_lines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("data:"):
                raw_data = line[5:].strip()
                event_data = json.loads(raw_data)
                event_type = event_data.get("type")
                agent = event_data.get("agent")
                
                if event_data.get("run_id"):
                    run_id = event_data["run_id"]
                
                if event_type == "approval_required":
                    print(f"Rejecting plan for run_id={run_id}...")
                    appr_res = client.post(
                        f"/api/agent/{run_id}/approval",
                        json={
                            "run_id": run_id,
                            "approval_type": "plan_approval",
                            "approved": False,
                            "approved_by": "test_user",
                            "reason": "Change requirements"
                        }
                    )
                    assert appr_res.status_code == 200
                
                if agent == "Coder":
                    coder_seen = True
                
                if event_type == "run_completed" and event_data.get("status") == "failed":
                    workflow_failed = True
                    break

        assert not coder_seen, "Coder must NOT run when plan is rejected"
        assert workflow_failed, "Workflow should report failed status on rejection"
        print("REJECTION FLOW PASSED: Coder was correctly blocked on rejection.")

if __name__ == "__main__":
    test_rejection_workflow()
