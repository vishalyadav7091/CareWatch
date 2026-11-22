from datetime import datetime, timezone
from app import db


class Hospital(db.Model):
    __tablename__ = "hospitals"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.Text, nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    icu_units = db.relationship("ICUUnit", backref="hospital", lazy=True)
    doctors = db.relationship("Doctor", backref="hospital", lazy=True)
    nurses = db.relationship("Nurse", backref="hospital", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "contact_number": self.contact_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ICUUnit(db.Model):
    __tablename__ = "icu_units"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    hospital_id = db.Column(
        db.BigInteger, db.ForeignKey("hospitals.id"), nullable=False
    )
    name = db.Column(db.String(100), nullable=False)
    unit_type = db.Column(db.String(50), nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    beds = db.relationship("Bed", backref="icu_unit", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "hospital_id": self.hospital_id,
            "name": self.name,
            "unit_type": self.unit_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Bed(db.Model):
    __tablename__ = "beds"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    icu_unit_id = db.Column(
        db.BigInteger, db.ForeignKey("icu_units.id"), nullable=False
    )
    bed_number = db.Column(db.String(20), nullable=False)
    status = db.Column(
        db.Enum("available", "occupied", "maintenance", name="bed_status_enum"),
        default="available",
    )

    # Relationships
    admissions = db.relationship("Admission", backref="bed", lazy=True)
    device_assignments = db.relationship(
        "DeviceAssignment", backref="bed", lazy=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "icu_unit_id": self.icu_unit_id,
            "bed_number": self.bed_number,
            "status": self.status,
        }


class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, unique=True, nullable=False)
    hospital_id = db.Column(
        db.BigInteger, db.ForeignKey("hospitals.id"), nullable=False
    )
    specialization = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "hospital_id": self.hospital_id,
            "specialization": self.specialization,
        }


class Nurse(db.Model):
    __tablename__ = "nurses"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, unique=True, nullable=False)
    hospital_id = db.Column(
        db.BigInteger, db.ForeignKey("hospitals.id"), nullable=False
    )
    department = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "hospital_id": self.hospital_id,
            "department": self.department,
        }

