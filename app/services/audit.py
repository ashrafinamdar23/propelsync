import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog


def record_audit_log(
    session: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
    summary: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata_=metadata or {},
    )
    session.add(audit_log)
    return audit_log
