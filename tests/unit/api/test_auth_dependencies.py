import uuid
from collections.abc import Generator

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user, get_token_claims, require_platform_superuser
from app.db.deps import get_db
from app.models import User


def build_test_client(user: User, claims: dict[str, object] | None) -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with TestingSessionLocal() as session:
        session.add(user)
        session.commit()

    def override_get_db() -> Generator[Session]:
        with TestingSessionLocal() as session:
            yield session

    app = FastAPI()

    @app.get("/me")
    def me(current_user: User = Depends(get_current_user)) -> dict[str, str]:
        return {"id": str(current_user.id)}

    @app.get("/platform")
    def platform(current_user: User = Depends(require_platform_superuser)) -> dict[str, str]:
        return {"id": str(current_user.id)}

    app.dependency_overrides[get_db] = override_get_db
    if claims is not None:

        def override_get_token_claims() -> dict[str, object]:
            return claims

        app.dependency_overrides[get_token_claims] = override_get_token_claims
    return TestClient(app)


def test_get_current_user_resolves_active_local_user() -> None:
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        keycloak_subject="subject-1",
        email="admin@propelsync.local",
        full_name="Platform Admin",
        status="active",
        is_platform_superuser=True,
    )
    client = build_test_client(user, {"sub": "subject-1"})

    response = client.get("/me", headers={"Authorization": "Bearer token"})

    assert response.status_code == 200
    assert response.json() == {"id": str(user_id)}


def test_get_current_user_rejects_missing_token() -> None:
    user = User(
        keycloak_subject="subject-1",
        email="admin@propelsync.local",
        full_name="Platform Admin",
        status="active",
    )
    client = build_test_client(user, None)

    response = client.get("/me")

    assert response.status_code == 401


def test_require_platform_superuser_rejects_normal_user() -> None:
    user = User(
        keycloak_subject="subject-1",
        email="user@propelsync.local",
        full_name="Normal User",
        status="active",
        is_platform_superuser=False,
    )
    client = build_test_client(user, {"sub": "subject-1"})

    response = client.get("/platform", headers={"Authorization": "Bearer token"})

    assert response.status_code == 403
