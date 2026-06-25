from __future__ import annotations

import argparse
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Expense, ExpensePaymentAllocation
from app.services.expenses import create_immediate_expense_payment_record
from app.tenants.context import TenantContext


@dataclass(frozen=True)
class BackfillResult:
    eligible_expenses: int
    created_payments: int
    applied: bool


def find_missing_immediate_expense_payments(session: Session) -> list[Expense]:
    allocation_exists = (
        select(ExpensePaymentAllocation.id)
        .where(
            ExpensePaymentAllocation.tenant_id == Expense.tenant_id,
            ExpensePaymentAllocation.society_id == Expense.society_id,
            ExpensePaymentAllocation.expense_id == Expense.id,
            ExpensePaymentAllocation.status == "active",
        )
        .exists()
    )
    return list(
        session.scalars(
            select(Expense)
            .where(
                Expense.expense_type.in_(("cash_expense", "other")),
                Expense.payment_account_id.is_not(None),
                Expense.journal_entry_id.is_not(None),
                Expense.status != "cancelled",
                Expense.payment_status == "paid",
                Expense.amount_due == 0,
                Expense.amount_paid == Expense.total_amount,
                ~allocation_exists,
            )
            .order_by(Expense.expense_date, Expense.created_at)
        )
    )


def backfill_immediate_expense_payments(session: Session, *, apply: bool) -> BackfillResult:
    expenses = find_missing_immediate_expense_payments(session)
    if not apply:
        return BackfillResult(eligible_expenses=len(expenses), created_payments=0, applied=False)

    for expense in expenses:
        create_immediate_expense_payment_record(
            session,
            tenant_context=TenantContext(tenant_id=expense.tenant_id, tenant=None, user=None),  # type: ignore[arg-type]
            society_id=expense.society_id,
            expense=expense,
        )
    session.commit()
    return BackfillResult(eligible_expenses=len(expenses), created_payments=len(expenses), applied=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill missing expense payment rows for immediate-paid cash/other expenses."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create the missing expense payment and allocation rows. Without this flag, only previews the count.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with SessionLocal() as session:
        result = backfill_immediate_expense_payments(session, apply=args.apply)

    if result.applied:
        print(
            "Immediate expense payment backfill applied. "
            f"Eligible expenses: {result.eligible_expenses}. "
            f"Payments created: {result.created_payments}."
        )
    else:
        print(
            "Immediate expense payment backfill preview. "
            f"Eligible expenses: {result.eligible_expenses}. "
            "Run again with --apply to create payment rows."
        )


if __name__ == "__main__":
    main()
