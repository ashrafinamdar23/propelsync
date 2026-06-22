from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import TokenVerificationError, credentials_exception, verify_keycloak_token
from app.db.deps import get_db
from app.models import User


bearer_scheme = HTTPBearer(auto_error=False)


def get_token_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise credentials_exception()

    try:
        return verify_keycloak_token(credentials.credentials)
    except TokenVerificationError as exc:
        raise credentials_exception() from exc


def get_current_user(
    claims: Annotated[dict[str, Any], Depends(get_token_claims)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    keycloak_subject = claims.get("sub")
    if not keycloak_subject:
        raise credentials_exception()

    user = db.scalar(select(User).where(User.keycloak_subject == keycloak_subject))
    if user is None or user.status != "active":
        raise credentials_exception()

    return user


def require_platform_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_platform_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform superuser access is required.",
        )
    return current_user
