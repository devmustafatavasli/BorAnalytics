import pytest
from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)

def test_events_list():
    response = client.get("/api/events")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_events_filter():
    response = client.get("/api/events?event_type=capacity_expansion")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert data[0]['event_type'] == 'capacity_expansion'

def test_event_not_found():
    response = client.get("/api/events/999999")
    assert response.status_code == 404

def test_centrality_no_neo4j(monkeypatch):
    """Verifies the 503 fallback when NEO4J_URI environment bindings are missing."""
    monkeypatch.delenv("NEO4J_URI", raising=False)
    response = client.get("/api/graph/centrality")
    assert response.status_code == 503
    assert "Graph database not configured" in response.json()['detail']

def test_exposure_endpoint(monkeypatch):
    """
    Simulates graph query when Neo4j URI exists but driver could fail or 
    returns struct conditionally. To avoid external dependency crashes, 
    we test structural availability or handling natively.
    """
    # Simply ensure the route exists and has proper query params mapping
    monkeypatch.delenv("NEO4J_URI", raising=False)
    
    # Without API param
    response = client.get("/api/graph/exposure")
    assert response.status_code == 422 # Pydantic validation error (missing 'country')
    
    # With param but no Neo4j
    response2 = client.get("/api/graph/exposure?country=DEU")
    assert response2.status_code == 503
