import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.services.simulator import PatientTelemetrySimulator
from app.services.device_adapter import IntelliVueDeviceAdapter
from app.services.validator import VitalValidator
from app.services.normalizer import VitalNormalizer


@pytest.fixture
def client():
    app = create_app("testing")
    with app.test_client() as client:
        yield client


def test_synthetic_data_simulator():
    """Day 15: Test synthetic patient data generation across clinical scenarios."""
    scenarios = ["stable", "arrhythmia_tachycardia", "desaturation_hypoxia", "septic_shock"]
    for sc in scenarios:
        reading = PatientTelemetrySimulator.generate_reading(patient_id=1, scenario=sc)
        assert reading["patient_id"] == 1
        assert reading["measurement_source"] == "simulator"
        assert reading["heart_rate"] is not None
        assert reading["spo2"] is not None
        assert reading["systolic_bp"] > reading["diastolic_bp"]


def test_device_adapter():
    """Day 16: Test Philips IntelliVue adapter decoding raw packet."""
    raw_packet = {
        "deviceId": "DEV-ICU-001",
        "patientId": "PAT-2026-001",
        "hr": 92.5,
        "pulse_ox": 98.0,
        "bp_sys": 118.0,
        "bp_dia": 76.0,
        "resp_rate": 15.0,
        "temp": 36.9,
    }
    adapter = IntelliVueDeviceAdapter()
    parsed = adapter.parse_payload(raw_packet)
    assert parsed["device_code"] == "DEV-ICU-001"
    assert parsed["heart_rate"] == 92.5
    assert parsed["spo2"] == 98.0


def test_vital_validation_engine():
    """Day 17: Test biological range and systolic/diastolic validity checks."""
    valid_reading = {"heart_rate": 80, "spo2": 99, "systolic_bp": 120, "diastolic_bp": 80}
    is_valid, status, errors = VitalValidator.validate(valid_reading)
    assert is_valid is True
    assert status == "valid"

    # Invalid: heart rate out of biological limits
    invalid_hr = {"heart_rate": 500}
    is_valid, status, errors = VitalValidator.validate(invalid_hr)
    assert is_valid is False
    assert status == "invalid"
    assert any("out of biological bounds" in e for e in errors)

    # Invalid: inverted blood pressure
    inverted_bp = {"systolic_bp": 80, "diastolic_bp": 120}
    is_valid, status, errors = VitalValidator.validate(inverted_bp)
    assert is_valid is False
    assert any("greater than Diastolic" in e for e in errors)


def test_vital_normalizer():
    """Day 18: Test timestamp normalization and unit conversions."""
    # Fahrenheit to Celsius conversion
    f_reading = {"temperature": 98.6, "temp_unit": "F"}
    norm = VitalNormalizer.normalize_reading(f_reading)
    assert norm["temperature"] == 37.0  # (98.6 - 32) * 5/9 = 37.0


def test_acquisition_api_and_mysql_storage(client):
    """Day 19 & 20: Test end-to-end ingestion and persistence in MySQL."""
    # 1. Trigger simulation API endpoint
    sim_res = client.post("/api/v1/acquisition/simulate/1?scenario=arrhythmia_tachycardia")
    assert sim_res.status_code == 201
    sim_data = sim_res.get_json()
    assert sim_data["success"] is True
    assert sim_data["scenario"] == "arrhythmia_tachycardia"
    assert sim_data["data"]["heart_rate"] >= 120.0

    # 2. Trigger IntelliVue adapter ingestion endpoint
    adapter_res = client.post("/api/v1/acquisition/adapter/intellivue", json={
        "deviceId": "DEV-ICU-001",
        "patientId": "PAT-2026-001",
        "hr": 85.0,
        "pulse_ox": 99.0,
        "bp_sys": 122.0,
        "bp_dia": 78.0,
        "resp_rate": 16.0,
        "temp": 37.0,
    })
    assert adapter_res.status_code == 201
    adapter_data = adapter_res.get_json()
    assert adapter_data["success"] is True
    assert adapter_data["data"]["heart_rate"] == 85.0

    # 3. Verify both entries exist in database via vitals API
    vitals_res = client.get("/api/v1/vitals/patient/1?limit=10")
    assert vitals_res.status_code == 200
    assert vitals_res.get_json()["count"] >= 3

