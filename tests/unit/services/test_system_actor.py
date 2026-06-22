from app.core.config import settings
from app.models import User
from app.services.system_actor import ensure_scheduled_jobs_system_actor


class FakeSession:
    def __init__(self, scalar_results: list[object | None] | None = None) -> None:
        self.scalar_results = scalar_results or []
        self.added: list[object] = []
        self.committed = False
        self.refreshed: object | None = None

    def scalar(self, *_: object) -> object | None:
        return self.scalar_results.pop(0) if self.scalar_results else None

    def add(self, instance: object) -> None:
        self.added.append(instance)

    def commit(self) -> None:
        self.committed = True

    def refresh(self, instance: object) -> None:
        self.refreshed = instance


def test_ensure_scheduled_jobs_system_actor_creates_user() -> None:
    session = FakeSession()

    user = ensure_scheduled_jobs_system_actor(session)  # type: ignore[arg-type]

    assert user.keycloak_subject == settings.scheduled_jobs_system_actor_subject
    assert user.email == settings.scheduled_jobs_system_actor_email
    assert user.full_name == settings.scheduled_jobs_system_actor_full_name
    assert user.status == "active"
    assert user.is_platform_superuser is True
    assert session.added == [user]
    assert session.committed is True
    assert session.refreshed is user


def test_ensure_scheduled_jobs_system_actor_reuses_existing_user() -> None:
    existing = User(
        keycloak_subject="old-subject",
        email=settings.scheduled_jobs_system_actor_email,
        full_name="Old Name",
        status="suspended",
        is_platform_superuser=False,
    )
    session = FakeSession(scalar_results=[None, existing])

    user = ensure_scheduled_jobs_system_actor(session)  # type: ignore[arg-type]

    assert user is existing
    assert user.keycloak_subject == settings.scheduled_jobs_system_actor_subject
    assert user.status == "active"
    assert user.is_platform_superuser is True
    assert session.added == []
