import pytest
from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)

def test_nl_query_503_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    resp = client.post("/api/nl-query", json={"question": "test"})
    assert resp.status_code == 503
    assert "Natural language queries are not available" in resp.json()['detail']

def test_nl_query_response_schema():
    if "GEMINI_API_KEY" not in os.environ:
        pytest.skip("GEMINI_API_KEY strictly required organically to resolve endpoint testing.")
        
    resp = client.post("/api/nl-query", json={
        "question": "Which country imported most boron strictly evaluating raw schemas structurally?"
    })
    
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "path" in data
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0 
