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


def test_get_patients_api(client):
    """Test GET /api/v1/patients."""
    response = client.get("/api/v1/patients")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["count"] >= 1
    assert any(p["patient_code"] == "PAT-2026-001" for p in data["data"])


def test_get_single_patient_api(client):
    """Test GET /api/v1/patients/<id>."""
    response = client.get("/api/v1/patients/1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["patient_code"] == "PAT-2026-001"
    assert data["data"]["active_admission"]["bed_number"] == "ICU-01"


def test_get_beds_api(client):
    """Test GET /api/v1/beds."""
    response = client.get("/api/v1/beds")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["count"] == 4
    # Check bed ICU-01 has current admitted patient
    bed_1 = next(b for b in data["data"] if b["bed_number"] == "ICU-01")
    assert bed_1["current_patient"]["patient_code"] == "PAT-2026-001"


def test_record_and_get_vitals_api(client):
    """Test POST /api/v1/vitals and GET /api/v1/vitals/patient/<id>."""
    # Post a new reading
    new_vital = {
        "patient_id": 1,
        "heart_rate": 84.0,
        "spo2": 97.5,
        "systolic_bp": 125.0,
        "diastolic_bp": 82.0,
        "respiratory_rate": 18.0,
        "temperature": 37.2,
        "measurement_source": "simulator",
    }
    post_res = client.post("/api/v1/vitals", json=new_vital)
    assert post_res.status_code == 201
    post_data = post_res.get_json()
    assert post_data["success"] is True
    assert post_data["data"]["heart_rate"] == 84.0

    # Query vitals
    get_res = client.get("/api/v1/vitals/patient/1?limit=10")
    assert get_res.status_code == 200
    get_data = get_res.get_json()
    assert get_data["success"] is True
    assert get_data["count"] >= 2

