from flask import Blueprint, jsonify, request
from app.models import Bed, ICUUnit, Admission, Patient
from app import db

beds_bp = Blueprint("beds", __name__, url_prefix="/api/v1/beds")


@beds_bp.route("", methods=["GET"])
def get_beds():
    """Retrieve all ICU beds with unit info, status, and current admitted patient."""
    status_filter = request.args.get("status")
    unit_id = request.args.get("icu_unit_id", type=int)

    query = Bed.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if unit_id:
        query = query.filter_by(icu_unit_id=unit_id)

    beds = query.all()
    results = []
    for b in beds:
        b_dict = b.to_dict()
        b_dict["icu_unit_name"] = b.icu_unit.name if b.icu_unit else None

        active_adm = next((a for a in b.admissions if a.status == "admitted"), None)
        if active_adm:
            b_dict["current_patient"] = {
                "patient_id": active_adm.patient.id,
                "patient_code": active_adm.patient.patient_code,
                "full_name": f"{active_adm.patient.first_name} {active_adm.patient.last_name or ''}".strip(),
                "admission_date": active_adm.admission_date.isoformat(),
            }
        else:
            b_dict["current_patient"] = None

        results.append(b_dict)

    return jsonify({
        "success": True,
        "count": len(results),
        "data": results,
    }), 200


@beds_bp.route("/<int:bed_id>", methods=["GET"])
def get_bed(bed_id):
    """Retrieve a single bed's current occupancy and assigned medical devices."""
    bed = db.session.get(Bed, bed_id)
    if not bed:
        return jsonify({"success": False, "error": "Bed not found"}), 404

    b_dict = bed.to_dict()
    b_dict["icu_unit_name"] = bed.icu_unit.name if bed.icu_unit else None

    active_adm = next((a for a in bed.admissions if a.status == "admitted"), None)
    b_dict["current_patient"] = (
        {
            "patient_id": active_adm.patient.id,
            "patient_code": active_adm.patient.patient_code,
            "full_name": f"{active_adm.patient.first_name} {active_adm.patient.last_name or ''}".strip(),
            "admission_date": active_adm.admission_date.isoformat(),
        }
        if active_adm
        else None
    )

    # Active assigned devices
    active_devices = []
    for da in bed.device_assignments:
        if da.unassigned_at is None:
            active_devices.append({
                "device_id": da.device.id,
                "device_code": da.device.device_code,
                "model": da.device.model,
                "status": da.device.connection_status,
            })
    b_dict["assigned_devices"] = active_devices

    return jsonify({"success": True, "data": b_dict}), 200


@beds_bp.route("/<int:bed_id>/status", methods=["PATCH"])
def update_bed_status(bed_id):
    """Update bed maintenance or availability status."""
    bed = db.session.get(Bed, bed_id)
    if not bed:
        return jsonify({"success": False, "error": "Bed not found"}), 404

    data = request.get_json()
    new_status = data.get("status")
    if new_status not in ["available", "occupied", "maintenance"]:
        return jsonify({
            "success": False,
            "error": "Invalid status. Must be available, occupied, or maintenance",
        }), 400

    bed.status = new_status
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Bed {bed.bed_number} status updated to {new_status}",
        "data": bed.to_dict(),
    }), 200
