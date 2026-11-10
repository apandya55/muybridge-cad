from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "openscad_installed" in data
    assert "llm_provider" in data
    assert "critic_max_iterations" in data


def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_missing_stl_404():
    # Valid md5 hex length but nonexistent job
    res = client.get("/api/stl/00000000000000000000000000000000")
    assert res.status_code == 404


def test_invalid_job_id_format():
    res = client.get("/api/stl/bad_id!")
    assert res.status_code == 404
