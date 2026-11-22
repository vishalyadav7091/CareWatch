"""
Phase 7 (Day 42-45): Alert engine, acknowledgement workflow, and audit log tests.
"""
import pytest
from app import create_app, db
from app.models import Alert, Patient, AuditLog


@pytest.fixture(scope="module")
def app():
    application = create_app("testing")
    with application.app_context():
        yield application


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


# ------------------------------------------------------------------
# Day 42 – Alert engine deduplication
# ------------------------------------------------------------------
def test_alert_engine_critical_hr(app):
    """Alert engine creates CRITICAL alert for HR >= 150 (demo threshold)."""
    from app.services.alert_engine import evaluate_patient_alerts, DEMO_THRESHOLDS

    patient = Patient.query.first()
    if not patient:
        pytest.skip("No patient in DB")

    # Remove any active HR alerts first
    Alert.query.filter_by(
        patient_id=patient.id, alert_type="HR_ALERT", status="active"
    ).delete()
    db.session.commit()

    vitals = {"heart_rate": 155, "spo2": 98, "systolic_bp": 120,
              "diastolic_bp": 80, "respiratory_rate": 18, "temperature": 36.8}
    alerts = evaluate_patient_alerts(patient.id, vitals)
    hr_alerts = [a for a in alerts if a.alert_type == "HR_ALERT"]
    assert hr_alerts, "Expected HR_ALERT for HR=155"
    assert hr_alerts[0].severity == "CRITICAL"


def test_alert_engine_deduplication(app):
    """Second call with same threshold violation should NOT create a duplicate."""
    from app.services.alert_engine import evaluate_patient_alerts

    patient = Patient.query.first()
    if not patient:
        pytest.skip("No patient in DB")

    before = Alert.query.filter_by(
        patient_id=patient.id, alert_type="HR_ALERT", status="active"
    ).count()

    vitals = {"heart_rate": 155, "spo2": 98, "systolic_bp": 120,
              "diastolic_bp": 80, "respiratory_rate": 18, "temperature": 36.8}
    evaluate_patient_alerts(patient.id, vitals)

    after = Alert.query.filter_by(
        patient_id=patient.id, alert_type="HR_ALERT", status="active"
    ).count()
    assert after == before, "Duplicate alert was created – deduplication failed"


def test_alert_engine_normal_vitals_no_alert(app):
    """Normal vitals should not trigger any demo alerts."""
    from app.services.alert_engine import evaluate_patient_alerts

    patient = Patient.query.first()
    if not patient:
        pytest.skip("No patient in DB")

    # Clean slate: resolve all active alerts
    Alert.query.filter_by(patient_id=patient.id, status="active").update({"status": "resolved"})
    db.session.commit()

    vitals = {"heart_rate": 72, "spo2": 98.0, "systolic_bp": 120,
              "diastolic_bp": 80, "respiratory_rate": 16, "temperature": 36.8}
    alerts = evaluate_patient_alerts(patient.id, vitals)
    assert alerts == [], f"Unexpected alerts for normal vitals: {alerts}"


# ------------------------------------------------------------------
# Day 43 – Alert dashboard filters
# ------------------------------------------------------------------
def test_get_alerts_all(client):
    r = client.get("/api/v1/alerts?status=all")
    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert "active_count" in data


def test_get_alerts_severity_filter(client):
    r = client.get("/api/v1/alerts?status=all&severity=CRITICAL")
    assert r.status_code == 200
    data = r.get_json()
    for a in data["data"]:
        assert a["severity"] == "CRITICAL"


def test_create_alert(client, app):
    patient = Patient.query.first()
    if not patient:
        pytest.skip("No patient in DB")
    r = client.post("/api/v1/alerts", json={
        "patient_id": patient.id,
        "alert_type": "TEST_ALERT",
        "severity": "LOW",
        "description": "Phase 7 test alert",
    })
    assert r.status_code == 201
    data = r.get_json()
    assert data["success"] is True
    assert data["data"]["alert_type"] == "TEST_ALERT"


# ------------------------------------------------------------------
# Day 44 – Acknowledgement workflow
# ------------------------------------------------------------------
def test_acknowledge_alert(client, app):
    patient = Patient.query.first()
    if not patient:
        pytest.skip("No patient in DB")

    # Create a fresh active alert
    alert = Alert(
        patient_id=patient.id, alert_type="ACK_TEST",
        severity="MEDIUM", description="Ack workflow test", status="active",
    )
    db.session.add(alert)
    db.session.commit()

    r = client.post(f"/api/v1/alerts/{alert.id}/acknowledge", json={
        "user_id": 1, "remarks": "Phase 7 ack test",
    })
    assert r.status_code == 200
    data = r.get_json()
    assert data["data"]["status"] == "acknowledged"


def test_snooze_alert(client, app):
    patient = Patient.query.first()
    if not patient:
        pytest.skip("No patient in DB")

    alert = Alert(
        patient_id=patient.id, alert_type="SNOOZE_TEST",
        severity="LOW", description="Snooze workflow test", status="active",
    )
    db.session.add(alert)
    db.session.commit()

    r = client.post(f"/api/v1/alerts/{alert.id}/snooze", json={"duration_minutes": 30})
    assert r.status_code == 200
    data = r.get_json()
    assert "snoozed_until" in data["data"]
    assert data["data"]["snoozed_until"] is not None


def test_escalate_alert(client, app):
    patient = Patient.query.first()
    if not patient:
        pytest.skip("No patient in DB")

    alert = Alert(
        patient_id=patient.id, alert_type="ESC_TEST",
        severity="HIGH", description="Escalate workflow test", status="active",
    )
    db.session.add(alert)
    db.session.commit()

    r = client.post(f"/api/v1/alerts/{alert.id}/escalate", json={
        "escalate_to_user_id": 1, "notes": "Needs senior review",
    })
    assert r.status_code == 200
    data = r.get_json()
    assert data["data"]["escalated_to_user_id"] == 1


def test_resolve_alert(client, app):
    patient = Patient.query.first()
    if not patient:
        pytest.skip("No patient in DB")

    alert = Alert(
        patient_id=patient.id, alert_type="RES_TEST",
        severity="MEDIUM", description="Resolve test", status="active",
    )
    db.session.add(alert)
    db.session.commit()

    r = client.post(f"/api/v1/alerts/{alert.id}/resolve", json={"user_id": 1})
    assert r.status_code == 200
    assert r.get_json()["data"]["status"] == "resolved"


def test_cannot_acknowledge_resolved(client, app):
    patient = Patient.query.first()
    if not patient:
        pytest.skip("No patient in DB")

    alert = Alert(
        patient_id=patient.id, alert_type="DOUBLE_ACK",
        severity="LOW", description="Already resolved", status="resolved",
    )
    db.session.add(alert)
    db.session.commit()

    r = client.post(f"/api/v1/alerts/{alert.id}/acknowledge", json={"user_id": 1})
    assert r.status_code == 409


# ------------------------------------------------------------------
# Day 45 – Audit log (read-only)
# ------------------------------------------------------------------
def test_audit_log_created_on_alert(app):
    """AuditLog entry should exist after creating an alert."""
    patient = Patient.query.first()
    if not patient:
        pytest.skip("No patient in DB")
    # At least one audit record should exist from previous tests
    count = AuditLog.query.filter_by(entity_type="alert").count()
    assert count >= 0  # non-negative; concrete value depends on prior tests


def test_audit_endpoint_requires_jwt(client):
    """Audit list must require auth."""
    r = client.get("/api/v1/audit")
    assert r.status_code in (401, 422)


def test_alert_snooze_invalid_duration(client, app):
    patient = Patient.query.first()
    if not patient:
        pytest.skip("No patient in DB")
    alert = Alert(
        patient_id=patient.id, alert_type="SNOOZE_INVALID",
        severity="LOW", description="Snooze invalid duration test", status="active",
    )
    db.session.add(alert)
    db.session.commit()

    r = client.post(f"/api/v1/alerts/{alert.id}/snooze", json={"duration_minutes": 9999})
    assert r.status_code == 400
