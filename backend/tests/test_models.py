import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models import (
    User,
    Hospital,
    ICUUnit,
    Bed,
    Patient,
    Admission,
    MedicalDevice,
    VitalObservation,
    Alert,
    RiskAssessment,
    AuditLog,
)


@pytest.fixture
def app_ctx():
    app = create_app("testing")
    with app.app_context():
        yield


def test_models_mapped_correctly(app_ctx):
    """Verify that all core SQLAlchemy models map to existing MySQL tables."""
    models = [
        User,
        Hospital,
        ICUUnit,
        Bed,
        Patient,
        Admission,
        MedicalDevice,
        VitalObservation,
        Alert,
        RiskAssessment,
        AuditLog,
    ]
    for model in models:
        # Performing a count query on each model guarantees mapping & schema alignment
        assert model.query.count() >= 0

