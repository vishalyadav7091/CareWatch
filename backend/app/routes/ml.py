"""
Phase 6 (Day 40): Real-time inference API.
RESEARCH / DEMONSTRATION ONLY. Output is not a clinically validated probability.
"""
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from app.services.feature_extractor import extract_features, FEATURE_SCHEMA, N_FEATURES
from app.services.model_service import load_model, get_metadata, train_and_save
from app.models import Patient, VitalObservation
from app import db
import numpy as np

ml_bp = Blueprint("ml", __name__, url_prefix="/api/v1/ml")

_DISCLAIMER = (
    "RESEARCH/DEMONSTRATION ONLY. Output is an experimental score from a model "
    "trained on synthetic data. Not clinically validated. "
    "Do not use for clinical decisions."
)


@ml_bp.route("/train", methods=["POST"])
def trigger_training():
    """Train and save the model. Can take 5-15 seconds."""
    try:
        eval_results = train_and_save()
        return jsonify({"success": True, "evaluation": eval_results}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ml_bp.route("/status", methods=["GET"])
def model_status():
    """Check whether a trained model exists and return metadata."""
    meta = get_metadata()
    if not meta:
        return jsonify({
            "success": True,
            "model_ready": False,
            "message": "No trained model found. POST /api/v1/ml/train to train.",
        }), 200
    return jsonify({
        "success": True,
        "model_ready": True,
        "version": meta.get("version"),
        "model": meta.get("model"),
        "auroc": meta.get("auroc"),
        "f1": meta.get("f1"),
        "trained_at": meta.get("trained_at"),
        "disclaimer": _DISCLAIMER,
    }), 200


@ml_bp.route("/infer/<int:patient_id>", methods=["GET"])
def infer_patient_risk(patient_id):
    """
    Day 40: Run inference on the latest vitals window for a patient.
    Returns experimental risk score (0-100). NOT clinically validated.
    """
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({"success": False, "error": "Patient not found"}), 404

    model = load_model()
    if model is None:
        return jsonify({
            "success": False,
            "error": "No trained model available. POST /api/v1/ml/train first.",
            "model_ready": False,
        }), 503

    window_size = request.args.get("window", 10, type=int)
    vitals = (
        VitalObservation.query
        .filter_by(patient_id=patient_id)
        .order_by(VitalObservation.measured_at.asc())
        .limit(window_size)
        .all()
    )

    if len(vitals) < 3:
        return jsonify({
            "success": False,
            "error": f"Insufficient vitals data: {len(vitals)} reading(s). Minimum 3 required.",
        }), 422

    window_dicts = [v.to_dict() for v in vitals]
    features = extract_features(window_dicts)

    # Validate no all-NaN input
    if np.all(np.isnan(features)):
        return jsonify({"success": False, "error": "All feature values are missing."}), 422

    features_2d = features.reshape(1, -1)
    try:
        prob = float(model.predict_proba(features_2d)[0][1])
    except Exception as e:
        return jsonify({"success": False, "error": f"Inference error: {e}"}), 500

    risk_score = round(prob * 100, 1)
    if risk_score >= 70:
        risk_category = "HIGH"
    elif risk_score >= 40:
        risk_category = "MEDIUM"
    else:
        risk_category = "LOW"

    meta = get_metadata() or {}

    # Persist to risk_assessments table (non-blocking)
    try:
        from app.models import RiskAssessment
        from datetime import datetime, timezone
        ra = RiskAssessment(
            patient_id=patient_id,
            model_name=meta.get("model", "Unknown"),
            model_version=meta.get("version", "demo"),
            risk_score=prob,
            risk_category=risk_category,
            assessment_status="demonstration",
            assessed_at=datetime.now(timezone.utc),
        )
        db.session.add(ra)
        db.session.commit()
    except Exception:
        pass  # non-critical

    return jsonify({
        "success": True,
        "patient_id": patient_id,
        "experimental_risk_score": risk_score,
        "risk_category": risk_category,
        "vitals_window_size": len(vitals),
        "model_version": meta.get("version", "unknown"),
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": _DISCLAIMER,
    }), 200


@ml_bp.route("/history/<int:patient_id>", methods=["GET"])
def risk_history(patient_id):
    """Return historical AI risk assessments for a patient."""
    from app.models import RiskAssessment
    assessments = (
        RiskAssessment.query
        .filter_by(patient_id=patient_id)
        .order_by(RiskAssessment.assessed_at.desc())
        .limit(50)
        .all()
    )
    return jsonify({
        "success": True,
        "patient_id": patient_id,
        "count": len(assessments),
        "data": [a.to_dict() for a in assessments],
        "disclaimer": _DISCLAIMER,
    }), 200
