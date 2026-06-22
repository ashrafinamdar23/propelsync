import uuid
from types import SimpleNamespace

from app.worker.tasks import ping, run_due_jobs_for_all_societies, scan_due_work


class FakeScalarResult:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows

    def __iter__(self):
        return iter(self.rows)


class FakeSession:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows
        self.closed = False

    def scalars(self, *_: object) -> FakeScalarResult:
        return FakeScalarResult(self.rows)

    def close(self) -> None:
        self.closed = True


def test_ping_returns_ok() -> None:
    assert ping.run() == {"status": "ok"}


def test_scan_due_work_returns_due_societies(monkeypatch) -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    society = SimpleNamespace(
        id=society_id,
        tenant_id=tenant_id,
        name="Dream Savera",
        status="active",
    )
    session = FakeSession([society])

    def fake_session_local() -> FakeSession:
        return session

    def fake_get_due_work(*_: object, **__: object) -> SimpleNamespace:
        return SimpleNamespace(billing_due_count=2, late_fee_due_count=1)

    monkeypatch.setattr("app.worker.tasks.SessionLocal", fake_session_local)
    monkeypatch.setattr("app.worker.tasks.get_due_work", fake_get_due_work)

    result = scan_due_work.run("2026-06-22")

    assert result["as_of_date"] == "2026-06-22"
    assert result["society_count"] == 1
    assert result["due_society_count"] == 1
    assert result["due_societies"] == [
        {
            "tenant_id": str(tenant_id),
            "society_id": str(society_id),
            "society_name": "Dream Savera",
            "billing_due_count": 2,
            "late_fee_due_count": 1,
        }
    ]
    assert session.closed is True


def test_run_due_jobs_for_all_societies_uses_system_actor_and_scheduled_mode(monkeypatch) -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    society = SimpleNamespace(
        id=society_id,
        tenant_id=tenant_id,
        name="Dream Savera",
        status="active",
    )
    system_actor = SimpleNamespace(id=uuid.uuid4())
    session = FakeSession([society])
    calls = []

    def fake_session_local() -> FakeSession:
        return session

    def fake_ensure_system_actor(_: object) -> SimpleNamespace:
        return system_actor

    def fake_get_due_work(*_: object, **__: object) -> SimpleNamespace:
        return SimpleNamespace(billing_due_count=1, late_fee_due_count=0)

    def fake_run_due_jobs(*_: object, **kwargs: object) -> SimpleNamespace:
        calls.append(kwargs)
        return SimpleNamespace(
            billing_rule_count=1,
            late_fee_rule_count=0,
            generated_invoice_count=3,
            generated_penalty_invoice_count=0,
        )

    monkeypatch.setattr("app.worker.tasks.SessionLocal", fake_session_local)
    monkeypatch.setattr("app.worker.tasks.ensure_scheduled_jobs_system_actor", fake_ensure_system_actor)
    monkeypatch.setattr("app.worker.tasks.get_due_work", fake_get_due_work)
    monkeypatch.setattr("app.worker.tasks.run_due_jobs", fake_run_due_jobs)

    result = run_due_jobs_for_all_societies.run("2026-06-22")

    assert result["processed_society_count"] == 1
    assert result["failed_society_count"] == 0
    assert result["results"][0]["generated_invoice_count"] == 3
    assert calls[0]["actor"] is system_actor
    assert calls[0]["run_mode"] == "scheduled"
    assert session.closed is True
