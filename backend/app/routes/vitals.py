from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
from app.models import VitalObservation, Patient
from app import db

vitals_bp = Blueprint("vitals", __name__, url_prefix="/api/v1/vitals")


@vitals_bp.route("/patient/<int:patient_id>", methods=["GET"])
def get_patient_vitals(patient_id):
    """Retrieve recent vitals for a patient."""
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({
            "success": False,
            "error": "Patient not found",
        }), 404

    limit = request.args.get("limit", 50, type=int)
    vitals = (
        VitalObservation.query.filter_by(patient_id=patient_id)
        .order_by(VitalObservation.measured_at.desc())
        .limit(limit)
        .all()
    )

    return jsonify({
        "success": True,
        "patient_id": patient_id,
        "count": len(vitals),
        "data": [v.to_dict() for v in vitals],
    }), 200


@vitals_bp.route("", methods=["POST"])
def record_vital():
    """Record a new vital observation (simulated or real device reading)."""
    payload = request.get_json()
    if not payload:
        return jsonify({"success": False, "error": "Request body must be JSON"}), 400

    patient_id = payload.get("patient_id")
    if not patient_id:
        return jsonify({"success": False, "error": "patient_id is required"}), 400

    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({"success": False, "error": "Patient does not exist"}), 404

    measured_at_str = payload.get("measured_at")
    if measured_at_str:
        try:
            measured_at = datetime.fromisoformat(measured_at_str.replace("Z", "+00:00"))
        except ValueError:
            measured_at = datetime.now(timezone.utc)
    else:
        measured_at = datetime.now(timezone.utc)

    vital = VitalObservation(
        patient_id=patient_id,
        device_id=payload.get("device_id"),
        heart_rate=payload.get("heart_rate"),
        spo2=payload.get("spo2"),
        systolic_bp=payload.get("systolic_bp"),
        diastolic_bp=payload.get("diastolic_bp"),
        respiratory_rate=payload.get("respiratory_rate"),
        temperature=payload.get("temperature"),
        measurement_source=payload.get("measurement_source", "simulator"),
        data_quality=payload.get("data_quality", "valid"),
        measured_at=measured_at,
    )

    db.session.add(vital)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Vital observation recorded successfully",
        "data": vital.to_dict(),
    }), 201
