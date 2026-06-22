import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Society, SocietyMembership, TenantMembership, User
from app.schemas.user_management import (
    ManagedUserCreate,
    ManagedUserMembershipRead,
    ManagedUserRead,
    ManagedUserSocietyMembershipRead,
)
from app.scripts.bootstrap_identity import KeycloakAdminClient, get_bootstrap_username
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


TENANT_ROLES = {"tenant_admin"}
SOCIETY_ROLES = {
    "society_admin",
    "treasurer",
    "accountant",
    "auditor",
    "committee_member",
    "flat_owner",
    "read_only_resident",
}


class UserManagementError(Exception):
    pass


class UserAlreadyExistsError(UserManagementError):
    pass


class UserProvisioningError(UserManagementError):
    pass


class UserRoleInvalidError(UserManagementError):
    pass


class UserManagementPermissionError(UserManagementError):
    pass


class ManagedUserNotFoundError(UserManagementError):
    pass


class SocietyAccessInvalidError(UserManagementError):
    pass


def provision_keycloak_user(payload: ManagedUserCreate) -> str:
    username = get_bootstrap_username(str(payload.email) if payload.email else None, payload.mobile_number)
    try:
        with KeycloakAdminClient(
            settings.keycloak_internal_url,
            settings.keycloak_admin_username,
            settings.keycloak_admin_password,
        ) as keycloak:
            keycloak.authenticate()
            keycloak_user_id, _ = keycloak.ensure_user(
                settings.keycloak_realm,
                username=username,
                email=str(payload.email) if payload.email else None,
                mobile_number=payload.mobile_number,
                full_name=payload.full_name,
                password=payload.temporary_password,
            )
            return keycloak_user_id
    except (httpx.HTTPError, KeyError) as exc:
        raise UserProvisioningError("Unable to provision user in Keycloak.") from exc


def validate_roles(payload: ManagedUserCreate) -> None:
    invalid_tenant_roles = sorted(set(payload.tenant_roles) - TENANT_ROLES)
    invalid_society_roles = sorted({assignment.role for assignment in payload.society_roles} - SOCIETY_ROLES)
    if invalid_tenant_roles or invalid_society_roles:
        raise UserRoleInvalidError(
            "Invalid role assignment: "
            f"tenant_roles={invalid_tenant_roles}, society_roles={invalid_society_roles}"
        )


def actor_is_tenant_admin(session: Session, *, tenant_context: TenantContext) -> bool:
    if tenant_context.user.is_platform_superuser:
        return True
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_context.tenant_id,
            TenantMembership.user_id == tenant_context.user.id,
            TenantMembership.role == "tenant_admin",
            TenantMembership.status == "active",
        )
    )
    return membership is not None


def actor_society_admin_ids(session: Session, *, tenant_context: TenantContext) -> set[uuid.UUID]:
    memberships = session.scalars(
        select(SocietyMembership).where(
            SocietyMembership.tenant_id == tenant_context.tenant_id,
            SocietyMembership.user_id == tenant_context.user.id,
            SocietyMembership.role == "society_admin",
            SocietyMembership.status == "active",
        )
    )
    return {membership.society_id for membership in memberships}


def get_user_management_scope(session: Session, *, tenant_context: TenantContext) -> set[uuid.UUID] | None:
    if actor_is_tenant_admin(session, tenant_context=tenant_context):
        return None
    society_ids = actor_society_admin_ids(session, tenant_context=tenant_context)
    if not society_ids:
        raise UserManagementPermissionError("User management access is required.")
    return society_ids


def ensure_actor_can_assign_roles(
    session: Session,
    *,
    tenant_context: TenantContext,
    payload: ManagedUserCreate,
) -> set[uuid.UUID] | None:
    scope = get_user_management_scope(session, tenant_context=tenant_context)
    if scope is None:
        return None

    requested_society_ids = {assignment.society_id for assignment in payload.society_roles}
    if payload.tenant_roles:
        raise UserManagementPermissionError("Society admins cannot assign tenant-level roles.")
    if not requested_society_ids:
        raise UserManagementPermissionError("Society admins must assign at least one society role.")
    if not requested_society_ids.issubset(scope):
        raise UserManagementPermissionError("Society admins can only assign roles in their societies.")
    return scope


def find_user_by_identity(
    session: Session,
    *,
    keycloak_subject: str,
    email: str | None,
    mobile_number: str | None,
) -> User | None:
    user = session.scalar(select(User).where(User.keycloak_subject == keycloak_subject))
    if user is None and email:
        user = session.scalar(select(User).where(User.email == email))
    if user is None and mobile_number:
        user = session.scalar(select(User).where(User.mobile_number == mobile_number))
    return user


def upsert_local_user(
    session: Session,
    *,
    keycloak_subject: str,
    payload: ManagedUserCreate,
) -> User:
    email = str(payload.email) if payload.email else None
    user = find_user_by_identity(
        session,
        keycloak_subject=keycloak_subject,
        email=email,
        mobile_number=payload.mobile_number,
    )
    if user is None:
        user = User(
            keycloak_subject=keycloak_subject,
            email=email,
            mobile_number=payload.mobile_number,
            full_name=payload.full_name,
            status="active",
            is_platform_superuser=False,
        )
        session.add(user)
    else:
        user.keycloak_subject = keycloak_subject
        user.email = email
        user.mobile_number = payload.mobile_number
        user.full_name = payload.full_name
        user.status = "active"
    session.flush()
    return user


def ensure_tenant_membership(
    session: Session,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    role: str,
) -> TenantMembership:
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == user_id,
            TenantMembership.role == role,
        )
    )
    if membership is None:
        membership = TenantMembership(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            status="active",
        )
        session.add(membership)
    else:
        membership.status = "active"
    return membership


def ensure_society_membership(
    session: Session,
    *,
    tenant_id: uuid.UUID,
    society_id: uuid.UUID,
    user_id: uuid.UUID,
    role: str,
) -> SocietyMembership:
    society = session.scalar(
        select(Society).where(
            Society.id == society_id,
            Society.tenant_id == tenant_id,
            Society.status == "active",
        )
    )
    if society is None:
        raise SocietyAccessInvalidError("Society must belong to the selected tenant and be active.")

    membership = session.scalar(
        select(SocietyMembership).where(
            SocietyMembership.tenant_id == tenant_id,
            SocietyMembership.society_id == society_id,
            SocietyMembership.user_id == user_id,
            SocietyMembership.role == role,
        )
    )
    if membership is None:
        membership = SocietyMembership(
            tenant_id=tenant_id,
            society_id=society_id,
            user_id=user_id,
            role=role,
            status="active",
        )
        session.add(membership)
    else:
        membership.status = "active"
    return membership


def user_to_read(
    user: User,
    *,
    tenant_memberships: list[TenantMembership],
    society_rows: list[tuple[SocietyMembership, Society]],
) -> ManagedUserRead:
    return ManagedUserRead(
        id=user.id,
        keycloak_subject=user.keycloak_subject,
        email=user.email,
        mobile_number=user.mobile_number,
        full_name=user.full_name,
        status=user.status,
        is_platform_superuser=user.is_platform_superuser,
        tenant_memberships=[
            ManagedUserMembershipRead(id=membership.id, role=membership.role, status=membership.status)
            for membership in tenant_memberships
        ],
        society_memberships=[
            ManagedUserSocietyMembershipRead(
                id=membership.id,
                society_id=membership.society_id,
                society_name=society.name,
                role=membership.role,
                status=membership.status,
            )
            for membership, society in society_rows
        ],
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def list_managed_users(session: Session, *, tenant_context: TenantContext) -> list[ManagedUserRead]:
    scope = get_user_management_scope(session, tenant_context=tenant_context)
    tenant_memberships = list(
        session.scalars(
            select(TenantMembership).where(TenantMembership.tenant_id == tenant_context.tenant_id)
        )
    ) if scope is None else []
    society_statement = (
        select(SocietyMembership, Society)
        .join(Society, Society.id == SocietyMembership.society_id)
        .where(SocietyMembership.tenant_id == tenant_context.tenant_id)
        .order_by(Society.name, SocietyMembership.role)
    )
    if scope is not None:
        society_statement = society_statement.where(SocietyMembership.society_id.in_(scope))
    society_rows = list(session.execute(society_statement))
    user_ids = {membership.user_id for membership in tenant_memberships}
    user_ids.update(membership.user_id for membership, _ in society_rows)
    if not user_ids:
        return []

    users = list(
        session.scalars(
            select(User)
            .where(User.id.in_(user_ids))
            .order_by(User.full_name, User.email, User.mobile_number)
        )
    )
    tenant_memberships_by_user: dict[uuid.UUID, list[TenantMembership]] = {user.id: [] for user in users}
    society_rows_by_user: dict[uuid.UUID, list[tuple[SocietyMembership, Society]]] = {user.id: [] for user in users}
    for membership in tenant_memberships:
        tenant_memberships_by_user.setdefault(membership.user_id, []).append(membership)
    for membership, society in society_rows:
        society_rows_by_user.setdefault(membership.user_id, []).append((membership, society))

    return [
        user_to_read(
            user,
            tenant_memberships=tenant_memberships_by_user.get(user.id, []),
            society_rows=society_rows_by_user.get(user.id, []),
        )
        for user in users
    ]


def provision_managed_user(
    session: Session,
    *,
    tenant_context: TenantContext,
    payload: ManagedUserCreate,
    actor: User,
) -> ManagedUserRead:
    validate_roles(payload)
    ensure_actor_can_assign_roles(session, tenant_context=tenant_context, payload=payload)
    keycloak_subject = provision_keycloak_user(payload)
    try:
        user = upsert_local_user(session, keycloak_subject=keycloak_subject, payload=payload)
        for role in sorted(set(payload.tenant_roles)):
            ensure_tenant_membership(
                session,
                tenant_id=tenant_context.tenant_id,
                user_id=user.id,
                role=role,
            )
        for assignment in payload.society_roles:
            ensure_society_membership(
                session,
                tenant_id=tenant_context.tenant_id,
                society_id=assignment.society_id,
                user_id=user.id,
                role=assignment.role,
            )

        record_audit_log(
            session,
            action="user.provisioned",
            entity_type="User",
            entity_id=user.id,
            actor_user_id=actor.id,
            tenant_id=tenant_context.tenant_id,
            summary=f"User provisioned: {user.full_name}",
            metadata={
                "email": user.email,
                "mobile_number": user.mobile_number,
                "tenant_roles": sorted(set(payload.tenant_roles)),
                "society_roles": [
                    {"society_id": str(assignment.society_id), "role": assignment.role}
                    for assignment in payload.society_roles
                ],
            },
        )
        session.commit()
        session.refresh(user)
    except IntegrityError as exc:
        session.rollback()
        raise UserAlreadyExistsError("User identity already exists.") from exc

    tenant_memberships = list(
        session.scalars(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_context.tenant_id,
                TenantMembership.user_id == user.id,
            )
        )
    )
    society_rows = list(
        session.execute(
            select(SocietyMembership, Society)
            .join(Society, Society.id == SocietyMembership.society_id)
            .where(
                SocietyMembership.tenant_id == tenant_context.tenant_id,
                SocietyMembership.user_id == user.id,
            )
            .order_by(Society.name, SocietyMembership.role)
        )
    )
    return user_to_read(user, tenant_memberships=tenant_memberships, society_rows=society_rows)


def change_managed_user_membership_status(
    session: Session,
    *,
    tenant_context: TenantContext,
    user_id: uuid.UUID,
    status: str,
    actor: User,
) -> ManagedUserRead:
    scope = get_user_management_scope(session, tenant_context=tenant_context)
    user = session.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise ManagedUserNotFoundError("User not found.")

    tenant_memberships = list(
        session.scalars(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_context.tenant_id,
                TenantMembership.user_id == user_id,
            )
        )
    ) if scope is None else []
    society_statement = (
        select(SocietyMembership, Society)
        .join(Society, Society.id == SocietyMembership.society_id)
        .where(
            SocietyMembership.tenant_id == tenant_context.tenant_id,
            SocietyMembership.user_id == user_id,
        )
        .order_by(Society.name, SocietyMembership.role)
    )
    if scope is not None:
        society_statement = society_statement.where(SocietyMembership.society_id.in_(scope))
    society_rows = list(session.execute(society_statement))
    if not tenant_memberships and not society_rows:
        raise ManagedUserNotFoundError("User is not assigned to this tenant.")

    for membership in tenant_memberships:
        membership.status = status
    for membership, _ in society_rows:
        membership.status = status

    record_audit_log(
        session,
        action=f"user.{status}",
        entity_type="User",
        entity_id=user.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"User {status}: {user.full_name}",
        metadata={"membership_scope": "tenant"},
    )
    session.commit()
    session.refresh(user)
    return user_to_read(user, tenant_memberships=tenant_memberships, society_rows=society_rows)
