from datetime import datetime, timezone
from app import db


class MedicalDevice(db.Model):
    __tablename__ = "medical_devices"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    device_code = db.Column(db.String(50), unique=True, nullable=False)
    manufacturer = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    device_type = db.Column(db.String(100), nullable=True)
    connection_status = db.Column(
        db.Enum("connected", "disconnected", "unknown", name="device_status_enum"),
        default="unknown",
    )
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    assignments = db.relationship("DeviceAssignment", backref="device", lazy=True)
    vitals = db.relationship("VitalObservation", backref="device", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "device_code": self.device_code,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "device_type": self.device_type,
            "connection_status": self.connection_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DeviceAssignment(db.Model):
    __tablename__ = "device_assignments"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    device_id = db.Column(
        db.BigInteger, db.ForeignKey("medical_devices.id"), nullable=False
    )
    bed_id = db.Column(db.BigInteger, db.ForeignKey("beds.id"), nullable=False)
    assigned_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    unassigned_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "bed_id": self.bed_id,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "unassigned_at": self.unassigned_at.isoformat() if self.unassigned_at else None,
        }

