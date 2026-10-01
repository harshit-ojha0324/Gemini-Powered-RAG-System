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
    assert data["status"] == "healthy"
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

def test_overlong_question_is_rejected_before_any_work():
    response = client.post("/api/query", json={"question": "a" * 10_001})
    assert response.status_code == 422

def test_security_logs_are_newest_first_and_limited(tmp_path, monkeypatch):
    import json
    import app as app_module
    log_file = tmp_path / "security_log.jsonl"
    log_file.write_text("".join(json.dumps({"query": q}) + "\n" for q in ["a", "b", "c"]))
    monkeypatch.setattr(app_module, "LOG_FILE", log_file)

    data = client.get("/api/security/logs?limit=2").json()
    assert [entry["query"] for entry in data["logs"]] == ["c", "b"]
    assert client.get("/api/security/logs?limit=0").status_code == 422