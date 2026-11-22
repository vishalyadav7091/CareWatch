from app import db
from app.models import VitalObservation, Patient, MedicalDevice
from app.services.validator import VitalValidator
from app.services.normalizer import VitalNormalizer


class IngestionPipeline:
    """End-to-end telemetry ingestion pipeline for MySQL."""

    @classmethod
    def ingest_reading(cls, raw_reading):
        """Validates, normalizes, and stores a single vital reading."""
        # 1. Normalize
        normalized = VitalNormalizer.normalize_reading(raw_reading)

        # 2. Validate
        is_valid, quality_status, errors = VitalValidator.validate(normalized)
        normalized["data_quality"] = quality_status

        # 3. Resolve Patient and Device
        patient_id = normalized.get("patient_id")
        if not patient_id and raw_reading.get("patient_code"):
            p = Patient.query.filter_by(patient_code=raw_reading["patient_code"]).first()
            if p:
                patient_id = p.id
                normalized["patient_id"] = patient_id

        device_id = normalized.get("device_id")
        if not device_id and raw_reading.get("device_code"):
            d = MedicalDevice.query.filter_by(device_code=raw_reading["device_code"]).first()
            if d:
                device_id = d.id
                normalized["device_id"] = device_id

        if not patient_id:
            return False, "Patient identifier required", None

        # 4. Insert into MySQL
        vital = VitalObservation(
            patient_id=patient_id,
            device_id=device_id,
            heart_rate=normalized["heart_rate"],
            spo2=normalized["spo2"],
            systolic_bp=normalized["systolic_bp"],
            diastolic_bp=normalized["diastolic_bp"],
            respiratory_rate=normalized["respiratory_rate"],
            temperature=normalized["temperature"],
            measurement_source=normalized["measurement_source"],
            data_quality=normalized["data_quality"],
            measured_at=normalized["measured_at"],
        )
        db.session.add(vital)
        db.session.commit()

        # Phase 7: Trigger demo alert engine (non-blocking, best-effort)
        try:
            from app.services.alert_engine import evaluate_patient_alerts
            evaluate_patient_alerts(patient_id, vital.to_dict())
        except Exception as ae:
            print(f"[AlertEngine] {ae}")

        return True, "Ingested successfully", vital.to_dict()

    @classmethod
    def bulk_ingest(cls, readings_list):
        """Batch ingestion for high-throughput streaming."""
        records = []
        for raw in readings_list:
            norm = VitalNormalizer.normalize_reading(raw)
            _, quality, _ = VitalValidator.validate(norm)
            records.append(
                VitalObservation(
                    patient_id=norm["patient_id"],
                    device_id=norm.get("device_id"),
                    heart_rate=norm["heart_rate"],
                    spo2=norm["spo2"],
                    systolic_bp=norm["systolic_bp"],
                    diastolic_bp=norm["diastolic_bp"],
                    respiratory_rate=norm["respiratory_rate"],
                    temperature=norm["temperature"],
                    measurement_source=norm["measurement_source"],
                    data_quality=quality,
                    measured_at=norm["measured_at"],
                )
            )
        db.session.bulk_save_objects(records)
        db.session.commit()
        return len(records)

