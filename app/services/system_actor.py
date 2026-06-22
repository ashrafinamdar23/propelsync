from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User


def ensure_scheduled_jobs_system_actor(session: Session) -> User:
    user = session.scalar(
        select(User).where(User.keycloak_subject == settings.scheduled_jobs_system_actor_subject)
    )
    if user is None:
        user = session.scalar(
            select(User).where(User.email == settings.scheduled_jobs_system_actor_email)
        )

    if user is None:
        user = User(
            keycloak_subject=settings.scheduled_jobs_system_actor_subject,
            email=settings.scheduled_jobs_system_actor_email,
            mobile_number=None,
            full_name=settings.scheduled_jobs_system_actor_full_name,
            status="active",
            is_platform_superuser=True,
        )
        session.add(user)
    else:
        user.keycloak_subject = settings.scheduled_jobs_system_actor_subject
        user.email = settings.scheduled_jobs_system_actor_email
        user.full_name = settings.scheduled_jobs_system_actor_full_name
        user.status = "active"
        user.is_platform_superuser = True

    session.commit()
    session.refresh(user)
    return user
