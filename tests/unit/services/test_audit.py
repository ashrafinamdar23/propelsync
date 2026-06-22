import uuid

from app.services.audit import record_audit_log


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, instance: object) -> None:
        self.added.append(instance)


def test_record_audit_log_adds_log_to_session() -> None:
    session = FakeSession()
    tenant_id = uuid.uuid4()
    actor_user_id = uuid.uuid4()
    entity_id = uuid.uuid4()

    audit_log = record_audit_log(
        session,  # type: ignore[arg-type]
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action="tenant.created",
        entity_type="Tenant",
        entity_id=entity_id,
        summary="Tenant created.",
        metadata={"slug": "green-heights"},
    )

    assert session.added == [audit_log]
    assert audit_log.tenant_id == tenant_id
    assert audit_log.actor_user_id == actor_user_id
    assert audit_log.action == "tenant.created"
    assert audit_log.entity_type == "Tenant"
    assert audit_log.entity_id == entity_id
    assert audit_log.summary == "Tenant created."
    assert audit_log.metadata_ == {"slug": "green-heights"}


def test_record_audit_log_supports_platform_level_events() -> None:
    session = FakeSession()

    audit_log = record_audit_log(
        session,  # type: ignore[arg-type]
        action="tenant.created",
        entity_type="Tenant",
    )

    assert audit_log.tenant_id is None
    assert audit_log.actor_user_id is None
    assert audit_log.metadata_ == {}
