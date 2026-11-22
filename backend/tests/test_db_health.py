import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app


@pytest.fixture
def client():
    app = create_app("testing")
    with app.test_client() as client:
        yield client


def test_db_health_endpoint_status(client):
    """Test that the database health endpoint returns HTTP 200 and connected status."""
    response = client.get("/api/health/db")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["database_connection"] == "connected"
    assert data["database_name"] in ("carewatch_db", "carewatch_test_db")
    assert "8.0" in data["database_version"]
    assert data["table_count"] >= 15
    assert "patients" in data["tables"]
    assert "vital_observations" in data["tables"]

