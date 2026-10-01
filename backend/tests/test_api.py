import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    # "degraded" is a legitimate state: it means the embedding fallback is live.
    assert data["status"] in ("healthy", "degraded")
    assert "services" in data

def test_get_statistics():
    """Test statistics endpoint"""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "statistics" in data
    assert "timestamp" in data

def test_list_documents():
    """Test list documents endpoint"""
    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "count" in data

def test_security_logs():
    """Test security logs endpoint"""
    response = client.get("/api/security/logs?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert "count" in data