"""
Phase 7 (Day 42): Demonstration Alert Engine.
All thresholds are DEMONSTRATION SETTINGS ONLY. Not clinical protocols.
"""
from datetime import datetime, timezone

# ------------------------------------------------------------------
# DEMONSTRATION thresholds — explicitly NOT clinical protocols.
# All values are configurable demonstration defaults.
# ------------------------------------------------------------------
DEMO_THRESHOLDS = {
    "heart_rate": {
        "CRITICAL_HIGH": 150,
        "WARNING_HIGH":  120,
        "WARNING_LOW":   50,
        "CRITICAL_LOW":  40,
    },
    "spo2": {
        "CRITICAL_LOW":  88,
        "WARNING_LOW":   92,
    },
    "systolic_bp": {
        "CRITICAL_HIGH": 190,
        "WARNING_HIGH":  160,
        "WARNING_LOW":   90,
        "CRITICAL_LOW":  70,
    },
    "respiratory_rate": {
        "CRITICAL_HIGH": 35,
        "WARNING_HIGH":  25,
        "WARNING_LOW":   8,
    },
    "temperature": {
        "CRITICAL_HIGH": 40.5,
        "WARNING_HIGH":  39.0,
        "WARNING_LOW":   35.5,
        "CRITICAL_LOW":  34.0,
    },
    "ai_risk": {
        "CRITICAL": 80,
        "WARNING":  60,
    },
}

DISCLAIMER = (
    "DEMONSTRATION ALERT — Thresholds are configurable demo settings, "
    "not validated clinical protocols. Not for clinical use."
)


def _check_vital(name, value, thresholds):
    """Return (severity, description) or None if no threshold crossed."""
    if value is None:
        return None
    value = float(value)
    t = thresholds

    if name == "spo2":
        if value <= t.get("CRITICAL_LOW", 0):
            return "CRITICAL", f"[DEMO] SpO2 critically low: {value}% ≤ {t['CRITICAL_LOW']}%"
        if value <= t.get("WARNING_LOW", 0):
            return "WARNING", f"[DEMO] SpO2 low: {value}% ≤ {t['WARNING_LOW']}%"
        return None

    if name == "respiratory_rate":
        if value >= t.get("CRITICAL_HIGH", 9999):
            return "CRITICAL", f"[DEMO] RR critically high: {value} ≥ {t['CRITICAL_HIGH']}/min"
        if value >= t.get("WARNING_HIGH", 9999):
            return "WARNING", f"[DEMO] RR elevated: {value} ≥ {t['WARNING_HIGH']}/min"
        if value <= t.get("WARNING_LOW", 0):
            return "WARNING", f"[DEMO] RR low: {value} ≤ {t['WARNING_LOW']}/min"
        return None

    # Generic high/low check
    if "CRITICAL_HIGH" in t and value >= t["CRITICAL_HIGH"]:
        return "CRITICAL", f"[DEMO] {name} critically high: {value} ≥ {t['CRITICAL_HIGH']}"
    if "WARNING_HIGH" in t and value >= t["WARNING_HIGH"]:
        return "WARNING", f"[DEMO] {name} high: {value} ≥ {t['WARNING_HIGH']}"
    if "CRITICAL_LOW" in t and value <= t["CRITICAL_LOW"]:
        return "CRITICAL", f"[DEMO] {name} critically low: {value} ≤ {t['CRITICAL_LOW']}"
    if "WARNING_LOW" in t and value <= t["WARNING_LOW"]:
        return "WARNING", f"[DEMO] {name} low: {value} ≤ {t['WARNING_LOW']}"
    return None


def evaluate_patient_alerts(patient_id, vital_dict, risk_score=None, app=None):
    """
    Evaluate one vital reading against DEMO thresholds.
    Creates Alert records if thresholds are crossed and no active alert of
    the same type already exists (deduplication).

    Parameters
    ----------
    patient_id : int
    vital_dict : dict  (keys: heart_rate, spo2, systolic_bp, etc.)
    risk_score : float or None  (0–100 experimental score)
    app        : Flask app instance (required when called from a thread)
    """
    from app import db
    from app.models import Alert
    from app.services.audit_service import log_action

    checks = [
        ("heart_rate",        vital_dict.get("heart_rate"),        DEMO_THRESHOLDS["heart_rate"],        "HR_ALERT"),
        ("spo2",              vital_dict.get("spo2"),               DEMO_THRESHOLDS["spo2"],              "SPO2_ALERT"),
        ("systolic_bp",       vital_dict.get("systolic_bp"),        DEMO_THRESHOLDS["systolic_bp"],       "BP_ALERT"),
        ("respiratory_rate",  vital_dict.get("respiratory_rate"),   DEMO_THRESHOLDS["respiratory_rate"],  "RR_ALERT"),
        ("temperature",       vital_dict.get("temperature"),        DEMO_THRESHOLDS["temperature"],       "TEMP_ALERT"),
    ]

    new_alerts = []

    for vital_name, value, thresholds, alert_type in checks:
        result = _check_vital(vital_name, value, thresholds)
        if not result:
            continue
        severity, description = result

        # Deduplication: skip if same type + active alert already exists
        existing = (
            Alert.query
            .filter_by(patient_id=patient_id, alert_type=alert_type, status="active")
            .first()
        )
        if existing:
            continue

        alert = Alert(
            patient_id=patient_id,
            alert_type=alert_type,
            severity=severity,
            description=description + " " + DISCLAIMER,
            status="active",
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(alert)
        new_alerts.append(alert)

    # AI risk alert
    if risk_score is not None:
        ai_t = DEMO_THRESHOLDS["ai_risk"]
        ai_severity = None
        if risk_score >= ai_t["CRITICAL"]:
            ai_severity = "CRITICAL"
        elif risk_score >= ai_t["WARNING"]:
            ai_severity = "WARNING"

        if ai_severity:
            existing = (
                Alert.query
                .filter_by(patient_id=patient_id, alert_type="AI_RISK_HIGH", status="active")
                .first()
            )
            if not existing:
                alert = Alert(
                    patient_id=patient_id,
                    alert_type="AI_RISK_HIGH",
                    severity=ai_severity,
                    description=(
                        f"[DEMO] Experimental AI risk score: {risk_score:.1f}/100. "
                        f"Research prototype output – not clinically validated. {DISCLAIMER}"
                    ),
                    status="active",
                    created_at=datetime.now(timezone.utc),
                )
                db.session.add(alert)
                new_alerts.append(alert)

    if new_alerts:
        db.session.commit()
        # Audit log
        for a in new_alerts:
            log_action(
                user_id=None,
                action="ALERT_CREATED",
                entity_type="alert",
                entity_id=a.id,
                details={
                    "alert_type": a.alert_type,
                    "severity": a.severity,
                    "patient_id": patient_id,
                    "note": "auto-generated by demo alert engine",
                },
            )
        # Real-time push to ward room
        try:
            from app import socketio
            for a in new_alerts:
                socketio.emit("alert_created", a.to_dict(), room="ward_a")
        except Exception:
            pass  # non-critical

    return new_alerts
