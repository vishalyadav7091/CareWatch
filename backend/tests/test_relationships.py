import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models import (
    Hospital,
    ICUUnit,
    Bed,
    Patient,
    Admission,
    MedicalDevice,
    DeviceAssignment,
    VitalObservation,
)


@pytest.fixture
def app_ctx():
    app = create_app("testing")
    with app.app_context():
        yield


def test_database_relationships_navigation(app_ctx):
    """Test navigating through ORM relationships across Hospital, Bed, Patient, and Vitals."""
    # Find patient
    patient = Patient.query.filter_by(patient_code="PAT-2026-001").first()
    assert patient is not None
    assert patient.first_name == "John"
    assert patient.last_name == "Doe"

    # Navigate to admission and bed
    assert len(patient.admissions) > 0
    admission = patient.admissions[0]
    assert admission.status == "admitted"
    assert admission.bed.bed_number == "ICU-01"

    # Navigate bed -> ICU unit -> hospital
    icu_unit = admission.bed.icu_unit
    assert icu_unit.name == "Main ICU - Ward A"
    assert icu_unit.hospital.name == "City General Hospital"

    # Navigate patient -> vitals
    assert len(patient.vitals) > 0
    vital = patient.vitals[0]
    assert float(vital.heart_rate) == 78.50
    assert float(vital.spo2) == 98.00
    assert float(vital.systolic_bp) == 120.00
    assert float(vital.diastolic_bp) == 80.00
    assert vital.measurement_source == "simulator"

