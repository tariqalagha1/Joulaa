import uuid
from typing import Any

import structlog

from .database import SessionLocal, engine
from ..models.audit_event import AuditEvent

logger = structlog.get_logger()
_table_checked = False


def _to_uuid(value: Any) -> uuid.UUID | None:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


def _ensure_audit_table() -> None:
    global _table_checked
    if _table_checked:
        return
    AuditEvent.__table__.create(bind=engine, checkfirst=True)
    _table_checked = True


def log_audit_event(
    event_type,
    user_id,
    organization_id,
    resource_type,
    resource_id,
    metadata=None,
):
    try:
        _ensure_audit_table()
        db = SessionLocal()
        try:
            event = AuditEvent(
                user_id=_to_uuid(user_id),
                organization_id=_to_uuid(organization_id),
                event_type=str(event_type),
                resource_type=str(resource_type),
                resource_id=str(resource_id),
                metadata_=metadata or {},
            )
            db.add(event)
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        logger.warning(
            "Audit event logging failed",
            event_type=str(event_type),
            resource_type=str(resource_type),
            resource_id=str(resource_id),
            error=str(exc),
        )
