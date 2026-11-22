"""
Phase 7 (Day 45): Audit logging service.
All audit records are write-once and append-only via this service.
"""
from datetime import datetime, timezone


def log_action(user_id, action, entity_type, entity_id, details=None):
    """
    Append a read-only audit record.
    Silently ignores DB errors to avoid blocking primary operations.
    """
    try:
        from app import db
        from app.models import AuditLog
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as exc:
        print(f"[AuditLog] Failed to write audit record: {exc}")
