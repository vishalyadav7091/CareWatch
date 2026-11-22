from datetime import datetime, timezone
from app import db


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    patient_id = db.Column(
        db.BigInteger, db.ForeignKey("patients.id"), nullable=False
    )
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(30), nullable=True)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.Enum("active", "acknowledged", "resolved", name="alert_status_enum"),
        default="active",
    )
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    acknowledgements = db.relationship(
        "AlertAcknowledgement", backref="alert", lazy=True
    )

    def to_dict(self):
        latest_ack = (
            self.acknowledgements[-1].to_dict()
            if self.acknowledgements else None
        )
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "latest_acknowledgement": latest_ack,
        }


class AlertAcknowledgement(db.Model):
    __tablename__ = "alert_acknowledgements"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    alert_id = db.Column(
        db.BigInteger, db.ForeignKey("alerts.id"), nullable=False
    )
    user_id = db.Column(db.BigInteger, nullable=False)
    acknowledged_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    remarks = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "user_id": self.user_id,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "remarks": self.remarks,
        }

