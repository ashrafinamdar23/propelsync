# Propelsync Web

The web app is a React/Vite frontend for platform administration.

## Start

```powershell
docker compose up -d web
```

Open:

```text
http://localhost:5173
```

The current admin-console slice supports:

- Keycloak login
- Cached local Keycloak session tokens for smoother browser refreshes
- Last-used tenant, society, building, flat, and workspace restoration
- Dashboard metrics in a dedicated Dashboard workspace
- Tenant list/create/edit/suspend/activate
- Tenant context switching
- Role-aware bootstrap through `/auth/my-access`
- Society list/create/edit/suspend/activate for the selected tenant, including receivable and payable account setup
- Building list/create/edit/suspend/activate for the selected society
- Building floor list/create/edit/inactivate/activate for the selected building
- Flat type list/create/edit/inactivate/activate for the selected society
- Hierarchical chart of accounts list/create/edit/inactivate/activate for the selected society
- Bank & Cash account workspace for focused asset/debit cash and bank account setup
- Bulk chart of accounts import with parent account codes, CSV template download, validation preview, and confirm import
- Charge type list/create/edit/inactivate/activate for the selected society, with revenue account selection
- Invoice numbering settings for society-level prefix, period/FY tokens, reset policy, padding, and next sequence
- Billing rule list/create/edit/inactivate/activate for fixed, area-based, parking-based, flat-type fixed, and manual MVP rule types, including generation day, due day, period timing, and next generation date
- Penalty rule list/create/edit/inactivate/activate for fixed and percent-of-due late fees with grace days, repeat interval, and max application controls
- Invoice generation workspace with billing rule selection, period dates, preview validation, rule-level duplicate blocking, confirm generation, and linked journal posting
- Apply penalties workspace with as-of date, penalty rule selection, preview validation, and confirm generation of separate penalty invoices
- Scheduled Jobs workspace for due billing/penalty detection, manual run-due execution, and job run history
- Manual invoice workspace for ad hoc flat charges such as clubhouse booking, document fees, or one-time penalties
- Invoice list/detail workspace for generated bills, invoice line items, and invoice cancellation
- Payment recording workspace with flat selection, deposit account selection, open invoice allocation, linked journal posting, payment registry, reversal action, and unapplied amount tracking
- Outstanding workspace with society totals, overdue balances, and flat-wise ageing buckets
- Vendor management workspace for society-level expense/payables masters
- Expense category management workspace linked to expense ledger accounts
- Expense registry workspace for vendor bills and society expenses with linked journal posting and approve/cancel actions
- Expense payment allocation inside the Expenses workspace for partial/full vendor payments with linked journal posting
- Journal entry workspace for balanced manual double-entry postings against chart of accounts
- Opening balance workspace for onboarding societies with balanced initial ledger balances and reversal for correction
- Account transfer workspace for cash/bank movements with linked journal posting
- Account ledger workspace for account/date-filtered debit, credit, opening, running, and closing balances
- Operational reports workspace for billing, collection, expense, defaulter, and outstanding reports with Excel/PDF exports
- Trial balance workspace for society-level as-of-date debit and credit account summaries
- Income vs Expense report workspace with period selection plus backend-generated Excel and PDF exports
- Balance Sheet report workspace with as-of-date assets, liabilities, equity, current surplus, and backend-generated Excel/PDF exports
- Wing list/create/edit/suspend/activate for the selected building
- Flat list/create/edit/inactivate/activate for the selected building, with optional wing assignment
- Bulk flat import for the selected building with CSV template download, validation preview, and confirm import
- Owner list/create/edit/inactivate/activate for the selected society
- Flat ownership list/create/edit/close/activate for the selected flat
- Resident list/create/edit/move-out/activate for the selected flat, with optional owner link
- Responsive app shell with top bar, collapsible grouped sidebar, metrics, and data tables

The app uses the `propelsync-web` Keycloak client and calls the FastAPI backend at
`http://localhost:8000/api/v1`.
