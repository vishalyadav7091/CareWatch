from datetime import datetime, timezone
from app import db


class VitalObservation(db.Model):
    __tablename__ = "vital_observations"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    patient_id = db.Column(
        db.BigInteger, db.ForeignKey("patients.id"), nullable=False
    )
    device_id = db.Column(
        db.BigInteger, db.ForeignKey("medical_devices.id"), nullable=True
    )
    heart_rate = db.Column(db.Numeric(6, 2), nullable=True)
    spo2 = db.Column(db.Numeric(5, 2), nullable=True)
    systolic_bp = db.Column(db.Numeric(6, 2), nullable=True)
    diastolic_bp = db.Column(db.Numeric(6, 2), nullable=True)
    respiratory_rate = db.Column(db.Numeric(6, 2), nullable=True)
    temperature = db.Column(db.Numeric(5, 2), nullable=True)
    measurement_source = db.Column(db.String(50), nullable=False, default="simulator")
    data_quality = db.Column(
        db.Enum("valid", "invalid", "delayed", "missing", name="vital_quality_enum"),
        default="valid",
    )
    measured_at = db.Column(db.DateTime, nullable=False)
    received_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "device_id": self.device_id,
            "heart_rate": float(self.heart_rate) if self.heart_rate is not None else None,
            "spo2": float(self.spo2) if self.spo2 is not None else None,
            "systolic_bp": float(self.systolic_bp) if self.systolic_bp is not None else None,
            "diastolic_bp": float(self.diastolic_bp) if self.diastolic_bp is not None else None,
            "respiratory_rate": float(self.respiratory_rate) if self.respiratory_rate is not None else None,
            "temperature": float(self.temperature) if self.temperature is not None else None,
            "measurement_source": self.measurement_source,
            "data_quality": self.data_quality,
            "measured_at": self.measured_at.isoformat() if self.measured_at else None,
            "received_at": self.received_at.isoformat() if self.received_at else None,
        }

