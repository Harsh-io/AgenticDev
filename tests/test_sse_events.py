import json
import pytest

def parse_sse_line(line: str):
    line = line.strip()
    if line.startswith("data:"):
        raw = line[5:].strip()
        return json.loads(raw)
    return None

def test_parse_valid_sse_event():
    sample = 'data: {"type": "agent_started", "agent": "planner", "message": "Planning initiated"}'
    parsed = parse_sse_line(sample)
    assert parsed is not None
    assert parsed["type"] == "agent_started"
    assert parsed["agent"] == "planner"

def test_parse_approval_required_event():
    sample = 'data: {"type": "approval_required", "run_id": "test-run-123", "plan": "Create dashboard"}'
    parsed = parse_sse_line(sample)
    assert parsed["type"] == "approval_required"
    assert parsed["run_id"] == "test-run-123"

def test_parse_empty_line():
    assert parse_sse_line("") is None
    assert parse_sse_line("   ") is None

