import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from models import ProjectSnapshot, ProjectFile, AgentRunRequest

def test_valid_project_snapshot():
    snapshot = ProjectSnapshot(
        name="test-app",
        framework="react",
        entrypoint="src/main.jsx",
        files=[
            ProjectFile(path="src/main.jsx", content="console.log('hi');")
        ]
    )
    assert snapshot.name == "test-app"
    assert len(snapshot.files) == 1

def test_agent_run_request_validation():
    req = AgentRunRequest(prompt="Build a blog")
    assert req.prompt == "Build a blog"
    assert req.project is None

