import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class TenantMembership(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "tenant_memberships"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "user_id",
            "role",
            name="uq_tenant_memberships_tenant_user_role",
        ),
        CheckConstraint(
            "role IN ('tenant_admin')",
            name="ck_tenant_memberships_role",
        ),
        CheckConstraint(
            "status IN ('active', 'invited', 'suspended')",
            name="ck_tenant_memberships_status",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")


class SocietyMembership(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "society_memberships"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "society_id",
            "user_id",
            "role",
            name="uq_society_memberships_scope_user_role",
        ),
        CheckConstraint(
            (
                "role IN ("
                "'society_admin', "
                "'treasurer', "
                "'accountant', "
                "'auditor', "
                "'committee_member', "
                "'flat_owner', "
                "'read_only_resident'"
                ")"
            ),
            name="ck_society_memberships_role",
        ),
        CheckConstraint(
            "status IN ('active', 'invited', 'suspended')",
            name="ck_society_memberships_status",
        ),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("societies.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
