import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    BillingRule,
    BillingRuleLateFeeRule,
    ChargeType,
    ChartOfAccount,
    Flat,
    FlatOwnership,
    Invoice,
    InvoiceLateFeeRule,
    InvoiceLineItem,
    JournalEntry,
    JournalLine,
    LateFeeRule,
    Owner,
    Society,
    User,
)
from app.schemas.invoice import InvoiceBulkCancelResponse, InvoiceBulkCancelResult, ManualInvoiceCreate
from app.schemas.invoice_generation import (
    InvoiceGenerationConfirmResponse,
    InvoiceGenerationLinePreview,
    InvoiceGenerationPreviewResponse,
    InvoiceGenerationPreviewRow,
    InvoiceGenerationRequest,
)
from app.services.document_sequences import next_invoice_number
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class InvoiceSocietyNotFoundError(Exception):
    pass


class InvoiceNotFoundError(Exception):
    pass


class InvoiceGenerationValidationError(Exception):
    def __init__(self, preview: InvoiceGenerationPreviewResponse) -> None:
        self.preview = preview
        super().__init__("Invoice generation has validation errors.")


class InvoiceGenerationRuleSelectionError(Exception):
    pass


class ManualInvoiceReferenceInvalidError(Exception):
    pass


class InvoiceCancellationInvalidError(Exception):
    pass


class InvoiceJournalPostingError(Exception):
    pass


MONEY_QUANT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def post_invoice_journal(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    invoice: Invoice,
    line_items: list[InvoiceLineItem],
) -> JournalEntry:
    society = session.scalar(
        select(Society).where(
            Society.id == society_id,
            Society.tenant_id == tenant_context.tenant_id,
        )
    )
    if society is None:
        raise InvoiceSocietyNotFoundError("Society not found.")
    if society.receivable_account_id is None:
        raise InvoiceJournalPostingError("Configure the society receivable account before creating invoices.")

    receivable_account = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == society.receivable_account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
            ChartOfAccount.account_type == "asset",
            ChartOfAccount.status == "active",
        )
    )
    if receivable_account is None:
        raise InvoiceJournalPostingError("Society receivable account must be an active asset account.")

    charge_type_ids = {line.charge_type_id for line in line_items}
    charge_types = {
        charge_type.id: charge_type
        for charge_type in session.scalars(
            select(ChargeType).where(
                ChargeType.id.in_(charge_type_ids),
                ChargeType.tenant_id == tenant_context.tenant_id,
                ChargeType.society_id == society_id,
                ChargeType.status == "active",
            )
        )
    }
    if charge_type_ids != set(charge_types):
        raise InvoiceJournalPostingError("All invoice charge types must be active before journal posting.")

    credit_amount_by_account_id: dict[uuid.UUID, Decimal] = {}
    for line in line_items:
        charge_type = charge_types[line.charge_type_id]
        if charge_type.revenue_account_id is None:
            raise InvoiceJournalPostingError("Every invoice charge type must have a revenue account.")
        credit_amount_by_account_id[charge_type.revenue_account_id] = money(
            credit_amount_by_account_id.get(charge_type.revenue_account_id, Decimal("0.00")) + line.line_amount
        )

    revenue_accounts = {
        account.id: account
        for account in session.scalars(
            select(ChartOfAccount).where(
                ChartOfAccount.id.in_(list(credit_amount_by_account_id)),
                ChartOfAccount.tenant_id == tenant_context.tenant_id,
                ChartOfAccount.society_id == society_id,
                ChartOfAccount.account_type == "income",
                ChartOfAccount.status == "active",
            )
        )
    }
    if set(credit_amount_by_account_id) != set(revenue_accounts):
        raise InvoiceJournalPostingError("Invoice revenue accounts must be active income accounts.")

    journal_entry = JournalEntry(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        journal_date=invoice.invoice_date,
        source_type="invoice",
        source_id=invoice.id,
        reference_number=invoice.invoice_number,
        description=f"Invoice posted: {invoice.invoice_number}",
        status="posted",
        notes=invoice.notes,
    )
    session.add(journal_entry)
    session.flush()

    session.add(
        JournalLine(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            journal_entry_id=journal_entry.id,
            account_id=receivable_account.id,
            line_number=1,
            description=f"Receivable for {invoice.invoice_number}",
            debit_amount=money(invoice.total_amount),
            credit_amount=Decimal("0.00"),
        )
    )
    for line_number, (account_id, credit_amount) in enumerate(credit_amount_by_account_id.items(), start=2):
        account = revenue_accounts[account_id]
        session.add(
            JournalLine(
                tenant_id=tenant_context.tenant_id,
                society_id=society_id,
                journal_entry_id=journal_entry.id,
                account_id=account_id,
                line_number=line_number,
                description=f"Revenue: {account.account_name}",
                debit_amount=Decimal("0.00"),
                credit_amount=money(credit_amount),
            )
        )

    invoice.journal_entry_id = journal_entry.id
    return journal_entry


def ensure_society_exists(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> None:
    society = session.scalar(
        select(Society).where(
            Society.id == society_id,
            Society.tenant_id == tenant_context.tenant_id,
        )
    )
    if society is None:
        raise InvoiceSocietyNotFoundError("Society not found.")


def list_invoices(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID | None = None,
    status: str | None = None,
    invoice_date_from: date | None = None,
    invoice_date_to: date | None = None,
) -> list[Invoice]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    statement = build_invoice_list_statement(
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        status=status,
        invoice_date_from=invoice_date_from,
        invoice_date_to=invoice_date_to,
    )
    return list(
        session.scalars(
            statement.order_by(Invoice.invoice_date.desc(), Invoice.invoice_number.desc())
        )
    )


def build_invoice_list_statement(
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID | None = None,
    status: str | None = None,
    invoice_date_from: date | None = None,
    invoice_date_to: date | None = None,
):
    statement = select(Invoice).where(
        Invoice.tenant_id == tenant_context.tenant_id,
        Invoice.society_id == society_id,
    )
    if flat_id is not None:
        statement = statement.where(Invoice.flat_id == flat_id)
    if status:
        statement = statement.where(Invoice.status == status)
    if invoice_date_from is not None:
        statement = statement.where(Invoice.invoice_date >= invoice_date_from)
    if invoice_date_to is not None:
        statement = statement.where(Invoice.invoice_date <= invoice_date_to)
    return statement


def list_invoices_paginated(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID | None = None,
    status: str | None = None,
    invoice_date_from: date | None = None,
    invoice_date_to: date | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Invoice], int]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    statement = build_invoice_list_statement(
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        status=status,
        invoice_date_from=invoice_date_from,
        invoice_date_to=invoice_date_to,
    )
    total_items = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = list(
        session.scalars(
            statement.order_by(Invoice.invoice_date.desc(), Invoice.invoice_number.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return rows, int(total_items)


def rule_applies_to_flat(rule: BillingRule, flat: Flat) -> bool:
    if rule.scope_type == "all_flats":
        return True
    if rule.scope_type == "building":
        return flat.building_id == rule.building_id
    if rule.scope_type == "wing":
        return flat.building_id == rule.building_id and flat.wing_id == rule.wing_id
    if rule.scope_type == "flat_type":
        return flat.flat_type_id == rule.flat_type_id
    return False


def rule_is_effective(rule: BillingRule, payload: InvoiceGenerationRequest) -> bool:
    return rule.effective_from <= payload.billing_period_end and (
        rule.effective_to is None or rule.effective_to >= payload.billing_period_start
    )


def load_generation_context(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: InvoiceGenerationRequest,
) -> tuple[list[Flat], list[BillingRule], list[tuple[uuid.UUID, uuid.UUID]], list[FlatOwnership]]:
    flats = list(
        session.scalars(
            select(Flat).where(
                Flat.tenant_id == tenant_context.tenant_id,
                Flat.society_id == society_id,
                Flat.status == "active",
            )
        )
    )
    rules = list(
        session.scalars(
            select(BillingRule).where(
                BillingRule.tenant_id == tenant_context.tenant_id,
                BillingRule.society_id == society_id,
                BillingRule.status == "active",
                BillingRule.calculation_method != "manual",
                BillingRule.id.in_(payload.billing_rule_ids),
            )
        )
    )
    found_rule_ids = {rule.id for rule in rules}
    missing_rule_ids = set(payload.billing_rule_ids) - found_rule_ids
    if missing_rule_ids:
        raise InvoiceGenerationRuleSelectionError("One or more selected billing rules are not active.")
    existing_rule_lines = [
        (row.flat_id, row.billing_rule_id)
        for row in session.execute(
            select(Invoice.flat_id, InvoiceLineItem.billing_rule_id)
            .join(Invoice, Invoice.id == InvoiceLineItem.invoice_id)
            .where(
                InvoiceLineItem.tenant_id == tenant_context.tenant_id,
                InvoiceLineItem.society_id == society_id,
                InvoiceLineItem.billing_rule_id.in_(payload.billing_rule_ids),
                InvoiceLineItem.billing_rule_id.is_not(None),
                Invoice.tenant_id == tenant_context.tenant_id,
                Invoice.society_id == society_id,
                Invoice.billing_period_start == payload.billing_period_start,
                Invoice.billing_period_end == payload.billing_period_end,
                Invoice.status != "cancelled",
            )
        )
    ]
    ownerships = list(
        session.scalars(
            select(FlatOwnership).where(
                FlatOwnership.tenant_id == tenant_context.tenant_id,
                FlatOwnership.society_id == society_id,
                FlatOwnership.ownership_type == "primary_owner",
                FlatOwnership.status == "active",
                FlatOwnership.effective_from <= payload.billing_period_end,
            )
        )
    )
    return flats, rules, existing_rule_lines, ownerships


def calculate_line(rule: BillingRule, flat: Flat) -> InvoiceGenerationLinePreview | None:
    if rule.amount is None:
        return None
    unit_amount = money(rule.amount)
    quantity = Decimal("1.00")

    if rule.calculation_method == "area_based":
        area = flat.carpet_area_sqft if rule.area_basis == "carpet_area" else flat.built_up_area_sqft
        if area is None:
            raise ValueError("Flat area is missing for area-based rule.")
        quantity = Decimal(area)
    elif rule.calculation_method == "parking_based":
        quantity = Decimal(flat.parking_count or 0)
        if quantity == 0:
            return None

    line_amount = money(quantity * unit_amount)
    if line_amount == 0:
        return None

    return InvoiceGenerationLinePreview(
        billing_rule_id=rule.id,
        charge_type_id=rule.charge_type_id,
        description=rule.name,
        quantity=money(quantity),
        unit_amount=unit_amount,
        line_amount=line_amount,
    )


def build_invoice_generation_preview(
    *,
    payload: InvoiceGenerationRequest,
    flats: list[Flat],
    rules: list[BillingRule],
    existing_rule_lines: list[tuple[uuid.UUID, uuid.UUID]],
    ownerships: list[FlatOwnership],
) -> InvoiceGenerationPreviewResponse:
    existing_rule_ids_by_flat_id: dict[uuid.UUID, set[uuid.UUID]] = {}
    for flat_id, billing_rule_id in existing_rule_lines:
        existing_rule_ids_by_flat_id.setdefault(flat_id, set()).add(billing_rule_id)
    owner_by_flat_id = {
        ownership.flat_id: ownership.owner_id
        for ownership in ownerships
        if ownership.effective_to is None or ownership.effective_to >= payload.billing_period_start
    }
    rows: list[InvoiceGenerationPreviewRow] = []

    for flat in flats:
        errors: list[str] = []
        lines: list[InvoiceGenerationLinePreview] = []

        applicable_rules = [
            rule for rule in rules if rule_is_effective(rule, payload) and rule_applies_to_flat(rule, flat)
        ]
        for rule in applicable_rules:
            if rule.id in existing_rule_ids_by_flat_id.get(flat.id, set()):
                errors.append(f"{rule.name}: billing rule already invoiced for this flat and period.")
                continue
            try:
                line = calculate_line(rule, flat)
                if line is not None:
                    lines.append(line)
            except ValueError as exc:
                errors.append(f"{rule.name}: {exc}")

        total_amount = money(sum((line.line_amount for line in lines), Decimal("0.00")))
        status = "invalid" if errors else "valid"
        if not errors and not lines:
            status = "skipped"
        rows.append(
            InvoiceGenerationPreviewRow(
                flat_id=flat.id,
                flat_number=flat.flat_number,
                owner_id=owner_by_flat_id.get(flat.id),
                status=status,
                errors=errors,
                total_amount=total_amount,
                lines=lines,
            )
        )

    valid_rows = sum(1 for row in rows if row.status == "valid")
    invalid_rows = sum(1 for row in rows if row.status == "invalid")
    skipped_rows = sum(1 for row in rows if row.status == "skipped")
    return InvoiceGenerationPreviewResponse(
        billing_period_start=payload.billing_period_start,
        billing_period_end=payload.billing_period_end,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        total_flats=len(rows),
        invoice_count=valid_rows,
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        skipped_rows=skipped_rows,
        total_amount=money(sum((row.total_amount for row in rows if row.status == "valid"), Decimal("0.00"))),
        rows=rows,
    )


def validate_late_fee_rule_ids(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    late_fee_rule_ids: list[uuid.UUID],
) -> None:
    if not late_fee_rule_ids:
        return
    if len(set(late_fee_rule_ids)) != len(late_fee_rule_ids):
        raise ManualInvoiceReferenceInvalidError("Penalty rules cannot contain duplicates.")
    found_rule_ids = set(
        session.scalars(
            select(LateFeeRule.id).where(
                LateFeeRule.id.in_(late_fee_rule_ids),
                LateFeeRule.tenant_id == tenant_context.tenant_id,
                LateFeeRule.society_id == society_id,
                LateFeeRule.status == "active",
            )
        )
    )
    if found_rule_ids != set(late_fee_rule_ids):
        raise ManualInvoiceReferenceInvalidError("All penalty rules must be active and belong to this society.")


def snapshot_invoice_late_fee_rules(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    invoice: Invoice,
    billing_rule_ids: set[uuid.UUID] | None = None,
    manual_late_fee_rule_ids: list[uuid.UUID] | None = None,
) -> None:
    snapshot_rows: list[tuple[uuid.UUID, int, str]] = []
    seen_rule_ids: set[uuid.UUID] = set()

    if billing_rule_ids:
        mappings = list(
            session.scalars(
                select(BillingRuleLateFeeRule)
                .where(
                    BillingRuleLateFeeRule.tenant_id == tenant_context.tenant_id,
                    BillingRuleLateFeeRule.society_id == society_id,
                    BillingRuleLateFeeRule.billing_rule_id.in_(billing_rule_ids),
                    BillingRuleLateFeeRule.status == "active",
                    BillingRuleLateFeeRule.effective_from <= invoice.invoice_date,
                    (
                        BillingRuleLateFeeRule.effective_to.is_(None)
                        | (BillingRuleLateFeeRule.effective_to >= invoice.invoice_date)
                    ),
                )
                .order_by(BillingRuleLateFeeRule.priority)
            )
        )
        for mapping in mappings:
            if mapping.late_fee_rule_id in seen_rule_ids:
                continue
            seen_rule_ids.add(mapping.late_fee_rule_id)
            snapshot_rows.append((mapping.late_fee_rule_id, mapping.priority, "billing_rule"))

    if manual_late_fee_rule_ids:
        validate_late_fee_rule_ids(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            late_fee_rule_ids=manual_late_fee_rule_ids,
        )
        for priority, late_fee_rule_id in enumerate(manual_late_fee_rule_ids):
            if late_fee_rule_id in seen_rule_ids:
                continue
            seen_rule_ids.add(late_fee_rule_id)
            snapshot_rows.append((late_fee_rule_id, priority, "manual_invoice"))

    for late_fee_rule_id, priority, source_type in snapshot_rows:
        session.add(
            InvoiceLateFeeRule(
                tenant_id=tenant_context.tenant_id,
                society_id=society_id,
                invoice_id=invoice.id,
                late_fee_rule_id=late_fee_rule_id,
                priority=priority,
                source_type=source_type,
                status="active",
            )
        )


def preview_invoice_generation(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: InvoiceGenerationRequest,
) -> InvoiceGenerationPreviewResponse:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    flats, rules, existing_rule_lines, ownerships = load_generation_context(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )
    return build_invoice_generation_preview(
        payload=payload,
        flats=flats,
        rules=rules,
        existing_rule_lines=existing_rule_lines,
        ownerships=ownerships,
    )


def confirm_invoice_generation(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: InvoiceGenerationRequest,
    actor: User,
) -> InvoiceGenerationConfirmResponse:
    preview = preview_invoice_generation(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )
    if preview.invalid_rows:
        raise InvoiceGenerationValidationError(preview)

    invoices: list[Invoice] = []

    for row in preview.rows:
        if row.status != "valid":
            continue
        invoice = Invoice(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            flat_id=row.flat_id,
            owner_id=row.owner_id,
            invoice_number=next_invoice_number(
                session,
                tenant_context=tenant_context,
                society_id=society_id,
                invoice_date=payload.invoice_date,
                billing_period_start=payload.billing_period_start,
            ),
            invoice_date=payload.invoice_date,
            due_date=payload.due_date,
            billing_period_start=payload.billing_period_start,
            billing_period_end=payload.billing_period_end,
            total_amount=row.total_amount,
            amount_paid=Decimal("0.00"),
            amount_due=row.total_amount,
            status="issued",
        )
        session.add(invoice)
        session.flush()
        invoice_lines: list[InvoiceLineItem] = []
        for line_number, line in enumerate(row.lines, start=1):
            invoice_line = InvoiceLineItem(
                tenant_id=tenant_context.tenant_id,
                society_id=society_id,
                invoice_id=invoice.id,
                charge_type_id=line.charge_type_id,
                billing_rule_id=line.billing_rule_id,
                line_number=line_number,
                description=line.description,
                quantity=line.quantity,
                unit_amount=line.unit_amount,
                line_amount=line.line_amount,
            )
            session.add(invoice_line)
            invoice_lines.append(invoice_line)
        snapshot_invoice_late_fee_rules(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            invoice=invoice,
            billing_rule_ids={
                line.billing_rule_id for line in invoice_lines if line.billing_rule_id is not None
            },
        )
        post_invoice_journal(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            invoice=invoice,
            line_items=invoice_lines,
        )
        invoices.append(invoice)

    record_audit_log(
        session,
        action="invoice_generation.completed",
        entity_type="Invoice",
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Invoice generation completed: {len(invoices)} invoices",
        metadata={
            "society_id": str(society_id),
            "billing_period_start": payload.billing_period_start.isoformat(),
            "billing_period_end": payload.billing_period_end.isoformat(),
            "invoice_ids": [str(invoice.id) for invoice in invoices],
            "billing_rule_ids": [str(rule_id) for rule_id in payload.billing_rule_ids],
        },
    )
    session.commit()
    return InvoiceGenerationConfirmResponse(
        generated_count=len(invoices),
        invoice_ids=[invoice.id for invoice in invoices],
    )


def get_primary_owner_id_for_flat(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID,
    effective_date: date,
) -> uuid.UUID | None:
    ownership = session.scalar(
        select(FlatOwnership).where(
            FlatOwnership.tenant_id == tenant_context.tenant_id,
            FlatOwnership.society_id == society_id,
            FlatOwnership.flat_id == flat_id,
            FlatOwnership.ownership_type == "primary_owner",
            FlatOwnership.status == "active",
            FlatOwnership.effective_from <= effective_date,
            (FlatOwnership.effective_to.is_(None) | (FlatOwnership.effective_to >= effective_date)),
        )
    )
    return ownership.owner_id if ownership is not None else None


def ensure_manual_invoice_references(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: ManualInvoiceCreate,
) -> tuple[Flat, uuid.UUID | None]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    flat = session.scalar(
        select(Flat).where(
            Flat.id == payload.flat_id,
            Flat.tenant_id == tenant_context.tenant_id,
            Flat.society_id == society_id,
            Flat.status == "active",
        )
    )
    if flat is None:
        raise ManualInvoiceReferenceInvalidError("Flat must be active and belong to this society.")

    owner_id = payload.owner_id
    if owner_id is None:
        owner_id = get_primary_owner_id_for_flat(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            flat_id=payload.flat_id,
            effective_date=payload.invoice_date,
        )
    else:
        owner = session.scalar(
            select(Owner).where(
                Owner.id == owner_id,
                Owner.tenant_id == tenant_context.tenant_id,
                Owner.society_id == society_id,
                Owner.status == "active",
            )
        )
        if owner is None:
            raise ManualInvoiceReferenceInvalidError("Owner must be active and belong to this society.")

    charge_type_ids = {line.charge_type_id for line in payload.line_items}
    active_charge_type_ids = set(
        session.scalars(
            select(ChargeType.id).where(
                ChargeType.id.in_(charge_type_ids),
                ChargeType.tenant_id == tenant_context.tenant_id,
                ChargeType.society_id == society_id,
                ChargeType.status == "active",
            )
        )
    )
    if charge_type_ids != active_charge_type_ids:
        raise ManualInvoiceReferenceInvalidError("All charge types must be active and belong to this society.")
    validate_late_fee_rule_ids(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        late_fee_rule_ids=payload.late_fee_rule_ids,
    )

    return flat, owner_id


def create_manual_invoice(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: ManualInvoiceCreate,
    actor: User,
) -> Invoice:
    _, owner_id = ensure_manual_invoice_references(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )
    line_amounts = [money(line.quantity * line.unit_amount) for line in payload.line_items]
    total_amount = money(sum(line_amounts, Decimal("0.00")))

    invoice = Invoice(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        flat_id=payload.flat_id,
        owner_id=owner_id,
        invoice_number=next_invoice_number(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            invoice_date=payload.invoice_date,
            billing_period_start=payload.billing_period_start,
        ),
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        billing_period_start=payload.billing_period_start,
        billing_period_end=payload.billing_period_end,
        total_amount=total_amount,
        amount_paid=Decimal("0.00"),
        amount_due=total_amount,
        status="issued",
        notes=payload.notes,
    )
    session.add(invoice)
    session.flush()

    invoice_lines: list[InvoiceLineItem] = []
    for line_number, (line, line_amount) in enumerate(zip(payload.line_items, line_amounts), start=1):
        invoice_line = InvoiceLineItem(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            invoice_id=invoice.id,
            charge_type_id=line.charge_type_id,
            billing_rule_id=None,
            line_number=line_number,
            description=line.description,
            quantity=money(line.quantity),
            unit_amount=money(line.unit_amount),
            line_amount=line_amount,
        )
        session.add(invoice_line)
        invoice_lines.append(invoice_line)

    snapshot_invoice_late_fee_rules(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        invoice=invoice,
        manual_late_fee_rule_ids=payload.late_fee_rule_ids,
    )
    post_invoice_journal(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        invoice=invoice,
        line_items=invoice_lines,
    )

    record_audit_log(
        session,
        action="invoice.manual.created",
        entity_type="Invoice",
        entity_id=invoice.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Manual invoice created: {invoice.invoice_number}",
        metadata={"society_id": str(society_id), "flat_id": str(payload.flat_id)},
    )
    session.commit()
    session.refresh(invoice)
    return invoice


def cancel_invoice(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    invoice_id: uuid.UUID,
    reason: str,
    actor: User,
) -> Invoice:
    invoice = get_invoice_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        invoice_id=invoice_id,
    )
    if invoice.status == "cancelled":
        raise InvoiceCancellationInvalidError("Invoice is already cancelled.")
    if invoice.amount_paid > 0:
        raise InvoiceCancellationInvalidError("Paid invoices cannot be cancelled directly.")

    invoice.status = "cancelled"
    invoice.amount_due = Decimal("0.00")
    invoice.notes = f"{invoice.notes}\nCancellation reason: {reason}" if invoice.notes else f"Cancellation reason: {reason}"
    if invoice.journal_entry_id is not None:
        journal_entry = session.scalar(
            select(JournalEntry).where(
                JournalEntry.id == invoice.journal_entry_id,
                JournalEntry.tenant_id == tenant_context.tenant_id,
                JournalEntry.society_id == society_id,
            )
        )
        if journal_entry is not None:
            journal_entry.status = "reversed"
    record_audit_log(
        session,
        action="invoice.cancelled",
        entity_type="Invoice",
        entity_id=invoice.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Invoice cancelled: {invoice.invoice_number}",
        metadata={"society_id": str(society_id), "reason": reason},
    )
    session.commit()
    session.refresh(invoice)
    return invoice


def bulk_cancel_invoices(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    invoice_ids: list[uuid.UUID],
    reason: str,
    actor: User,
) -> InvoiceBulkCancelResponse:
    results: list[InvoiceBulkCancelResult] = []
    seen_invoice_ids: set[uuid.UUID] = set()

    for invoice_id in invoice_ids:
        if invoice_id in seen_invoice_ids:
            results.append(
                InvoiceBulkCancelResult(
                    invoice_id=invoice_id,
                    status="failed",
                    error="Duplicate invoice selected.",
                )
            )
            continue
        seen_invoice_ids.add(invoice_id)
        try:
            invoice = cancel_invoice(
                session,
                tenant_context=tenant_context,
                society_id=society_id,
                invoice_id=invoice_id,
                reason=reason,
                actor=actor,
            )
        except (InvoiceNotFoundError, InvoiceCancellationInvalidError) as exc:
            session.rollback()
            results.append(
                InvoiceBulkCancelResult(
                    invoice_id=invoice_id,
                    status="failed",
                    error=str(exc),
                )
            )
            continue
        results.append(
            InvoiceBulkCancelResult(
                invoice_id=invoice.id,
                invoice_number=invoice.invoice_number,
                status="cancelled",
            )
        )

    cancelled_count = sum(1 for result in results if result.status == "cancelled")
    return InvoiceBulkCancelResponse(
        requested_count=len(invoice_ids),
        cancelled_count=cancelled_count,
        failed_count=len(results) - cancelled_count,
        results=results,
    )


def get_invoice_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> Invoice:
    invoice = session.scalar(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.tenant_id == tenant_context.tenant_id,
            Invoice.society_id == society_id,
        )
    )
    if invoice is None:
        raise InvoiceNotFoundError("Invoice not found.")
    return invoice


def list_invoice_line_items(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> list[InvoiceLineItem]:
    return list(
        session.scalars(
            select(InvoiceLineItem)
            .where(
                InvoiceLineItem.tenant_id == tenant_context.tenant_id,
                InvoiceLineItem.society_id == society_id,
                InvoiceLineItem.invoice_id == invoice_id,
            )
            .order_by(InvoiceLineItem.line_number)
        )
    )
