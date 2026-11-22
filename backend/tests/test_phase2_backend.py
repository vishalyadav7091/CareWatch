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


def test_auth_registration_and_login(client):
    """Day 8: Test staff registration, login, and JWT /me endpoint."""
    email = "doctor.smith@carewatch.local"
    # 1. Register
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Dr. Sarah Smith",
        "email": email,
        "password": "Password#123",
        "role": "doctor",
    })
    # If already exists from earlier test, expect 409, else 201
    assert reg_res.status_code in [201, 409]

    # 2. Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password#123",
    })
    assert login_res.status_code == 200
    login_data = login_res.get_json()
    assert login_data["success"] is True
    assert "token" in login_data
    token = login_data["token"]

    # 3. Access Protected /me
    me_res = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert me_res.status_code == 200
    me_data = me_res.get_json()
    assert me_data["user"]["email"] == email


def test_patient_admit_and_details(client):
    """Day 9: Test creating patient, admitting to bed, and querying."""
    code = "PAT-TEST-002"
    res = client.post("/api/v1/patients", json={
        "patient_code": code,
        "first_name": "Robert",
        "last_name": "Miller",
        "date_of_birth": "1972-04-10",
        "gender": "Male",
        "bed_id": 2,  # ICU-02 is available
    })
    assert res.status_code in [201, 409]

    # Query all patients
    list_res = client.get("/api/v1/patients")
    assert list_res.status_code == 200
    assert list_res.get_json()["count"] >= 2


def test_bed_management_and_status(client):
    """Day 10: Test ICU bed listing and status patching."""
    beds_res = client.get("/api/v1/beds")
    assert beds_res.status_code == 200
    beds_data = beds_res.get_json()
    assert beds_data["count"] == 4

    # Update ICU-03 status to maintenance
    patch_res = client.patch("/api/v1/beds/3/status", json={"status": "maintenance"})
    assert patch_res.status_code == 200
    assert patch_res.get_json()["data"]["status"] == "maintenance"

    # Reset back to available
    reset_res = client.patch("/api/v1/beds/3/status", json={"status": "available"})
    assert reset_res.status_code == 200


def test_vital_observations_flow(client):
    """Day 11: Ingest vital telemetry reading and query time series."""
    post_res = client.post("/api/v1/vitals", json={
        "patient_id": 1,
        "heart_rate": 88.0,
        "spo2": 96.0,
        "systolic_bp": 130.0,
        "diastolic_bp": 85.0,
        "respiratory_rate": 19.0,
        "temperature": 37.3,
        "measurement_source": "simulator",
        "data_quality": "valid",
    })
    assert post_res.status_code == 201

    get_res = client.get("/api/v1/vitals/patient/1?limit=5")
    assert get_res.status_code == 200
    data = get_res.get_json()
    assert data["success"] is True
    assert len(data["data"]) >= 1


def test_alerts_lifecycle(client):
    """Day 12: Raise alert, acknowledge alert, and resolve alert."""
    # 1. Raise alert
    create_res = client.post("/api/v1/alerts", json={
        "patient_id": 1,
        "alert_type": "Tachycardia",
        "severity": "HIGH",
        "description": "Heart rate sustained above 120 bpm",
    })
    assert create_res.status_code == 201
    alert_id = create_res.get_json()["data"]["id"]

    # 2. Query active alerts
    active_res = client.get("/api/v1/alerts?status=active")
    assert active_res.status_code == 200
    assert any(a["id"] == alert_id for a in active_res.get_json()["data"])

    # 3. Acknowledge alert
    ack_res = client.post(f"/api/v1/alerts/{alert_id}/acknowledge", json={
        "user_id": 1,
        "remarks": "Assessing patient rhythm",
    })
    assert ack_res.status_code == 200
    assert ack_res.get_json()["data"]["status"] == "acknowledged"

    # 4. Resolve alert
    res_res = client.post(f"/api/v1/alerts/{alert_id}/resolve")
    assert res_res.status_code == 200
    assert res_res.get_json()["data"]["status"] == "resolved"


def test_devices_flow(client):
    """Day 13: List devices and update device heartbeat."""
    dev_res = client.get("/api/v1/devices")
    assert dev_res.status_code == 200
    data = dev_res.get_json()
    assert data["count"] >= 1

    # Heartbeat patch
    dev_id = data["data"][0]["id"]
    patch_res = client.patch(f"/api/v1/devices/{dev_id}/status", json={
        "connection_status": "connected"
    })
    assert patch_res.status_code == 200
    assert patch_res.get_json()["data"]["connection_status"] == "connected"

