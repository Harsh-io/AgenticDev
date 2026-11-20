import json
import httpx
import time

def test_stream_workflow():
    client = httpx.Client(base_url="http://localhost:8000", timeout=60.0)
    
    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    print("Health check:", data)
    assert data["status"] == "ok"
    assert data["model_provider"] == "groq"
    
    # 2. Start streaming request
    print("Initiating streaming request...")
    with client.stream(
        "POST",
        "/api/agent/run/stream",
        json={"prompt": "create a tiny html ball game"},
        headers={"Origin": "http://localhost:5174"}
    ) as response:
        assert response.status_code == 200
        print("Connected to stream, status 200.")
        
        run_id = None
        plan_seen = False
        files_created = []
        workflow_completed = False
        
        for line in response.iter_lines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("data:"):
                raw_data = line[5:].strip()
                event_data = json.loads(raw_data)
                event_type = event_data.get("type")
                agent = event_data.get("agent")
                msg = event_data.get("message", "")
                
                print(f" [SSE] agent={agent} type={event_type} msg={msg[:60]}")
                
                if event_data.get("run_id"):
                    run_id = event_data["run_id"]
                
                if event_type == "approval_required":
                    plan_seen = True
                    print(f"\n>>> Approval required for run_id={run_id}. Submitting approval...")
                    appr_res = client.post(
                        f"/api/agent/{run_id}/approval",
                        json={
                            "run_id": run_id,
                            "approval_type": "plan_approval",
                            "approved": True,
                            "approved_by": "test_user",
                            "reason": "Plan looks great"
                        }
                    )
                    print(f">>> Approval response ({appr_res.status_code}):", appr_res.json())
                    assert appr_res.status_code == 200
                
                if event_type == "file_created":
                    path = event_data.get("path")
                    content_len = len(event_data.get("data", {}).get("content", ""))
                    files_created.append(path)
                    print(f"    --> File created: {path} ({content_len} bytes)")
                
                if event_type == "run_completed":
                    workflow_completed = True
                    project = event_data.get("project") or event_data.get("data", {}).get("project")
                    ready = event_data.get("ready_for_preview")
                    print(f"\n>>> Workflow completed! Ready for preview: {ready}")
                    print(f">>> Project files in completion event: {[f['path'] for f in project.get('files', [])]}")
                    break

        assert plan_seen, "Planner should have run and requested approval"
        assert len(files_created) > 0, "Coder should have created project files"
        assert workflow_completed, "Workflow should have completed successfully"
        print("\nALL WORKFLOW CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_stream_workflow()
