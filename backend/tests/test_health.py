import pytest
import sys
import os

# Ensure backend root is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app


@pytest.fixture
def client():
    app = create_app("development")
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_check_status_code(client):
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_check_payload(client):
    response = client.get("/api/health")
    data = response.get_json()
    assert data is not None
    assert data.get("status") == "healthy"
    assert data.get("service") == "CareWatch Backend"
    assert data.get("version") == "1.0.0"
    assert "timestamp" in data

