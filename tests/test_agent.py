import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for imports
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

os.environ["OPENAI_API_KEY"] = "dummy-key-for-testing"

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "AI Job Research & Summary Agent API"}

def test_analyze(monkeypatch):
    # Mock the agent to avoid real OpenAI calls during tests
    from app import main

    def fake_invoke(state):
        return {
            "skills_required": ["Python", "FastAPI"],
            "skill_gaps": [],
            "learning_plan": "Practice building FastAPI services.",
            "relevant_resources": ["https://fastapi.tiangolo.com/"]
        }

    monkeypatch.setattr(main, "agent", type("DummyAgent", (), {"invoke": staticmethod(fake_invoke)}))

    request_data = {
        "job_description": "We need a Python developer with LangChain and FastAPI experience.",
        "current_skills": ["Python", "FastAPI"]
    }
    response = client.post("/analyze", json=request_data)
    assert response.status_code == 200
    body = response.json()
    assert body["skills_required"] == ["Python", "FastAPI"]