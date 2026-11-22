from flask import Blueprint, jsonify, request
from datetime import datetime, timezone, timedelta
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.models import Alert, AlertAcknowledgement, Patient, User
from app import db
from app.services.audit_service import log_action

alerts_bp = Blueprint("alerts", __name__, url_prefix="/api/v1/alerts")


def _current_user_id():
    """Extract user_id from JWT if present, else return None."""
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        return int(identity) if identity else None
    except Exception:
        return None


@alerts_bp.route("", methods=["GET"])
def get_alerts():
    """Retrieve alerts with status, severity, patient, ward filters."""
    status_filter = request.args.get("status", "active")
    severity_filter = request.args.get("severity")
    patient_id = request.args.get("patient_id", type=int)

    query = Alert.query
    if status_filter != "all":
        query = query.filter_by(status=status_filter)
    if severity_filter:
        query = query.filter_by(severity=severity_filter.upper())
    if patient_id:
        query = query.filter_by(patient_id=patient_id)

    alerts = query.order_by(Alert.created_at.desc()).all()
    results = []
    for a in alerts:
        a_dict = a.to_dict()
        a_dict["patient_code"] = a.patient.patient_code if a.patient else None
        a_dict["patient_name"] = (
            f"{a.patient.first_name} {a.patient.last_name or ''}".strip()
            if a.patient else None
        )
        results.append(a_dict)

    active_count = sum(1 for a in results if a["status"] == "active")
    return jsonify({
        "success": True,
        "count": len(results),
        "active_count": active_count,
        "data": results,
    }), 200


@alerts_bp.route("", methods=["POST"])
def create_alert():
    """Create a new demonstration alarm."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body must be JSON"}), 400

    patient_id = data.get("patient_id")
    alert_type = data.get("alert_type")
    severity = data.get("severity", "MEDIUM").upper()
    description = data.get("description")

    if not patient_id or not alert_type or not description:
        return jsonify({
            "success": False,
            "error": "patient_id, alert_type, and description are required",
        }), 400

    if severity not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
        return jsonify({"success": False, "error": "severity must be LOW/MEDIUM/HIGH/CRITICAL"}), 400

    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({"success": False, "error": "Patient not found"}), 404

    alert = Alert(
        patient_id=patient_id,
        alert_type=alert_type,
        severity=severity,
        description=description,
        status="active",
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(alert)
    db.session.commit()

    uid = _current_user_id()
    log_action(uid, "ALERT_CREATED", "alert", alert.id, {
        "alert_type": alert_type, "severity": severity, "patient_id": patient_id,
    })

    return jsonify({
        "success": True,
        "message": "Alert raised successfully",
        "data": alert.to_dict(),
    }), 201


@alerts_bp.route("/<int:alert_id>/acknowledge", methods=["POST"])
def acknowledge_alert(alert_id):
    """Acknowledge an active alert. Records actor from JWT or body."""
    alert = db.session.get(Alert, alert_id)
    if not alert:
        return jsonify({"success": False, "error": "Alert not found"}), 404
    if alert.status == "resolved":
        return jsonify({"success": False, "error": "Cannot acknowledge a resolved alert"}), 409

    data = request.get_json() or {}
    uid = _current_user_id() or data.get("user_id", 1)
    remarks = data.get("remarks", "Acknowledged by clinical staff")
    notes = data.get("staff_notes")

    alert.status = "acknowledged"
    if notes:
        alert.staff_notes = notes

    ack = AlertAcknowledgement(
        alert_id=alert.id,
        user_id=uid,
        remarks=remarks,
        acknowledged_at=datetime.now(timezone.utc),
    )
    db.session.add(ack)
    db.session.commit()

    log_action(uid, "ALERT_ACKNOWLEDGED", "alert", alert.id, {
        "remarks": remarks, "patient_id": alert.patient_id,
    })

    return jsonify({
        "success": True,
        "message": f"Alert {alert.id} acknowledged",
        "data": alert.to_dict(),
    }), 200


@alerts_bp.route("/<int:alert_id>/resolve", methods=["POST"])
def resolve_alert(alert_id):
    """Resolve an alert after patient stabilization."""
    alert = db.session.get(Alert, alert_id)
    if not alert:
        return jsonify({"success": False, "error": "Alert not found"}), 404

    data = request.get_json(silent=True) or {}
    uid = _current_user_id() or data.get("user_id", 1)

    alert.status = "resolved"
    db.session.commit()

    log_action(uid, "ALERT_RESOLVED", "alert", alert.id, {"patient_id": alert.patient_id})

    res_data = alert.to_dict()
    res_data["resolved_by_user_id"] = uid
    return jsonify({
        "success": True,
        "message": f"Alert {alert.id} resolved",
        "data": res_data,
    }), 200


@alerts_bp.route("/<int:alert_id>/snooze", methods=["POST"])
def snooze_alert(alert_id):
    """
    Day 44: Snooze an active alert for a recorded duration.
    Body: { "duration_minutes": 15 }
    """
    alert = db.session.get(Alert, alert_id)
    if not alert:
        return jsonify({"success": False, "error": "Alert not found"}), 404
    if alert.status == "resolved":
        return jsonify({"success": False, "error": "Cannot snooze a resolved alert"}), 409

    data = request.get_json(silent=True) or {}
    duration_min = int(data.get("duration_minutes", 15))
    if duration_min < 1 or duration_min > 1440:
        return jsonify({"success": False, "error": "duration_minutes must be 1–1440"}), 400

    uid = _current_user_id() or data.get("user_id", 1)
    snooze_until = datetime.now(timezone.utc) + timedelta(minutes=duration_min)

    # Record snooze in acknowledgements table and audit
    ack = AlertAcknowledgement(
        alert_id=alert.id,
        user_id=uid,
        remarks=f"[SNOOZED] Alert snoozed for {duration_min} min until {snooze_until.isoformat()}",
        acknowledged_at=datetime.now(timezone.utc),
    )
    db.session.add(ack)
    db.session.commit()

    log_action(uid, "ALERT_SNOOZED", "alert", alert.id, {
        "duration_minutes": duration_min,
        "snoozed_until": snooze_until.isoformat(),
        "patient_id": alert.patient_id,
    })

    res_data = alert.to_dict()
    res_data["snoozed_until"] = snooze_until.isoformat()
    return jsonify({
        "success": True,
        "message": f"Alert {alert.id} snoozed for {duration_min} min",
        "data": res_data,
    }), 200


@alerts_bp.route("/<int:alert_id>/escalate", methods=["POST"])
def escalate_alert(alert_id):
    """
    Day 44: Escalate an alert to another staff member.
    Body: { "escalate_to_user_id": 2, "notes": "Requires senior review" }
    """
    alert = db.session.get(Alert, alert_id)
    if not alert:
        return jsonify({"success": False, "error": "Alert not found"}), 404
    if alert.status == "resolved":
        return jsonify({"success": False, "error": "Cannot escalate a resolved alert"}), 409

    data = request.get_json(silent=True) or {}
    escalate_to = data.get("escalate_to_user_id")
    if not escalate_to:
        return jsonify({"success": False, "error": "escalate_to_user_id required"}), 400

    uid = _current_user_id() or data.get("user_id", 1)
    notes = data.get("notes", "")

    # Record escalation in acknowledgements table and audit
    ack = AlertAcknowledgement(
        alert_id=alert.id,
        user_id=uid,
        remarks=f"[ESCALATED to user {escalate_to}] {notes}",
        acknowledged_at=datetime.now(timezone.utc),
    )
    db.session.add(ack)
    db.session.commit()

    log_action(uid, "ALERT_ESCALATED", "alert", alert.id, {
        "escalated_to_user_id": escalate_to,
        "notes": notes,
        "patient_id": alert.patient_id,
    })

    res_data = alert.to_dict()
    res_data["escalated_to_user_id"] = int(escalate_to)
    res_data["staff_notes"] = notes
    return jsonify({
        "success": True,
        "message": f"Alert {alert.id} escalated to user {escalate_to}",
        "data": res_data,
    }), 200
