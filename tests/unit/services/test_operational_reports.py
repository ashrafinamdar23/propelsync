from datetime import date
from decimal import Decimal
from io import BytesIO
import uuid
import zipfile

from app.schemas.operational_report import (
    BillingReportRead,
    BillingReportRow,
    CollectionReportRead,
    CollectionReportRow,
    DefaulterReportRead,
    DefaulterReportRow,
    ExpenseReportRead,
    ExpenseReportRow,
)
from app.services.operational_reports import (
    billing_export_table,
    collection_export_table,
    defaulter_export_table,
    expense_export_table,
    export_table,
    money,
)


def test_money_quantizes_to_two_decimals() -> None:
    assert money(Decimal("12.345")) == Decimal("12.35")


def test_operational_export_tables_build_xlsx_and_pdf() -> None:
    society_id = uuid.uuid4()
    invoice_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    expense_id = uuid.uuid4()
    flat_id = uuid.uuid4()

    billing = BillingReportRead(
        society_id=society_id,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        invoice_count=1,
        total_billed=Decimal("1000.00"),
        total_paid=Decimal("250.00"),
        total_due=Decimal("750.00"),
        rows=[
            BillingReportRow(
                invoice_id=invoice_id,
                invoice_number="INV-001",
                flat_number="101",
                building_name="A",
                invoice_date=date(2026, 4, 1),
                due_date=date(2026, 4, 10),
                billing_period_start=date(2026, 4, 1),
                billing_period_end=date(2026, 4, 30),
                total_amount=Decimal("1000.00"),
                amount_paid=Decimal("250.00"),
                amount_due=Decimal("750.00"),
                status="partially_paid",
            )
        ],
    )
    collection = CollectionReportRead(
        society_id=society_id,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        payment_count=1,
        total_collected=Decimal("250.00"),
        total_unapplied=Decimal("0.00"),
        rows=[
            CollectionReportRow(
                payment_id=payment_id,
                payment_date=date(2026, 4, 5),
                flat_number="101",
                building_name="A",
                payment_mode="upi",
                amount=Decimal("250.00"),
                unapplied_amount=Decimal("0.00"),
                status="received",
            )
        ],
    )
    expense = ExpenseReportRead(
        society_id=society_id,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        expense_count=1,
        total_expense=Decimal("500.00"),
        total_paid=Decimal("100.00"),
        total_due=Decimal("400.00"),
        rows=[
            ExpenseReportRow(
                expense_id=expense_id,
                expense_date=date(2026, 4, 6),
                due_date=date(2026, 4, 20),
                category_name="Housekeeping",
                expense_type="vendor_bill",
                description="Cleaning",
                amount=Decimal("500.00"),
                tax_amount=Decimal("0.00"),
                total_amount=Decimal("500.00"),
                amount_paid=Decimal("100.00"),
                amount_due=Decimal("400.00"),
                status="recorded",
                payment_status="partially_paid",
            )
        ],
    )
    defaulter = DefaulterReportRead(
        society_id=society_id,
        as_of_date=date(2026, 5, 15),
        defaulter_count=1,
        total_overdue=Decimal("750.00"),
        rows=[
            DefaulterReportRow(
                flat_id=flat_id,
                flat_number="101",
                building_name="A",
                invoice_count=1,
                overdue_amount=Decimal("750.00"),
                oldest_due_date=date(2026, 4, 10),
                days_overdue=35,
            )
        ],
    )

    for table in [
        billing_export_table(billing),
        collection_export_table(collection),
        expense_export_table(expense),
        defaulter_export_table(defaulter),
    ]:
        xlsx_content = export_table(table, "xlsx")
        pdf_content = export_table(table, "pdf")
        assert zipfile.is_zipfile(BytesIO(xlsx_content))
        assert pdf_content.startswith(b"%PDF-")
