from fastapi import APIRouter

from app.api.v1.endpoints import (
    account_ledgers,
    account_transfers,
    auth,
    balance_sheet,
    billing_rules,
    building_floors,
    buildings,
    chart_of_accounts,
    charge_types,
    document_sequences,
    expenses,
    expense_categories,
    expense_payments,
    flat_ownerships,
    flat_ledgers,
    flat_types,
    flats,
    health,
    invoices,
    income_expense,
    journals,
    late_fees,
    lease_agreements,
    monthly_reports,
    outstanding,
    owners,
    operational_reports,
    other_income,
    payments,
    platform,
    residents,
    scheduled_jobs,
    societies,
    trial_balance,
    user_management,
    vendors,
    wings,
)


api_router = APIRouter()
api_router.include_router(account_ledgers.router, tags=["account-ledgers"])
api_router.include_router(account_transfers.router, tags=["account-transfers"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(balance_sheet.router, tags=["reports"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(platform.router, tags=["platform"])
api_router.include_router(societies.router, tags=["societies"])
api_router.include_router(trial_balance.router, tags=["trial-balance"])
api_router.include_router(user_management.router, tags=["users"])
api_router.include_router(buildings.router, tags=["buildings"])
api_router.include_router(chart_of_accounts.router, tags=["chart-of-accounts"])
api_router.include_router(building_floors.router, tags=["building-floors"])
api_router.include_router(wings.router, tags=["wings"])
api_router.include_router(flats.router, tags=["flats"])
api_router.include_router(flat_ledgers.router, tags=["flat-ledgers"])
api_router.include_router(flat_types.router, tags=["flat-types"])
api_router.include_router(charge_types.router, tags=["charge-types"])
api_router.include_router(billing_rules.router, tags=["billing-rules"])
api_router.include_router(document_sequences.router, tags=["document-sequences"])
api_router.include_router(expense_categories.router, tags=["expense-categories"])
api_router.include_router(expenses.router, tags=["expenses"])
api_router.include_router(expense_payments.router, tags=["expense-payments"])
api_router.include_router(invoices.router, tags=["invoices"])
api_router.include_router(income_expense.router, tags=["reports"])
api_router.include_router(journals.router, tags=["journals"])
api_router.include_router(late_fees.router, tags=["late-fees"])
api_router.include_router(lease_agreements.router, tags=["lease-agreements"])
api_router.include_router(monthly_reports.router, tags=["reports"])
api_router.include_router(outstanding.router, tags=["outstanding"])
api_router.include_router(operational_reports.router, tags=["reports"])
api_router.include_router(other_income.router, tags=["other-income"])
api_router.include_router(payments.router, tags=["payments"])
api_router.include_router(owners.router, tags=["owners"])
api_router.include_router(flat_ownerships.router, tags=["flat-ownerships"])
api_router.include_router(residents.router, tags=["residents"])
api_router.include_router(scheduled_jobs.router, tags=["scheduled-jobs"])
api_router.include_router(vendors.router, tags=["vendors"])
