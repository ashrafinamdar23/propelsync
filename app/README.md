# Propelsync API

The API service is a FastAPI application running inside Docker.

## Start

```powershell
docker compose up -d api
```

## Health Checks

```powershell
docker compose exec api python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/v1/health').read().decode())"
docker compose exec api python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/v1/health/ready').read().decode())"
```

## Tests

```powershell
docker compose exec api python -m pytest
```

## Migrations

```powershell
docker compose exec api alembic upgrade head
```

The API uses the `DATABASE_URL` environment variable in Docker Compose to connect to PostgreSQL.

## Background Worker

The worker service uses Celery with Redis as broker and result backend.

```powershell
docker compose up -d redis worker
docker compose exec api celery -A app.worker.celery_app inspect ping
```

Available foundation tasks:

```text
propelsync.worker.ping
propelsync.scheduled_jobs.scan_due_work
propelsync.scheduled_jobs.run_due_jobs
```

`scan_due_work` is read-only. It checks active societies for due billing rules and penalty rules but
does not generate invoices.

`run_due_jobs` executes due billing and penalty work for active societies through the same service as
the manual API workflow. It writes `scheduled_job_runs` with `run_mode=scheduled` and uses the local
system actor configured through `SCHEDULED_JOBS_SYSTEM_ACTOR_*` settings so audit logs remain
traceable.

## Bootstrap Identity

Create the local Keycloak realm, API/web clients, and first Propelsync platform superuser:

```powershell
docker compose exec api python -m app.scripts.bootstrap_identity
```

The script is repeatable. It reads bootstrap values from `.env` through Docker Compose.

## Auth Smoke Checks

Protected routes:

```text
GET /api/v1/auth/me
GET /api/v1/auth/my-access
GET /api/v1/auth/platform-superuser
```

Both require a Keycloak bearer token for a user that exists in the local `users` table.

`/auth/my-access` returns the authenticated user's platform flag, tenant memberships, and society
memberships so the frontend can bootstrap the correct admin context without platform-only APIs.

## Tenant Context

Tenant-owned APIs should require:

```text
X-Tenant-Id: <tenant uuid>
```

Business tables should use `TenantOwnedMixin`, and data access should go through tenant-scoped helpers.

## Memberships And Roles

Platform superuser access is stored on `users.is_platform_superuser`.

Tenant-level access is stored in `tenant_memberships`.

Supported tenant roles:

```text
tenant_admin
```

Society-level access is stored in `society_memberships`.

Supported society roles:

```text
society_admin
treasurer
accountant
auditor
committee_member
flat_owner
read_only_resident
```

`flat_owner` is an application access role. The legal/business ownership record should still be
modeled separately through owner and flat ownership tables.

## User Management APIs

Tenant-scoped user management routes:

```text
GET /api/v1/users
POST /api/v1/users
POST /api/v1/users/{user_id}/suspend
POST /api/v1/users/{user_id}/activate
```

These routes require a valid bearer token and `X-Tenant-Id`. Keycloak owns identity and password
login. Propelsync owns application authorization through `tenant_memberships` and
`society_memberships`.

Creating a user provisions or updates the Keycloak user, upserts the local `users` record, and then
assigns tenant and/or society roles. Either `email` or `mobile_number` is required. A temporary
password is required for the current MVP admin-created onboarding flow.

Platform superusers and tenant admins can manage users across the selected tenant. Society admins
can list and assign users only for societies where they have an active `society_admin` membership,
and they cannot assign tenant-level roles.

Suspending a user from this API suspends that user's memberships in the current tenant scope; it does
not globally disable the identity because one person can belong to multiple tenants or societies.

## Owners

Owners are tenant-owned, society-scoped accounting parties. An owner may exist without a login
account. `owners.user_id` is optional and should be set only when the owner is linked to a portal
user.

The owner-to-flat relationship is modeled separately so ownership history, co-ownership, and primary
owner rules can be managed without duplicating owner records.

## Flat Ownerships

Flat ownerships connect owners to flats with effective dates. A flat can have one current active
`primary_owner` and any number of `co_owner` records. Historical records should be closed by setting
`effective_to` and `status=inactive`, not deleted.

## Residents

Residents are people currently or historically living in a flat. They are separate from owners:
a resident can be an owner-occupier, tenant, family member, staff member, or other occupant.

`residents.owner_id` and `residents.user_id` are optional. This allows offline residents and tenant
records before portal access is created.

## Lease Agreements

Lease agreements track rental tenancy for a flat. They are separate from SaaS tenants and from
resident records: the agreement belongs to one society flat, links to the legal owner, and may
optionally link to a resident occupant.

Only one active lease agreement is allowed per flat. Terminating a lease records a move-out date and
audit reason instead of deleting history. Agreement expiry, rent, deposit, document reference, and
police verification status are stored so society admins can monitor rental compliance.

## Society Hierarchy

The society master-data hierarchy is:

```text
Tenant -> Society -> Building -> Wing -> Flat
```

`Building` is mandatory for flats. `Wing` is optional because some societies organize flats directly
under a building without wings.

Buildings are unique by name/code within a society and tenant.

Wings always belong to a building. Flats are unique by number within either a building-without-wing
or a building-and-wing scope.

## Audit Logs

Financial and administrative workflows should call `record_audit_log()` in the same transaction as
the business change.

Platform-level actions may use `tenant_id=None`. Tenant-owned actions should always include
`tenant_id`.

## Platform Tenant APIs

Platform superuser routes:

```text
GET /api/v1/platform/tenants
POST /api/v1/platform/tenants
PATCH /api/v1/platform/tenants/{tenant_id}
POST /api/v1/platform/tenants/{tenant_id}/suspend
POST /api/v1/platform/tenants/{tenant_id}/activate
```

Both require a valid bearer token for a local user with `is_platform_superuser=true`.

## Society APIs

Tenant admin routes:

```text
GET /api/v1/societies
POST /api/v1/societies
PATCH /api/v1/societies/{society_id}
POST /api/v1/societies/{society_id}/suspend
POST /api/v1/societies/{society_id}/activate
```

These routes require a valid bearer token and `X-Tenant-Id`. Access is allowed for platform
superusers or users with an active `tenant_admin` membership for that tenant.

`receivable_account_id` is optional during initial setup, but must be configured with an active
society `asset` account before invoice creation. Invoice journal posting debits this account.
`payable_account_id` is optional during initial setup, but must be configured with an active society
`liability` account before vendor-bill expense creation. Expense journal posting credits this
account for unpaid vendor bills.

## Building APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/buildings
POST /api/v1/societies/{society_id}/buildings
PATCH /api/v1/societies/{society_id}/buildings/{building_id}
POST /api/v1/societies/{society_id}/buildings/{building_id}/suspend
POST /api/v1/societies/{society_id}/buildings/{building_id}/activate
```

These routes require a valid bearer token and `X-Tenant-Id`. Access is allowed for platform
superusers, tenant admins, or active `society_admin` members of the requested society.

## Wing APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/buildings/{building_id}/wings
POST /api/v1/societies/{society_id}/buildings/{building_id}/wings
PATCH /api/v1/societies/{society_id}/buildings/{building_id}/wings/{wing_id}
POST /api/v1/societies/{society_id}/buildings/{building_id}/wings/{wing_id}/suspend
POST /api/v1/societies/{society_id}/buildings/{building_id}/wings/{wing_id}/activate
```

These routes require a valid bearer token and `X-Tenant-Id`. Access follows the same rules as
building APIs. Wings are always scoped to a building.

## Chart Of Accounts APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/chart-of-accounts
POST /api/v1/societies/{society_id}/chart-of-accounts
POST /api/v1/societies/{society_id}/chart-of-accounts/import/preview
POST /api/v1/societies/{society_id}/chart-of-accounts/import/confirm
PATCH /api/v1/societies/{society_id}/chart-of-accounts/{account_id}
POST /api/v1/societies/{society_id}/chart-of-accounts/{account_id}/inactivate
POST /api/v1/societies/{society_id}/chart-of-accounts/{account_id}/activate
```

Chart of accounts is a society-level accounting master. Accounts are unique by code and name within
a society. Supported account types are `asset`, `liability`, `equity`, `income`, and `expense`.
Accounts can optionally reference a parent account through `parent_account_id`.

Charge types must map to an active `income` account. Bank, cash, advance, receivable, payable, and
expense accounts should be created here too, but charge-type revenue selection is intentionally
limited to income accounts.

Bank and cash accounts are normal chart-of-accounts entries with `account_type=asset` and
`normal_balance=debit`. Societies can create multiple bank and cash accounts, such as separate bank
accounts, petty cash, and cash in hand.

Parent and child accounts must have the same account type and normal balance. The API rejects
self-parenting and circular parent changes.

Bulk chart-of-accounts import starts with a validation-only preview endpoint and then a confirm
endpoint. Confirm rejects the whole batch if any row is invalid. Each row should provide:

```json
{
  "account_code": "4000",
  "parent_account_code": null,
  "account_name": "Maintenance Income",
  "account_type": "income",
  "normal_balance": "credit",
  "description": "Monthly maintenance billing"
}
```

`account_type` must be one of `asset`, `liability`, `equity`, `income`, or `expense`.
`normal_balance` must be `debit` or `credit`. If `parent_account_code` is provided, the parent must
already exist in the society or appear earlier in the same CSV file.

## Charge Type APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/charge-types
POST /api/v1/societies/{society_id}/charge-types
PATCH /api/v1/societies/{society_id}/charge-types/{charge_type_id}
POST /api/v1/societies/{society_id}/charge-types/{charge_type_id}/inactivate
POST /api/v1/societies/{society_id}/charge-types/{charge_type_id}/activate
```

Charge types are society-level billing masters used to classify invoice line items. Amounts and
calculation formulas belong to billing rules, not charge types. Each charge type must reference an
active income account from chart of accounts through `revenue_account_id`.

## Billing Rule APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/billing-rules
POST /api/v1/societies/{society_id}/billing-rules
PATCH /api/v1/societies/{society_id}/billing-rules/{billing_rule_id}
POST /api/v1/societies/{society_id}/billing-rules/{billing_rule_id}/inactivate
POST /api/v1/societies/{society_id}/billing-rules/{billing_rule_id}/activate
```

Billing rules define how standard society charges should be calculated before invoice generation.
MVP calculation methods are `fixed`, `area_based`, `parking_based`, `flat_type_fixed`, and `manual`.

MVP rule scopes are `all_flats`, `building`, `wing`, and `flat_type`. `area_based` rules require
`area_basis` of `carpet_area` or `built_up_area`. `flat_type_fixed` rules must use `flat_type` scope.

Billing rules are scheduler-ready. `generation_day` defines the day of the period when bills should
be generated, `due_day` defines payment due day, `billing_period_timing` defines whether generated
bills apply to the current or next period, and `next_generation_date` is the scheduler cursor.

Late fee and interest rules are intentionally not implemented yet, but the rule model keeps
calculation method, frequency, scope, effective dates, and status explicit so those rule types can be
added later without replacing the billing foundation.

## Document Numbering APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/document-sequences/invoice
PATCH /api/v1/societies/{society_id}/document-sequences/invoice
```

Invoice numbering is society-level configuration. If no setting exists yet, the API creates a default
invoice sequence using:

```text
INV-{billing_period_yyyymm}-{sequence}
```

Supported settings:

- `prefix`
- `include_period`
- `include_financial_year`
- `separator`
- `next_sequence`
- `padding`
- `reset_policy`: `never`, `monthly`, or `financial_year`

Invoice generation uses this setting in the same transaction as invoice creation and increments
`next_sequence` after each invoice number is assigned.

## Invoice APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/invoices
POST /api/v1/societies/{society_id}/invoices
POST /api/v1/societies/{society_id}/invoices/generation/preview
POST /api/v1/societies/{society_id}/invoices/generation/confirm
GET /api/v1/societies/{society_id}/invoices/{invoice_id}
POST /api/v1/societies/{society_id}/invoices/{invoice_id}/cancel
```

Invoices store generated bills for flats. Invoice line items preserve charge-level details and point
back to charge types and billing rules where applicable.

Invoice creation posts a linked journal entry in the same transaction. The journal debits the
society receivable account and credits each charge type's configured revenue account. Invoice
creation fails if the receivable account is missing, inactive, or if any charge type lacks an active
income revenue account.

Invoice generation is a preview-first workflow. Admins provide `billing_period_start`,
`billing_period_end`, `invoice_date`, `due_date`, and one or more `billing_rule_ids`, so backdated
billing is supported. For example, on 2026-06-21 an admin may generate the April period by selecting
`2026-04-01` to `2026-04-30`.

Preview evaluates active flats and the selected active non-manual billing rules for the selected
society. It returns valid, skipped, and invalid rows without creating invoices. Confirm re-runs the
same validation and creates one issued invoice per valid flat only when there are no invalid rows.

Selected billing rule IDs must belong to active, non-manual rules in the same tenant and society.
This allows separate runs for monthly maintenance, sinking fund, one-time repair fund, or any other
configured rule set without generating every active rule by accident.

Duplicate protection blocks a selected billing rule from being billed twice for the same society,
flat, and billing period. Manual invoices can coexist in the same period because ad hoc charges such
as clubhouse booking or document fees are separate invoice events.

This manual generation workflow is separate from future scheduler automation. `generation_day`,
`due_day`, and `next_generation_date` remain available on billing rules for the later recurring job
runner.

Manual/ad hoc invoices are created with `POST /invoices`. They require a flat, invoice dates, billing
period dates, and one or more charge-type line items. If no owner is provided, the API uses the
current active primary owner for the selected flat when available.

Invoices are not hard-deleted. Wrong invoices should be cancelled with a reason. Cancellation sets
status to `cancelled`, clears `amount_due`, preserves the invoice record, and writes an audit log.
Invoices with paid amounts cannot be cancelled directly.

## Late Fee / Penalty APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/late-fees/rules
POST /api/v1/societies/{society_id}/late-fees/rules
PATCH /api/v1/societies/{society_id}/late-fees/rules/{late_fee_rule_id}
POST /api/v1/societies/{society_id}/late-fees/rules/{late_fee_rule_id}/inactivate
POST /api/v1/societies/{society_id}/late-fees/rules/{late_fee_rule_id}/activate
POST /api/v1/societies/{society_id}/late-fees/preview
POST /api/v1/societies/{society_id}/late-fees/apply
```

Late fee rules are society-level penalty configuration. MVP calculation methods are:

```text
fixed
percent_of_due
```

Rules support grace days, optional repeat interval days, optional maximum applications per invoice,
effective dates, and an active/inactive lifecycle. A rule without `repeat_interval_days` is treated
as a one-time penalty. A repeated rule is evaluated from the invoice due date plus grace days and
can catch up missed scheduled runs by returning every missing application date up to the selected
`as_of_date`, while respecting existing applications and the maximum application limit.

Penalty application is a preview-first workflow. Admins select an `as_of_date` and one or more
active late fee rules. Preview evaluates open overdue invoices and returns valid/skipped rows
without writing data. Apply re-runs validation and creates separate penalty invoices for valid rows.

Penalty invoices use the rule's charge type, post through normal invoice journal posting, debit the
society receivable account, and credit the charge type revenue account. The original overdue invoice
is not mutated. `late_fee_applications` links the original invoice, penalty invoice, rule, as-of date,
and amount for auditability and duplicate protection.

When a backdated payment is recorded against the original invoice, the payment workflow revalidates
active penalty applications for that invoice. If the original invoice was fully paid before a
penalty application's `applied_as_of_date`, that unpaid penalty invoice is auto-cancelled, its
journal entry is marked reversed, and the application is marked `cancelled`. This keeps penalties
through the actual payment date while cancelling later penalties that were only generated because
the payment was posted late. Paid penalty invoices are not silently cancelled; they require a later
adjustment or credit-note workflow.

## Scheduled Job Foundation APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/scheduled-jobs/due?as_of_date=YYYY-MM-DD
GET /api/v1/societies/{society_id}/scheduled-jobs/runs
POST /api/v1/societies/{society_id}/scheduled-jobs/run-due
```

The scheduled job foundation separates visibility from execution. The due-work endpoint shows which
billing rules and penalty rules need attention as of a selected date. Billing rules are considered
due when active non-manual rules have `next_generation_date` on or before the selected date. Penalty
rules are considered due when the late-fee preview engine finds at least one eligible overdue invoice.

`scheduled_job_runs` stores manual or scheduled automation runs for billing generation and late-fee
application. The manual run endpoint creates job-run records, executes due billing rules through the
existing invoice generation engine, executes due penalty rules through the existing late-fee engine,
and marks each run completed or failed.

Billing runs process one due period per due rule, then advance `next_generation_date` based on the
rule frequency. Penalty runs apply all currently due active penalty rules for the selected as-of
date. If a daily/weekly penalty run was missed, the late-fee engine catches up the missing penalty
application dates in the next run instead of applying only one penalty for the current date.

The Celery worker can execute scheduled work through:

```text
propelsync.scheduled_jobs.run_due_jobs
```

The task uses the local scheduled-jobs system actor configured by `SCHEDULED_JOBS_SYSTEM_ACTOR_*`,
records job runs with `run_mode=scheduled`, and continues processing other active societies if one
society fails.

## Payment APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/payments
POST /api/v1/societies/{society_id}/payments
POST /api/v1/societies/{society_id}/payments/{payment_id}/reverse
```

Payments record member collections against flats. A payment can allocate to multiple open invoices,
and invoices can receive multiple payments over time. Payment creation updates each allocated
invoice's `amount_paid`, `amount_due`, and status in the same transaction.

Payment creation posts a linked journal entry in the same transaction. The journal debits the
selected deposit account and credits the society receivable account. Payment creation fails if the
deposit account is missing/inactive or the society receivable account is not configured.

MVP payment modes are:

```text
cash
bank_transfer
cheque
upi
card
other
```

If a payment amount is greater than the allocated invoice amount, the difference is stored as
`unapplied_amount`. Payment reversal marks the payment and active allocations as reversed, restores
allocated invoice balances, marks the linked payment journal entry as `reversed`, and records the
reversal reason in the audit log. A full advance-balance ledger remains a later slice.

## Outstanding APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/outstanding?as_of_date=YYYY-MM-DD
```

Outstanding balances are calculated by the centralized outstanding service. It uses non-cancelled
invoices with positive `amount_due`, groups balances by flat, and returns society totals plus ageing
buckets: current, 1-30, 31-60, 61-90, and 90+ days.

## Vendor APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/vendors
POST /api/v1/societies/{society_id}/vendors
PATCH /api/v1/societies/{society_id}/vendors/{vendor_id}
POST /api/v1/societies/{society_id}/vendors/{vendor_id}/inactivate
POST /api/v1/societies/{society_id}/vendors/{vendor_id}/activate
```

Vendors are society-level expense/payables masters. Vendor codes are unique within a society and
are intended to become stable references for expense imports, vendor ledgers, and later payables
reports. Vendors are not deleted; inactive vendors remain available for historical expenses.

## Expense Category APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/expense-categories
POST /api/v1/societies/{society_id}/expense-categories
PATCH /api/v1/societies/{society_id}/expense-categories/{category_id}
POST /api/v1/societies/{society_id}/expense-categories/{category_id}/inactivate
POST /api/v1/societies/{society_id}/expense-categories/{category_id}/activate
```

Expense categories are society-level masters used to classify vendor bills and cash expenses.
Each category must map to an active `expense` chart-of-accounts entry so later expense posting can
debit the correct ledger account.

## Expense APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/expenses
POST /api/v1/societies/{society_id}/expenses
PATCH /api/v1/societies/{society_id}/expenses/{expense_id}
POST /api/v1/societies/{society_id}/expenses/{expense_id}/approve
POST /api/v1/societies/{society_id}/expenses/{expense_id}/cancel
```

Expenses record vendor bills and society cash/bank expenses. Each expense stores the selected
category's expense ledger account, optional vendor, optional payment account, amount, tax amount,
total amount, amount paid, amount due, approval status, and payment status. Vendor bill numbers are
unique per vendor when provided. Expenses are not deleted; wrong unpaid expenses should be cancelled
with a reason.

Expense creation posts a linked journal entry in the same transaction. Vendor bills debit the
expense account and credit the society payable account. Cash expenses debit the expense account,
credit the selected payment account, and are marked paid immediately. Editing an unpaid expense
marks the previous journal as `reversed` and posts a replacement journal. Cancelling an unpaid
expense reverses its linked journal.

## Expense Payment APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/expense-payments
POST /api/v1/societies/{society_id}/expense-payments
```

Expense payments allocate cash/bank outflows to one or more open expenses. A payment can partially
pay an expense, fully pay an expense, or leave an unapplied amount for a later vendor advance
workflow. Payment creation updates `amount_paid`, `amount_due`, and `payment_status` on allocated
expenses in the same transaction.

Expense payment creation posts a linked journal entry in the same transaction. The journal debits
the society payable account and credits the selected payment account. Creation fails if the payable
account is missing/inactive or the selected payment account is not an active asset account.

## Journal APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/journals
POST /api/v1/societies/{society_id}/journals
POST /api/v1/societies/{society_id}/journals/opening-balance
POST /api/v1/societies/{society_id}/journals/{journal_entry_id}/reverse
GET /api/v1/societies/{society_id}/accounts/{account_id}/ledger
GET /api/v1/societies/{society_id}/trial-balance?as_of_date=YYYY-MM-DD
```

Journals are the double-entry ledger foundation. Manual journal entries require at least two active
chart-of-account lines from the selected society, exactly one debit or credit amount per line, and
total debits equal to total credits. The API posts the journal and its lines in one transaction and
writes an audit log record.

Opening balance journals use `source_type=opening_balance`, require balanced debit and credit lines,
and are intended for onboarding societies that already have bank balances, cash balances, reserves,
receivables, payables, or accumulated funds before Propelsync go-live.

Posted manual and opening balance journals are not edited in place. If an opening balance was posted
wrongly during onboarding, reverse it with a reason and post a corrected opening balance. Reversal
sets the original journal status to `reversed`, preserves the audit trail, and removes it from
ledger/report calculations that exclude reversed journals.

The account ledger endpoint is a read-only accounting view over posted journal lines. It supports
optional `date_from` and `date_to` filters, excludes reversed journal entries, calculates opening
balance, running balance, total debits, total credits, and closing balance using the account's normal
balance.

The trial balance endpoint is a read-only financial report over posted journal lines as of a selected
date. It excludes reversed journal entries, summarizes each chart-of-accounts entry into a debit or
credit closing balance, and returns total debits, total credits, and whether the society books are
balanced.

## Income Vs Expense Report APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/reports/income-expense?period_start=YYYY-MM-DD&period_end=YYYY-MM-DD
GET /api/v1/societies/{society_id}/reports/income-expense/export?period_start=YYYY-MM-DD&period_end=YYYY-MM-DD&export_format=xlsx
GET /api/v1/societies/{society_id}/reports/income-expense/export?period_start=YYYY-MM-DD&period_end=YYYY-MM-DD&export_format=pdf
```

The report is generated from posted journal lines only and excludes reversed entries. Income accounts
use credit minus debit movement for the selected period. Expense accounts use debit minus credit
movement. The API returns total income, total expense, and net surplus/deficit.

Exports are generated by the backend. XLSX and PDF are supported for the first financial report
slice, with report title, period, account rows, and totals.

## Balance Sheet Report APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/reports/balance-sheet?as_of_date=YYYY-MM-DD
GET /api/v1/societies/{society_id}/reports/balance-sheet/export?as_of_date=YYYY-MM-DD&export_format=xlsx
GET /api/v1/societies/{society_id}/reports/balance-sheet/export?as_of_date=YYYY-MM-DD&export_format=pdf
```

The balance sheet is generated from posted journal lines as of the selected date and excludes
reversed entries. Asset accounts use debit minus credit balances. Liability and equity accounts use
credit minus debit balances. Since formal year-end closing entries are not implemented yet, the
report includes a synthetic equity row for current surplus/deficit derived from cumulative income
and expense account movement.

## Operational Report APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/reports/billing?period_start=YYYY-MM-DD&period_end=YYYY-MM-DD
GET /api/v1/societies/{society_id}/reports/billing/export?period_start=YYYY-MM-DD&period_end=YYYY-MM-DD&export_format=xlsx
GET /api/v1/societies/{society_id}/reports/collection?period_start=YYYY-MM-DD&period_end=YYYY-MM-DD
GET /api/v1/societies/{society_id}/reports/collection/export?period_start=YYYY-MM-DD&period_end=YYYY-MM-DD&export_format=pdf
GET /api/v1/societies/{society_id}/reports/expenses?period_start=YYYY-MM-DD&period_end=YYYY-MM-DD
GET /api/v1/societies/{society_id}/reports/expenses/export?period_start=YYYY-MM-DD&period_end=YYYY-MM-DD&export_format=xlsx
GET /api/v1/societies/{society_id}/reports/defaulters?as_of_date=YYYY-MM-DD
GET /api/v1/societies/{society_id}/reports/defaulters/export?as_of_date=YYYY-MM-DD&export_format=pdf
GET /api/v1/societies/{society_id}/reports/outstanding?as_of_date=YYYY-MM-DD
GET /api/v1/societies/{society_id}/reports/outstanding/export?as_of_date=YYYY-MM-DD&export_format=xlsx
```

Operational reports are backend-generated and support XLSX/PDF exports. Billing excludes cancelled
invoices. Collection excludes reversed payments. Expense excludes cancelled expenses. Defaulter and
outstanding reports use the centralized outstanding calculation service so ageing and overdue totals
stay consistent across dashboard/report surfaces.

## Account Transfer APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/account-transfers
POST /api/v1/societies/{society_id}/account-transfers
```

Account transfers move money between active `asset` accounts such as cash and bank accounts. Source
and destination accounts must be different and belong to the selected society. Posting a transfer
creates an `account_transfers` record and a linked journal entry in the same transaction: debit the
destination account and credit the source account.

## Flat Type APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/flat-types
POST /api/v1/societies/{society_id}/flat-types
PATCH /api/v1/societies/{society_id}/flat-types/{flat_type_id}
POST /api/v1/societies/{society_id}/flat-types/{flat_type_id}/inactivate
POST /api/v1/societies/{society_id}/flat-types/{flat_type_id}/activate
```

Flat types are society-level masters for unit category, area, and default parking values.

## Building Floor APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/buildings/{building_id}/floors
POST /api/v1/societies/{society_id}/buildings/{building_id}/floors
PATCH /api/v1/societies/{society_id}/buildings/{building_id}/floors/{floor_id}
POST /api/v1/societies/{society_id}/buildings/{building_id}/floors/{floor_id}/inactivate
POST /api/v1/societies/{society_id}/buildings/{building_id}/floors/{floor_id}/activate
```

Building floors are building-level masters used to prevent invalid floor entry during flat setup.

## Flat APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/buildings/{building_id}/flats
POST /api/v1/societies/{society_id}/buildings/{building_id}/flats
POST /api/v1/societies/{society_id}/buildings/{building_id}/flats/import/preview
POST /api/v1/societies/{society_id}/buildings/{building_id}/flats/import/confirm
PATCH /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}
POST /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/inactivate
POST /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/activate
```

These routes require a valid bearer token and `X-Tenant-Id`. Access follows the same rules as
building APIs. `building_id` is required by the route. `wing_id` is optional in the payload and must
belong to the same building when provided. `floor_id` and `flat_type_id` are optional during the
transition period, but new setup should use them. When a flat type is selected, blank area and parking
inputs inherit the flat type defaults.

Bulk flat import starts with a validation-only preview endpoint. It accepts up to 1000 rows and does
not create records. Each row should provide:

```json
{
  "flat_number": "101",
  "flat_type_code": "2BHK",
  "floor_label": "First Floor",
  "wing_code": "A"
}
```

`wing_code` is optional. The preview validates required fields, active flat type, active building
floor, optional active wing, existing flat duplicates, and duplicate rows inside the import file.
The confirm endpoint re-runs validation, rejects the whole batch if any row is invalid, inserts all
valid rows in one transaction, derives area and parking from flat type, and writes one bulk import
audit log.

## Owner APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/owners
POST /api/v1/societies/{society_id}/owners
PATCH /api/v1/societies/{society_id}/owners/{owner_id}
POST /api/v1/societies/{society_id}/owners/{owner_id}/inactivate
POST /api/v1/societies/{society_id}/owners/{owner_id}/activate
```

These routes require a valid bearer token and `X-Tenant-Id`. Access follows the same rules as
building APIs. `user_id` is optional and should only be set when the owner has a portal user.

## Flat Ownership APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/ownerships
POST /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/ownerships
PATCH /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/ownerships/{ownership_id}
POST /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/ownerships/{ownership_id}/close
POST /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/ownerships/{ownership_id}/activate
```

These routes require a valid bearer token and `X-Tenant-Id`. Access follows the same rules as
building APIs. Closing an ownership sets `effective_to` and `status=inactive`; records are not
deleted.

## Resident APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/residents
POST /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/residents
PATCH /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/residents/{resident_id}
POST /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/residents/{resident_id}/move-out
POST /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/residents/{resident_id}/activate
```

These routes require a valid bearer token and `X-Tenant-Id`. Access follows the same rules as
building APIs. Moving out a resident sets `move_out_date` and `status=inactive`; records are not
deleted.

## Lease Agreement APIs

Society admin routes:

```text
GET /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/lease-agreements
POST /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/lease-agreements
PATCH /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/lease-agreements/{lease_agreement_id}
POST /api/v1/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/lease-agreements/{lease_agreement_id}/terminate
```

These routes require a valid bearer token and `X-Tenant-Id`. Access follows the same rules as
building APIs. Creating or updating an active lease rejects a second active lease for the same flat.
Terminating a lease sets `move_out_date` and `status=terminated`; lease records are not deleted.
