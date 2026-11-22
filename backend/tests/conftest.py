"""
Phase 8 (Day 46): Pytest fixtures for backend testing.
Configures isolated test database (carewatch_test_db), test client, and authenticated role headers.
Never touches the development MySQL database.
"""
import pytest
from app import create_app, db
from app.models import User


@pytest.fixture(scope="session")
def app():
    """Create test application using testing configuration (pointing to carewatch_test_db)."""
    application = create_app("testing")
    with application.app_context():
        yield application


@pytest.fixture(scope="session")
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture(scope="session")
def doctor_token(client):
    """JWT token for doctor role."""
    r = client.post("/api/v1/auth/login", json={
        "email": "doctor.smith@carewatch.local",
        "password": "Password#123",
    })
    return r.get_json()["token"]


@pytest.fixture(scope="session")
def nurse_token(client):
    """JWT token for nurse role."""
    r = client.post("/api/v1/auth/login", json={
        "email": "nurse.jack@carewatch.local",
        "password": "Password#123",
    })
    return r.get_json()["token"]


@pytest.fixture(scope="session")
def admin_token(client):
    """JWT token for admin role."""
    r = client.post("/api/v1/auth/login", json={
        "email": "admin@carewatch.local",
        "password": "Password#123",
    })
    return r.get_json()["token"]


@pytest.fixture(scope="session")
def doctor_headers(doctor_token):
    return {"Authorization": f"Bearer {doctor_token}"}


@pytest.fixture(scope="session")
def nurse_headers(nurse_token):
    return {"Authorization": f"Bearer {nurse_token}"}


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
