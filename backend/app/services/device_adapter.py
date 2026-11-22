from abc import ABC, abstractmethod
from datetime import datetime, timezone


class BaseDeviceAdapter(ABC):
    """Abstract device adapter interface for ICU monitors."""

    @abstractmethod
    def parse_payload(self, raw_data):
        """Parse raw device transmission into CareWatch standard format."""
        pass


class IntelliVueDeviceAdapter(BaseDeviceAdapter):
    """Adapter for Philips IntelliVue series monitors or mock simulator streams."""

    def parse_payload(self, raw_data):
        if not isinstance(raw_data, dict):
            raise ValueError("Raw payload must be a JSON dictionary")

        measured_at = raw_data.get("timestamp") or datetime.now(timezone.utc).isoformat()

        return {
            "device_code": raw_data.get("device_code") or raw_data.get("deviceId"),
            "patient_code": raw_data.get("patient_code") or raw_data.get("patientId"),
            "heart_rate": raw_data.get("hr") or raw_data.get("heart_rate"),
            "spo2": raw_data.get("spo2") or raw_data.get("pulse_ox"),
            "systolic_bp": raw_data.get("sbp") or raw_data.get("bp_sys"),
            "diastolic_bp": raw_data.get("dbp") or raw_data.get("bp_dia"),
            "respiratory_rate": raw_data.get("rr") or raw_data.get("resp_rate"),
            "temperature": raw_data.get("temp") or raw_data.get("temperature"),
            "measured_at": measured_at,
            "measurement_source": "intellivue_adapter",
        }

