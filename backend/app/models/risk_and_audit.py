from datetime import datetime, timezone
from app import db


class RiskAssessment(db.Model):
    __tablename__ = "risk_assessments"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    patient_id = db.Column(
        db.BigInteger, db.ForeignKey("patients.id"), nullable=False
    )
    model_name = db.Column(db.String(100), nullable=True)
    model_version = db.Column(db.String(50), nullable=True)
    risk_score = db.Column(db.Numeric(7, 4), nullable=True)
    risk_category = db.Column(db.String(50), nullable=True)
    assessment_status = db.Column(
        db.Enum("not_configured", "demonstration", "validated", name="assessment_status_enum"),
        default="not_configured",
    )
    assessed_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "risk_score": float(self.risk_score) if self.risk_score is not None else None,
            "risk_category": self.risk_category,
            "assessment_status": self.assessment_status,
            "assessed_at": self.assessed_at.isoformat() if self.assessed_at else None,
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.BigInteger, db.ForeignKey("users.id"), nullable=True
    )
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(100), nullable=True)
    entity_id = db.Column(db.BigInteger, nullable=True)
    details = db.Column(db.JSON, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

