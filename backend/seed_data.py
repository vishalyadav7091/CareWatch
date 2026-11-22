import os
import sys
from datetime import datetime, timezone, date
import bcrypt

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import create_app, db
from app.models import (
    User,
    Hospital,
    ICUUnit,
    Bed,
    Doctor,
    Nurse,
    Patient,
    Admission,
    MedicalDevice,
    DeviceAssignment,
    VitalObservation,
    Alert,
)


def seed_demo_data(config_name="development"):
    """Seed initial reference data for CareWatch ICU demo."""
    app = create_app(config_name)
    with app.app_context():
        db.create_all()
        print(f"Checking existing records in {config_name} database...")

        # 1. Hospital
        hospital = Hospital.query.filter_by(name="City General Hospital").first()
        if not hospital:
            hospital = Hospital(
                name="City General Hospital",
                address="742 Evergreen Terrace, Medical District",
                contact_number="+1-555-0199",
            )
            db.session.add(hospital)
            db.session.commit()
            print(f"Created Hospital: {hospital.name} (ID: {hospital.id})")
        else:
            print(f"Hospital exists: {hospital.name} (ID: {hospital.id})")

        # 1b. Clinical & Administrative Staff (Doctors, Nurses, Admin)
        default_pwd_hash = bcrypt.hashpw(b"Password#123", bcrypt.gensalt()).decode("utf-8")
        demo_staff = [
            ("doctor.smith@carewatch.local", "Dr. Sarah Smith", "doctor", "doc", "Critical Care Medicine / Intensivist"),
            ("doctor.kumar@carewatch.local", "Dr. Rajesh Kumar", "doctor", "doc", "Cardiology & Hemodynamic Monitoring"),
            ("doctor.chen@carewatch.local", "Dr. Emily Chen", "doctor", "doc", "Pulmonology & Neuro-Critical Care"),
            ("nurse.jack@carewatch.local", "Nurse Jack Robinson", "nurse", "nurse", "ICU Critical Care Nursing - Head Nurse"),
            ("nurse.priya@carewatch.local", "Nurse Priya Sharma", "nurse", "nurse", "ICU Night Shift Staff Nurse"),
            ("nurse.david@carewatch.local", "Nurse David Miller", "nurse", "nurse", "Trauma & Resuscitation Specialist"),
            ("admin@carewatch.local", "System Administrator", "admin", "admin", "Hospital IT & Biomedical Informatics"),
        ]
        for email, full_name, role, staff_type, spec_dept in demo_staff:
            u = User.query.filter_by(email=email).first()
            if not u:
                u = User(
                    full_name=full_name,
                    email=email,
                    password_hash=default_pwd_hash,
                    role=role,
                    is_active=True,
                )
                db.session.add(u)
                db.session.commit()
                print(f"Created User: {email} ({role})")
            else:
                u.full_name = full_name
                u.password_hash = default_pwd_hash
                u.is_active = True
                db.session.commit()
                print(f"User exists & verified: {email} ({role})")

            if staff_type == "doc":
                doc = Doctor.query.filter_by(user_id=u.id).first()
                if not doc:
                    doc = Doctor(user_id=u.id, hospital_id=hospital.id, specialization=spec_dept)
                    db.session.add(doc)
                    db.session.commit()
                else:
                    doc.specialization = spec_dept
                    db.session.commit()
            elif staff_type == "nurse":
                nur = Nurse.query.filter_by(user_id=u.id).first()
                if not nur:
                    nur = Nurse(user_id=u.id, hospital_id=hospital.id, department=spec_dept)
                    db.session.add(nur)
                    db.session.commit()
                else:
                    nur.department = spec_dept
                    db.session.commit()

        # 2. ICU Unit
        icu = ICUUnit.query.filter_by(name="Main ICU - Ward A", hospital_id=hospital.id).first()
        if not icu:
            icu = ICUUnit(
                hospital_id=hospital.id,
                name="Main ICU - Ward A",
                unit_type="Cardiovascular / Critical Care",
            )
            db.session.add(icu)
            db.session.commit()
            print(f"Created ICU Unit: {icu.name} (ID: {icu.id})")
        else:
            print(f"ICU Unit exists: {icu.name} (ID: {icu.id})")

        # 3. Beds (ICU-01 through ICU-04)
        for i in range(1, 5):
            bed_num = f"ICU-{i:02d}"
            bed = Bed.query.filter_by(bed_number=bed_num, icu_unit_id=icu.id).first()
            if not bed:
                bed = Bed(
                    icu_unit_id=icu.id,
                    bed_number=bed_num,
                    status="available" if i > 1 else "occupied",
                )
                db.session.add(bed)
                db.session.commit()
                print(f"Created Bed: {bed.bed_number}")

        # 4. Medical Device
        device = MedicalDevice.query.filter_by(device_code="DEV-ICU-001").first()
        if not device:
            device = MedicalDevice(
                device_code="DEV-ICU-001",
                manufacturer="Philips Healthcare",
                model="IntelliVue MX800",
                device_type="Bedside Multi-Parameter Monitor",
                connection_status="connected",
            )
            db.session.add(device)
            db.session.commit()
            print(f"Created Device: {device.device_code}")

        # 5. Patient
        patient = Patient.query.filter_by(patient_code="PAT-2026-001").first()
        if not patient:
            patient = Patient(
                patient_code="PAT-2026-001",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1965, 8, 14),
                gender="Male",
            )
            db.session.add(patient)
            db.session.commit()
            print(f"Created Patient: {patient.first_name} {patient.last_name} ({patient.patient_code})")

        # 6. Admission
        bed_1 = Bed.query.filter_by(bed_number="ICU-01", icu_unit_id=icu.id).first()
        admission = Admission.query.filter_by(patient_id=patient.id, bed_id=bed_1.id).first()
        if not admission:
            admission = Admission(
                patient_id=patient.id,
                bed_id=bed_1.id,
                status="admitted",
            )
            db.session.add(admission)
            db.session.commit()
            print(f"Created Admission for {patient.patient_code} in {bed_1.bed_number}")

        # 7. Device Assignment
        assignment = DeviceAssignment.query.filter_by(device_id=device.id, bed_id=bed_1.id).first()
        if not assignment:
            assignment = DeviceAssignment(
                device_id=device.id,
                bed_id=bed_1.id,
            )
            db.session.add(assignment)
            db.session.commit()
            print(f"Assigned device {device.device_code} to {bed_1.bed_number}")

        # 8. Sample Baseline Vital Observation
        vital = VitalObservation.query.filter_by(patient_id=patient.id).first()
        if not vital:
            vital = VitalObservation(
                patient_id=patient.id,
                device_id=device.id,
                heart_rate=78.50,
                spo2=98.00,
                systolic_bp=120.00,
                diastolic_bp=80.00,
                respiratory_rate=16.00,
                temperature=37.10,
                measurement_source="simulator",
                data_quality="valid",
                measured_at=datetime.now(timezone.utc),
            )
            db.session.add(vital)
            db.session.commit()
            print(f"Created baseline vital observation for {patient.patient_code}")

        print("Seed verification completed successfully!")


if __name__ == "__main__":
    seed_demo_data()

