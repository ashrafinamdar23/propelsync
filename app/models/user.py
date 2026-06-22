from sqlalchemy import Boolean, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "email IS NOT NULL OR mobile_number IS NOT NULL",
            name="ck_users_email_or_mobile_required",
        ),
        CheckConstraint(
            "status IN ('active', 'invited', 'suspended')",
            name="ck_users_status",
        ),
    )

    keycloak_subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )
    mobile_number: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    is_platform_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
