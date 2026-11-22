from datetime import datetime, timezone, date
from flask import Blueprint, jsonify, request
from app.models import Patient, Admission, Bed
from app import db

patients_bp = Blueprint("patients", __name__, url_prefix="/api/v1/patients")


@patients_bp.route("", methods=["GET"])
def get_patients():
    """Retrieve all patients with query filters."""
    status_filter = request.args.get("status")  # e.g., 'admitted'
    query = Patient.query

    if status_filter:
        query = query.join(Admission).filter(Admission.status == status_filter)

    patients = query.all()
    results = []
    for p in patients:
        p_dict = p.to_dict()
        # Find active admission and bed
        active_adm = next((a for a in p.admissions if a.status == "admitted"), None)
        if active_adm:
            p_dict["active_bed"] = {
                "bed_id": active_adm.bed.id,
                "bed_number": active_adm.bed.bed_number,
                "icu_unit": active_adm.bed.icu_unit.name if active_adm.bed.icu_unit else None,
                "admission_date": active_adm.admission_date.isoformat(),
            }
        else:
            p_dict["active_bed"] = None
        results.append(p_dict)

    return jsonify({
        "success": True,
        "count": len(results),
        "data": results,
    }), 200


@patients_bp.route("/<int:patient_id>", methods=["GET"])
def get_patient(patient_id):
    """Retrieve single patient by ID with complete clinical overview."""
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({"success": False, "error": "Patient not found"}), 404

    patient_dict = patient.to_dict()

    # Active admission details
    active_adm = next((a for a in patient.admissions if a.status == "admitted"), None)
    admission_data = (
        {
            "id": active_adm.id,
            "admission_id": active_adm.id,
            "bed_id": active_adm.bed.id,
            "bed_number": active_adm.bed.bed_number,
            "icu_unit": active_adm.bed.icu_unit.name if active_adm.bed.icu_unit else None,
            "admission_date": active_adm.admission_date.isoformat(),
            "status": active_adm.status,
        }
        if active_adm
        else None
    )
    patient_dict["admission"] = admission_data
    patient_dict["active_admission"] = admission_data


    # Latest vitals snapshot
    latest_vital = (
        patient.vitals[-1].to_dict() if len(patient.vitals) > 0 else None
    )
    patient_dict["latest_vitals"] = latest_vital

    # Active alerts count
    active_alerts = [a.to_dict() for a in patient.alerts if a.status == "active"]
    patient_dict["active_alerts_count"] = len(active_alerts)
    patient_dict["active_alerts"] = active_alerts

    return jsonify({"success": True, "data": patient_dict}), 200


@patients_bp.route("", methods=["POST"])
def create_patient():
    """Register a new patient and optionally assign an ICU bed."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body must be JSON"}), 400

    patient_code = data.get("patient_code")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    dob_str = data.get("date_of_birth")
    gender = data.get("gender")
    bed_id = data.get("bed_id")

    if not patient_code or not first_name:
        return jsonify({"success": False, "error": "patient_code and first_name are required"}), 400

    if Patient.query.filter_by(patient_code=patient_code).first():
        return jsonify({"success": False, "error": "patient_code already exists"}), 409

    dob = None
    if dob_str:
        try:
            dob = date.fromisoformat(dob_str)
        except ValueError:
            pass

    patient = Patient(
        patient_code=patient_code,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=dob,
        gender=gender,
    )
    db.session.add(patient)
    db.session.flush()

    if bed_id:
        bed = db.session.get(Bed, bed_id)
        if not bed:
            db.session.rollback()
            return jsonify({"success": False, "error": f"Bed ID {bed_id} not found"}), 404
        if bed.status == "occupied":
            db.session.rollback()
            return jsonify({"success": False, "error": f"Bed {bed.bed_number} is already occupied"}), 400

        bed.status = "occupied"
        admission = Admission(
            patient_id=patient.id,
            bed_id=bed.id,
            status="admitted",
        )
        db.session.add(admission)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Patient registered successfully",
        "data": patient.to_dict(),
    }), 201


@patients_bp.route("/<int:patient_id>/discharge", methods=["POST"])
def discharge_patient(patient_id):
    """Discharge an admitted patient and release their ICU bed."""
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({"success": False, "error": "Patient not found"}), 404

    active_adm = next((a for a in patient.admissions if a.status == "admitted"), None)
    if not active_adm:
        return jsonify({"success": False, "error": "Patient is not currently admitted"}), 400

    active_adm.status = "discharged"
    active_adm.discharge_date = datetime.now(timezone.utc)

    # Free the bed
    bed = active_adm.bed
    if bed:
        bed.status = "available"

    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Patient {patient.patient_code} discharged successfully. Bed {bed.bed_number} is now available.",
    }), 200
