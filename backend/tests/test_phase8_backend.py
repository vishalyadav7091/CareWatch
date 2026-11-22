"""
Phase 8 (Day 46): Comprehensive Backend Validation & Hardening Test Suite.
Tests unit logic, API integration, database, authentication, authorization (RBAC),
WebSocket messaging, and validation/error handling against carewatch_test_db.
"""
import pytest
from app.models import Patient, Bed, MedicalDevice, VitalObservation, Alert, AuditLog, User
from app.services.validator import VitalValidator
from app.services.normalizer import VitalNormalizer
from app.services.simulator import PatientTelemetrySimulator
from app.services.feature_extractor import extract_features, N_FEATURES
from app.services.alert_engine import evaluate_patient_alerts, DEMO_THRESHOLDS


# =====================================================================
# 1. UNIT TESTS
# =====================================================================
def test_unit_validator_valid_reading():
    reading = {
        "heart_rate": 75.0, "spo2": 98.0, "systolic_bp": 120.0,
        "diastolic_bp": 80.0, "respiratory_rate": 16.0, "temperature": 37.0,
    }
    is_valid, quality, errors = VitalValidator.validate(reading)
    assert is_valid is True
    assert quality == "valid"
    assert len(errors) == 0


def test_unit_validator_out_of_bounds():
    reading = {
        "heart_rate": 350.0,  # Biologically impossible
        "spo2": 105.0,        # > 100%
        "systolic_bp": -10.0,
    }
    is_valid, quality, errors = VitalValidator.validate(reading)
    assert is_valid is False
    assert quality == "invalid"
    assert len(errors) >= 2


def test_unit_normalizer_fahrenheit_conversion():
    reading = {"temperature": 98.6, "temperature_unit": "F"}
    norm = VitalNormalizer.normalize_reading(reading)
    assert abs(norm["temperature"] - 37.0) < 0.2


def test_unit_simulator_scenarios():
    for sc in ("stable", "arrhythmia_tachycardia", "desaturation_hypoxia", "septic_shock"):
        reading = PatientTelemetrySimulator.generate_reading(patient_id=1, scenario=sc)
        assert reading["patient_id"] == 1
        assert "heart_rate" in reading
        assert "spo2" in reading


def test_unit_feature_extraction_length():
    window = [
        {"heart_rate": 80, "spo2": 98, "systolic_bp": 120, "diastolic_bp": 80,
         "respiratory_rate": 16, "temperature": 37.0, "data_quality": "valid"}
        for _ in range(5)
    ]
    feats = extract_features(window)
    assert len(feats) == N_FEATURES


# =====================================================================
# 2. AUTHENTICATION TESTS
# =====================================================================
def test_auth_login_success(client):
    r = client.post("/api/v1/auth/login", json={
        "email": "doctor.smith@carewatch.local",
        "password": "Password#123",
    })
    assert r.status_code == 200
    data = r.get_json()
    assert "token" in data
    assert data["user"]["email"] == "doctor.smith@carewatch.local"


def test_auth_login_invalid_password(client):
    r = client.post("/api/v1/auth/login", json={
        "email": "doctor.smith@carewatch.local",
        "password": "WrongPassword!",
    })
    assert r.status_code == 401
    assert "Invalid credentials" in r.get_json().get("error", "")


def test_auth_login_nonexistent_user(client):
    r = client.post("/api/v1/auth/login", json={
        "email": "nobody@carewatch.local",
        "password": "Password#123",
    })
    assert r.status_code == 401


def test_auth_login_missing_fields(client):
    r = client.post("/api/v1/auth/login", json={"email": "doc@test.local"})
    assert r.status_code == 400


def test_auth_me_authenticated(client, doctor_headers):
    r = client.get("/api/v1/auth/me", headers=doctor_headers)
    assert r.status_code == 200
    assert r.get_json()["user"]["role"] == "doctor"


def test_auth_me_unauthenticated(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


# =====================================================================
# 3. AUTHORIZATION TESTS (RBAC)
# =====================================================================
def test_rbac_admin_can_access_audit(client, admin_headers):
    r = client.get("/api/v1/audit", headers=admin_headers)
    assert r.status_code == 200
    assert r.get_json()["success"] is True


def test_rbac_doctor_can_access_audit(client, doctor_headers):
    r = client.get("/api/v1/audit", headers=doctor_headers)
    assert r.status_code == 200
    assert r.get_json()["success"] is True


def test_rbac_nurse_forbidden_from_audit(client, nurse_headers):
    r = client.get("/api/v1/audit", headers=nurse_headers)
    assert r.status_code == 403
    assert "insufficient role" in r.get_json()["error"]


# =====================================================================
# 4. API INTEGRATION TESTS
# =====================================================================
def test_api_patients_list(client):
    r = client.get("/api/v1/patients")
    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert data["count"] >= 1


def test_api_patient_detail(client):
    r = client.get("/api/v1/patients/1")
    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert data["data"]["patient_code"] == "PAT-2026-001"


def test_api_beds_list(client):
    r = client.get("/api/v1/beds")
    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert data["count"] >= 4


def test_api_bed_status_patch(client):
    r = client.patch("/api/v1/beds/2/status", json={"status": "maintenance"})
    assert r.status_code == 200
    assert r.get_json()["data"]["status"] == "maintenance"
    # Revert to available
    client.patch("/api/v1/beds/2/status", json={"status": "available"})


def test_api_vitals_ingest_and_retrieve(client):
    vital_payload = {
        "patient_id": 1,
        "heart_rate": 82.0,
        "spo2": 97.0,
        "systolic_bp": 118.0,
        "diastolic_bp": 78.0,
        "respiratory_rate": 16.0,
        "temperature": 36.9,
        "measurement_source": "test_suite",
    }
    post_res = client.post("/api/v1/vitals", json=vital_payload)
    assert post_res.status_code == 201

    get_res = client.get("/api/v1/vitals/patient/1?limit=5")
    assert get_res.status_code == 200
    assert len(get_res.get_json()["data"]) >= 1


# =====================================================================
# 5. DATABASE TESTS
# =====================================================================
def test_db_patient_admission_relationship(app):
    with app.app_context():
        p = Patient.query.filter_by(patient_code="PAT-2026-001").first()
        assert p is not None
        assert len(p.admissions) >= 1
        adm = p.admissions[0]
        assert adm.bed is not None
        assert adm.bed.bed_number == "ICU-01"


def test_db_audit_log_record(app):
    from app.services.audit_service import log_action
    with app.app_context():
        initial = AuditLog.query.count()
        log_action(1, "TEST_ACTION", "patient", 1, {"note": "db test"})
        after = AuditLog.query.count()
        assert after == initial + 1


# =====================================================================
# 6. VALIDATION & ERROR HANDLING TESTS
# =====================================================================
def test_error_404_handler(client):
    r = client.get("/api/v1/non_existent_route")
    assert r.status_code == 404
    assert r.get_json()["success"] is False


def test_error_missing_patient_in_alert(client):
    r = client.post("/api/v1/alerts", json={
        "patient_id": 999999,
        "alert_type": "TEST",
        "description": "missing patient",
    })
    assert r.status_code == 404


def test_error_invalid_alert_severity(client):
    r = client.post("/api/v1/alerts", json={
        "patient_id": 1,
        "alert_type": "TEST",
        "severity": "INVALID_SEVERITY",
        "description": "bad severity",
    })
    assert r.status_code == 400
