from datetime import datetime, timezone
from app import db


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    patient_code = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(30), nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    admissions = db.relationship("Admission", backref="patient", lazy=True)
    vitals = db.relationship("VitalObservation", backref="patient", lazy=True)
    alerts = db.relationship("Alert", backref="patient", lazy=True)
    risk_assessments = db.relationship("RiskAssessment", backref="patient", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "patient_code": self.patient_code,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Admission(db.Model):
    __tablename__ = "admissions"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    patient_id = db.Column(
        db.BigInteger, db.ForeignKey("patients.id"), nullable=False
    )
    bed_id = db.Column(db.BigInteger, db.ForeignKey("beds.id"), nullable=False)
    admission_date = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    discharge_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(
        db.Enum("admitted", "discharged", "transferred", name="admission_status_enum"),
        default="admitted",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "bed_id": self.bed_id,
            "admission_date": self.admission_date.isoformat() if self.admission_date else None,
            "discharge_date": self.discharge_date.isoformat() if self.discharge_date else None,
            "status": self.status,
        }

