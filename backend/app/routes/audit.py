"""
Phase 7 (Day 45): Read-only audit log endpoints.
Only admin and doctor roles may read audit logs.
Ordinary users cannot modify, delete, or create audit records via API.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import AuditLog, User, Hospital, Doctor, Nurse
from app import db

audit_bp = Blueprint("audit", __name__, url_prefix="/api/v1/audit")

_ALLOWED_ROLES = {"admin", "doctor"}


def _require_audit_role():
    """Return current user or None if unauthorized."""
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity))
    if not user or user.role not in _ALLOWED_ROLES:
        return None, jsonify({"success": False, "error": "Forbidden: insufficient role"}), 403
    return user, None, None


@audit_bp.route("", methods=["GET"])
@jwt_required()
def list_audit_logs():
    """Paginated audit log — admin/doctor only."""
    user, err_resp, code = _require_audit_role()
    if err_resp:
        return err_resp, code

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)
    action_filter = request.args.get("action")
    entity_filter = request.args.get("entity_type")

    query = AuditLog.query
    if action_filter:
        query = query.filter(AuditLog.action == action_filter.upper())
    if entity_filter:
        query = query.filter(AuditLog.entity_type == entity_filter.lower())

    paginated = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "success": True,
        "total": paginated.total,
        "page": paginated.page,
        "pages": paginated.pages,
        "data": [a.to_dict() for a in paginated.items],
    }), 200


@audit_bp.route("/patient/<int:patient_id>", methods=["GET"])
@jwt_required()
def patient_audit_trail(patient_id):
    """Patient-specific audit trail — admin/doctor only."""
    user, err_resp, code = _require_audit_role()
    if err_resp:
        return err_resp, code

    limit = min(request.args.get("limit", 100, type=int), 500)
    logs = (
        AuditLog.query
        .filter_by(entity_type="patient", entity_id=patient_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    # Also include alert actions for this patient
    alert_logs = (
        AuditLog.query
        .filter_by(entity_type="alert")
        .filter(AuditLog.details["patient_id"].as_integer() == patient_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    combined = sorted(
        logs + alert_logs,
        key=lambda x: x.created_at or "",
        reverse=True,
    )[:limit]

    return jsonify({
        "success": True,
        "patient_id": patient_id,
        "count": len(combined),
        "data": [a.to_dict() for a in combined],
    }), 200


@audit_bp.route("/staff", methods=["GET"])
@jwt_required()
def list_staff_members():
    """List all hospital doctors and nurses — admin/doctor only."""
    user, err_resp, code = _require_audit_role()
    if err_resp:
        return err_resp, code

    doctors = Doctor.query.all()
    nurses = Nurse.query.all()

    doc_list = []
    for d in doctors:
        u = db.session.get(User, d.user_id) if d.user_id else None
        h = db.session.get(Hospital, d.hospital_id) if d.hospital_id else None
        doc_list.append({
            "id": d.id,
            "user_id": d.user_id,
            "name": u.full_name if u else f"Doctor #{d.id}",
            "email": u.email if u else "N/A",
            "role": "doctor",
            "specialization": d.specialization or "Critical Care / Intensivist",
            "hospital": h.name if h else "City General Hospital",
            "is_active": u.is_active if u else True,
            "created_at": u.created_at.strftime("%Y-%m-%d") if u and u.created_at else "2026-01-01",
        })

    nurse_list = []
    for n in nurses:
        u = db.session.get(User, n.user_id) if n.user_id else None
        h = db.session.get(Hospital, n.hospital_id) if n.hospital_id else None
        nurse_list.append({
            "id": n.id,
            "user_id": n.user_id,
            "name": u.full_name if u else f"Nurse #{n.id}",
            "email": u.email if u else "N/A",
            "role": "nurse",
            "department": n.department or "ICU Critical Care Nursing",
            "hospital": h.name if h else "City General Hospital",
            "is_active": u.is_active if u else True,
            "created_at": u.created_at.strftime("%Y-%m-%d") if u and u.created_at else "2026-01-01",
        })

    # Include any users with role doctor or nurse not yet linked to doctor/nurse rows
    doc_user_ids = {d["user_id"] for d in doc_list}
    nurse_user_ids = {n["user_id"] for n in nurse_list}
    all_users = User.query.all()
    for u in all_users:
        if u.role == "doctor" and u.id not in doc_user_ids:
            doc_list.append({
                "id": u.id,
                "user_id": u.id,
                "name": u.full_name,
                "email": u.email,
                "role": "doctor",
                "specialization": "Critical Care Medicine",
                "hospital": "City General Hospital",
                "is_active": u.is_active,
                "created_at": u.created_at.strftime("%Y-%m-%d") if u.created_at else "2026-01-01",
            })
        elif u.role == "nurse" and u.id not in nurse_user_ids:
            nurse_list.append({
                "id": u.id,
                "user_id": u.id,
                "name": u.full_name,
                "email": u.email,
                "role": "nurse",
                "department": "ICU Ward A",
                "hospital": "City General Hospital",
                "is_active": u.is_active,
                "created_at": u.created_at.strftime("%Y-%m-%d") if u.created_at else "2026-01-01",
            })

    return jsonify({
        "success": True,
        "doctors": doc_list,
        "nurses": nurse_list,
        "summary": {
            "total_staff": len(doc_list) + len(nurse_list),
            "doctors_count": len(doc_list),
            "nurses_count": len(nurse_list),
        },
    }), 200
