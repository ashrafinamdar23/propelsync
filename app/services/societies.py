import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import ChartOfAccount, Society, User
from app.schemas.society import SocietyCreate, SocietyUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class SocietyAlreadyExistsError(Exception):
    pass


class SocietyNotFoundError(Exception):
    pass


class SocietyAccountInvalidError(Exception):
    pass


def ensure_receivable_account_valid(
    session: Session,
    *,
    tenant_context: TenantContext,
    account_id: uuid.UUID | None,
    society_id: uuid.UUID | None = None,
) -> None:
    if account_id is None:
        return
    if society_id is None:
        raise SocietyAccountInvalidError("Receivable account can be configured after society creation.")
    filters = [
        ChartOfAccount.id == account_id,
        ChartOfAccount.tenant_id == tenant_context.tenant_id,
        ChartOfAccount.society_id == society_id,
        ChartOfAccount.account_type == "asset",
        ChartOfAccount.status == "active",
    ]
    account = session.scalar(
        select(ChartOfAccount).where(*filters)
    )
    if account is None:
        raise SocietyAccountInvalidError("Receivable account must be an active asset account.")


def ensure_payable_account_valid(
    session: Session,
    *,
    tenant_context: TenantContext,
    account_id: uuid.UUID | None,
    society_id: uuid.UUID | None = None,
) -> None:
    if account_id is None:
        return
    if society_id is None:
        raise SocietyAccountInvalidError("Payable account can be configured after society creation.")
    account = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
            ChartOfAccount.account_type == "liability",
            ChartOfAccount.status == "active",
        )
    )
    if account is None:
        raise SocietyAccountInvalidError("Payable account must be an active liability account.")


def ensure_member_advance_account_valid(
    session: Session,
    *,
    tenant_context: TenantContext,
    account_id: uuid.UUID | None,
    society_id: uuid.UUID | None = None,
) -> None:
    if account_id is None:
        return
    if society_id is None:
        raise SocietyAccountInvalidError("Member advance account can be configured after society creation.")
    account = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
            ChartOfAccount.account_type == "liability",
            ChartOfAccount.status == "active",
        )
    )
    if account is None:
        raise SocietyAccountInvalidError("Member advance account must be an active liability account.")


def list_societies(session: Session, tenant_context: TenantContext) -> list[Society]:
    return list(
        session.scalars(
            select(Society)
            .where(Society.tenant_id == tenant_context.tenant_id)
            .order_by(Society.name)
        )
    )


def get_society_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> Society:
    society = session.scalar(
        select(Society).where(
            Society.id == society_id,
            Society.tenant_id == tenant_context.tenant_id,
        )
    )
    if society is None:
        raise SocietyNotFoundError("Society not found.")
    return society


def ensure_society_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    payload: SocietyCreate | SocietyUpdate,
    existing_society_id: uuid.UUID | None = None,
) -> None:
    filters = [Society.name == payload.name]
    if payload.registration_number:
        filters.append(Society.registration_number == payload.registration_number)

    statement = select(Society).where(
        Society.tenant_id == tenant_context.tenant_id,
        or_(*filters),
    )
    if existing_society_id is not None:
        statement = statement.where(Society.id != existing_society_id)

    if session.scalar(statement) is not None:
        raise SocietyAlreadyExistsError("Society name or registration number already exists.")


def create_society(
    session: Session,
    *,
    tenant_context: TenantContext,
    payload: SocietyCreate,
    actor: User,
) -> Society:
    ensure_society_unique(session, tenant_context=tenant_context, payload=payload)
    ensure_receivable_account_valid(
        session,
        tenant_context=tenant_context,
        account_id=payload.receivable_account_id,
        society_id=None,
    )
    ensure_payable_account_valid(
        session,
        tenant_context=tenant_context,
        account_id=payload.payable_account_id,
        society_id=None,
    )
    ensure_member_advance_account_valid(
        session,
        tenant_context=tenant_context,
        account_id=payload.member_advance_account_id,
        society_id=None,
    )

    society = Society(
        tenant_id=tenant_context.tenant_id,
        name=payload.name,
        registration_number=payload.registration_number,
        address_line1=payload.address_line1,
        address_line2=payload.address_line2,
        city=payload.city,
        state=payload.state,
        postal_code=payload.postal_code,
        country=payload.country,
        timezone=payload.timezone,
        locale=payload.locale,
        currency=payload.currency.upper(),
        financial_year_start_month=payload.financial_year_start_month,
        receivable_account_id=payload.receivable_account_id,
        payable_account_id=payload.payable_account_id,
        member_advance_account_id=payload.member_advance_account_id,
        status="active",
    )
    session.add(society)
    session.flush()

    record_audit_log(
        session,
        action="society.created",
        entity_type="Society",
        entity_id=society.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Society created: {society.name}",
        metadata={
            "registration_number": society.registration_number,
            "currency": society.currency,
            "receivable_account_id": str(society.receivable_account_id) if society.receivable_account_id else None,
            "payable_account_id": str(society.payable_account_id) if society.payable_account_id else None,
            "member_advance_account_id": (
                str(society.member_advance_account_id) if society.member_advance_account_id else None
            ),
        },
    )
    session.commit()
    session.refresh(society)
    return society


def update_society(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: SocietyUpdate,
    actor: User,
) -> Society:
    society = get_society_or_raise(session, tenant_context=tenant_context, society_id=society_id)
    ensure_society_unique(
        session,
        tenant_context=tenant_context,
        payload=payload,
        existing_society_id=society.id,
    )
    ensure_receivable_account_valid(
        session,
        tenant_context=tenant_context,
        account_id=payload.receivable_account_id,
        society_id=society.id,
    )
    ensure_payable_account_valid(
        session,
        tenant_context=tenant_context,
        account_id=payload.payable_account_id,
        society_id=society.id,
    )
    ensure_member_advance_account_valid(
        session,
        tenant_context=tenant_context,
        account_id=payload.member_advance_account_id,
        society_id=society.id,
    )

    previous_values = {
        "name": society.name,
        "registration_number": society.registration_number,
        "city": society.city,
        "state": society.state,
        "timezone": society.timezone,
        "locale": society.locale,
        "currency": society.currency,
        "financial_year_start_month": society.financial_year_start_month,
        "receivable_account_id": str(society.receivable_account_id) if society.receivable_account_id else None,
        "payable_account_id": str(society.payable_account_id) if society.payable_account_id else None,
        "member_advance_account_id": (
            str(society.member_advance_account_id) if society.member_advance_account_id else None
        ),
    }

    society.name = payload.name
    society.registration_number = payload.registration_number
    society.address_line1 = payload.address_line1
    society.address_line2 = payload.address_line2
    society.city = payload.city
    society.state = payload.state
    society.postal_code = payload.postal_code
    society.country = payload.country
    society.timezone = payload.timezone
    society.locale = payload.locale
    society.currency = payload.currency.upper()
    society.financial_year_start_month = payload.financial_year_start_month
    society.receivable_account_id = payload.receivable_account_id
    society.payable_account_id = payload.payable_account_id
    society.member_advance_account_id = payload.member_advance_account_id

    record_audit_log(
        session,
        action="society.updated",
        entity_type="Society",
        entity_id=society.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Society updated: {society.name}",
        metadata={
            "previous": previous_values,
            "current": {
                "name": society.name,
                "registration_number": society.registration_number,
                "city": society.city,
                "state": society.state,
                "timezone": society.timezone,
                "locale": society.locale,
                "currency": society.currency,
                "financial_year_start_month": society.financial_year_start_month,
                "receivable_account_id": str(society.receivable_account_id) if society.receivable_account_id else None,
                "payable_account_id": str(society.payable_account_id) if society.payable_account_id else None,
                "member_advance_account_id": (
                    str(society.member_advance_account_id) if society.member_advance_account_id else None
                ),
            },
        },
    )
    session.commit()
    session.refresh(society)
    return society


def change_society_status(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    status: str,
    actor: User,
) -> Society:
    society = get_society_or_raise(session, tenant_context=tenant_context, society_id=society_id)
    previous_status = society.status
    society.status = status

    action = "society.suspended" if status == "suspended" else "society.activated"
    record_audit_log(
        session,
        action=action,
        entity_type="Society",
        entity_id=society.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Society {status}: {society.name}",
        metadata={
            "previous_status": previous_status,
            "current_status": status,
        },
    )
    session.commit()
    session.refresh(society)
    return society
