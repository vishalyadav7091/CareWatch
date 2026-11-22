import random
from datetime import datetime, timezone


class PatientTelemetrySimulator:
    """Generates synthetic physiological telemetry for ICU patients.
    
    Clearly labels all readings as simulated data to avoid clinical confusion.
    """

    SCENARIOS = {
        "stable": {
            "hr": (65.0, 85.0),
            "spo2": (97.0, 100.0),
            "sbp": (110.0, 128.0),
            "dbp": (70.0, 82.0),
            "rr": (12.0, 18.0),
            "temp": (36.6, 37.2),
        },
        "arrhythmia_tachycardia": {
            "hr": (125.0, 155.0),
            "spo2": (93.0, 97.0),
            "sbp": (135.0, 160.0),
            "dbp": (85.0, 98.0),
            "rr": (20.0, 26.0),
            "temp": (37.0, 37.6),
        },
        "desaturation_hypoxia": {
            "hr": (95.0, 120.0),
            "spo2": (82.0, 89.0),
            "sbp": (100.0, 125.0),
            "dbp": (60.0, 78.0),
            "rr": (26.0, 36.0),
            "temp": (36.8, 37.5),
        },
        "septic_shock": {
            "hr": (115.0, 140.0),
            "spo2": (91.0, 95.0),
            "sbp": (75.0, 90.0),
            "dbp": (45.0, 58.0),
            "rr": (24.0, 32.0),
            "temp": (38.8, 40.1),
        },
    }

    @classmethod
    def generate_reading(cls, patient_id, device_id=None, scenario="stable"):
        """Generate a single physiological observation dictionary."""
        ranges = cls.SCENARIOS.get(scenario, cls.SCENARIOS["stable"])

        def _val(r):
            return round(random.uniform(r[0], r[1]), 2)

        return {
            "patient_id": patient_id,
            "device_id": device_id,
            "heart_rate": _val(ranges["hr"]),
            "spo2": _val(ranges["spo2"]),
            "systolic_bp": _val(ranges["sbp"]),
            "diastolic_bp": _val(ranges["dbp"]),
            "respiratory_rate": _val(ranges["rr"]),
            "temperature": _val(ranges["temp"]),
            "measurement_source": "simulator",
            "scenario": scenario,
            "data_quality": "valid",
            "measured_at": datetime.now(timezone.utc).isoformat(),
        }

