# AGENTS.md

## Project Name

Propelsync

## Product Goal

Build a SaaS ERP for housing society accounting.

This is not a MyGate clone.

The MVP must focus only on society finance operations:

- Flat and owner management
- Maintenance billing
- Payment tracking
- Expense tracking
- Defaulter reports
- Financial dashboard
- PDF, Excel, and CSV reports

The product should help treasurers, secretaries, managing committee members, accountants, and auditors replace manual Excel-based accounting.

---

## Core Principle

Keep the MVP simple, practical, enterprise-ready, and accounting-first.

The MVP should be functionally focused, but the architecture must be robust, extensible, configurable, secure, auditable, and maintainable from day one.

Never sacrifice accounting correctness for UI improvements.

---

## Target Users

- Housing society treasurer
- Society secretary
- Managing committee members
- Accountant
- Auditor

---

## Chosen Technology Stack

The approved backend stack is:

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic
- Pytest

Supporting technologies may include:

- JWT authentication
- Redis for caching and queues when needed
- Celery or RQ for background jobs when needed
- OpenPyXL or similar library for Excel exports
- WeasyPrint, ReportLab, or similar library for PDF exports
- Docker and Docker Compose for deployment

Frontend development must not begin until backend APIs are stable.

---

## SaaS Requirements

The system must be multi-tenant from day one.

Every business table must include:

```sql
tenant_id UUID NOT NULL
```

Possible exceptions are global/system tables such as tenant records, migration metadata, and platform-level configuration.

All tenant-owned data must be isolated at the database, service, and API layers.

Cross-tenant data access is a critical security bug.

---

## Enterprise Readiness Requirements

Propelsync must be enterprise-ready from day one.

The MVP scope should remain focused, but the foundation must support long-term SaaS growth.

Required principles:

- Multi-tenant architecture from day one
- Strong tenant isolation
- Configurable society-level settings
- Role-based access control
- Audit logging for financial and administrative actions
- Decimal-safe money handling
- API-first backend design
- Centralized accounting calculations
- Centralized reporting calculations
- Clear status lifecycle for financial records
- Migration-safe database evolution
- Validation and error handling at all boundaries
- Test coverage for business-critical workflows
- Structured logging and health checks
- Environment-based configuration
- Extensible billing and reporting design

---

## Accounting Correctness Rules

Accounting correctness is the highest priority.

Rules:

- Use Decimal / Numeric types for money.
- Never use floating point types for financial amounts.
- Posted invoices, payments, allocations, and expenses must not be hard-deleted.
- Financial corrections should use cancellation, reversal, or adjustment flows.
- Reports must not calculate balances independently.
- All reports must use the centralized accounting/outstanding calculation services.
- All important financial actions must be auditable.

---

## Configuration First

Avoid hardcoding society-specific behavior.

The following should be configurable where applicable:

- Chart of accounts
- Billing cycle
- Due date rules
- Late fee rules
- Invoice numbering format
- Receipt numbering format
- Charge types
- Billing rules
- Financial year settings
- Roles and permissions
- Report formats where practical
- Tax/GST settings if enabled later

---

## Explicit Non-Goals For MVP

Do not build:

- Mobile applications
- Visitor management
- Security guard workflows
- Delivery tracking
- Facility booking
- Chat systems
- Social features
- Marketplace
- WhatsApp integration
- Payment gateway integration
- AI agents

These are future roadmap items.

---

## AI Agent Working Rules

The project must move step by step.

The AI agent must not start development without discussion and approval.

Only one feature, model, service, API, workflow, or setup task should be implemented at a time.

Before implementing any feature:

1. Review existing schema.
2. Review accounting impact.
3. Review tenant isolation impact.
4. Review audit logging requirements.
5. Define tests.
6. Get user approval.
7. Implement only the approved item.
8. Update documentation.

Never bypass these steps.

---

## Approval Rule

The AI agent must not implement the next item in the sequence until the current item has been discussed, reviewed, and approved by the user.

No frontend work should begin before backend foundation, accounting engine, APIs, and reports are stable.

---

## One-Step-At-A-Time Feature Onboarding Sequence

For every feature or module, follow this sequence:

1. Define the business requirement.
2. Define entities and relationships.
3. Define database schema.
4. Define accounting impact.
5. Define tenant isolation rules.
6. Define audit logging requirements.
7. Define validations and constraints.
8. Define service behavior.
9. Define API contract.
10. Define test cases.
11. Implement database migration.
12. Implement models.
13. Implement service logic.
14. Implement APIs.
15. Implement tests.
16. Update documentation.
17. Review with user before moving to the next feature.

---

## Development Progress Status Legend

Use the following status values:

- Not Started
- Discussing
- Approved
- In Progress
- Implemented
- Tested
- Completed

Do not mark an item as Completed until it has been implemented, tested where applicable, and reviewed.

---

## Recommended Build Sequence

### Foundation

| # | Item | Status |
|---|------|--------|
| 1 | Finalize AGENTS.md project instructions | Completed |
| 2 | Local PostgreSQL Docker setup | Completed |
| 3 | Local FastAPI Docker setup | Completed |
| 4 | Define backend project architecture | Completed |
| 5 | Define configuration and environment strategy | Completed |
| 6 | Define database connection strategy | Completed |
| 7 | Define Alembic migration strategy | Completed |
| 8 | Define base SQLAlchemy model conventions | Completed |
| 9 | Define tenant model | Completed |
| 10 | Local Keycloak Docker setup | Completed |
| 11 | Define user model | Completed |
| 12 | Define authentication foundation | Tested |
| 13 | Define tenant isolation pattern | Tested |
| 14 | Define audit log foundation | Completed |
| 15 | Define platform tenant management API | Tested |
| 16 | Superuser tenant creation frontend | Tested |

### Society Master Data

| # | Item | Status |
|---|------|--------|
| 17 | Define society model | Completed |
| 18 | Define building model | Completed |
| 19 | Define wing model | Completed |
| 20 | Define flat model | Completed |
| 21 | Define tenant and society membership models | Completed |
| 22 | Define owner model | Completed |
| 23 | Define flat ownership model | Completed |
| 24 | Define resident model | Completed |

### Billing Foundation

| # | Item | Status |
|---|------|--------|
| 18 | Define chart of accounts model | Tested |
| 19 | Define chart of accounts hierarchy | Tested |
| 20 | Define bulk chart of accounts import | Tested |
| 21 | Define charge type model | Tested |
| 22 | Define billing rule model | Tested |
| 23 | Define billing rule schedule fields | Tested |
| 24 | Define invoice model | Tested |
| 25 | Define invoice line item model | Tested |
| 26 | Define invoice numbering rules | Tested |
| 27 | Define invoice status lifecycle | Tested |
| 28 | Define late fee / penalty rule model | Tested |

### Accounting Engine

| # | Item | Status |
|---|------|--------|
| 24 | Define monthly invoice generation service | Tested |
| 25 | Define duplicate invoice prevention | Tested |
| 26 | Define bulk invoice generation | Tested |
| 27 | Define manual charges | Tested |
| 28 | Define invoice journal posting | Tested |
| 29 | Define late fee / penalty preview and application workflow | Tested |
| 30 | Define backdated payment penalty revalidation | Tested |
| 31 | Define scheduled billing / penalty job foundation | Tested |
| 32 | Define manual run due jobs workflow | Tested |
| 33 | Define Redis/Celery worker foundation | Tested |
| 34 | Define scheduled jobs system actor and worker execution | Tested |
| 35 | Define opening balance journal reversal workflow | Tested |
| 36 | Define invoice regeneration rules | Not Started |

### Payments

| # | Item | Status |
|---|------|--------|
| 29 | Define payment model | Tested |
| 30 | Define payment allocation model | Tested |
| 31 | Define payment allocation engine | Tested |
| 32 | Define partial payment handling | Tested |
| 33 | Define advance payment handling | Implemented |
| 34 | Define payment reversal rules | Tested |
| 35 | Define member payment journal posting | Tested |

### Outstanding Engine

| # | Item | Status |
|---|------|--------|
| 35 | Define invoice balance calculation | Tested |
| 36 | Define owner/flat balance calculation | Tested |
| 37 | Define ageing bucket calculation | Tested |
| 38 | Define overdue calculation | Tested |
| 39 | Define centralized outstanding service | Tested |

### Expenses

| # | Item | Status |
|---|------|--------|
| 40 | Define vendor model | Tested |
| 41 | Define expense category model | Tested |
| 42 | Define expense model | Tested |
| 43 | Define expense approval/status lifecycle | Tested |
| 44 | Define expense payment allocation | Tested |
| 45 | Define expense journal posting | Tested |
| 46 | Define expense payment journal posting | Tested |

### Banking and Ledger

| # | Item | Status |
|---|------|--------|
| 45 | Define journal entry model | Tested |
| 46 | Define journal line model | Tested |
| 47 | Define bank/cash account transfer model | Tested |
| 48 | Define inter-account transfer workflow | Tested |
| 49 | Define account ledger view/API/UI | Tested |
| 50 | Define trial balance API/UI | Tested |
| 51 | Define income vs expense report API/UI/export | Tested |
| 52 | Define bank and cash account setup UI | Tested |
| 53 | Define opening balance journal workflow | Tested |
| 54 | Define balance sheet report API/UI/export | Tested |

### APIs

| # | Item | Status |
|---|------|--------|
| 48 | Define auth APIs | Completed |
| 49 | Define society APIs | Completed |
| 50 | Define building APIs | Completed |
| 51 | Define wing APIs | Completed |
| 52 | Define flat APIs | Completed |
| 53 | Define bulk flat import preview API | Tested |
| 54 | Define bulk flat import confirm API | Tested |
| 55 | Define owner APIs | Completed |
| 56 | Define flat ownership APIs | Completed |
| 57 | Define resident APIs | Completed |
| 58 | Define chart of accounts APIs | Tested |
| 59 | Define chart of accounts hierarchy APIs | Tested |
| 60 | Define bulk chart of accounts import APIs | Tested |
| 61 | Define charge type APIs | Tested |
| 62 | Define billing rule APIs | Tested |
| 63 | Define invoice APIs | Tested |
| 64 | Define invoice generation APIs | Tested |
| 65 | Define manual invoice APIs | Tested |
| 66 | Define invoice cancellation APIs | Tested |
| 67 | Define document numbering APIs | Tested |
| 68 | Define payment APIs | Tested |
| 69 | Define outstanding APIs | Tested |
| 70 | Define vendor APIs | Tested |
| 71 | Define expense category APIs | Tested |
| 72 | Define expense APIs | Tested |
| 73 | Define expense payment APIs | Tested |
| 74 | Define journal APIs | Tested |
| 75 | Define account transfer APIs | Tested |
| 76 | Define invoice journal posting APIs | Tested |
| 77 | Define account ledger APIs | Tested |
| 78 | Define trial balance APIs | Tested |
| 79 | Define income vs expense report APIs | Tested |
| 80 | Define opening balance journal APIs | Tested |
| 81 | Define balance sheet report APIs | Tested |
| 82 | Define late fee / penalty APIs | Tested |
| 83 | Define scheduled job due-work APIs | Tested |
| 84 | Define manual run due jobs API | Tested |
| 85 | Define dashboard APIs | Not Started |
| 86 | Define reporting APIs | Tested |

### Reports

| # | Item | Status |
|---|------|--------|
| 54 | Define billing report | Tested |
| 55 | Define collection report | Tested |
| 56 | Define defaulter report | Tested |
| 57 | Define outstanding report | Tested |
| 58 | Define income vs expense report | Tested |
| 59 | Define expense report | Tested |
| 60 | Define flat ledger | Not Started |
| 61 | Define owner ledger | Not Started |
| 62 | Define Excel export | Tested |
| 63 | Define PDF export | Tested |
| 64 | Define CSV export | Not Started |

### Frontend

| # | Item | Status |
|---|------|--------|
| 65 | Login | Not Started |
| 66 | Admin console shell | Completed |
| 67 | Dashboard workspace | Completed |
| 68 | Tenant management screen | Completed |
| 69 | Society management screen | Completed |
| 70 | Buildings | Completed |
| 71 | Role-aware access bootstrap | Completed |
| 72 | Building floors | Completed |
| 73 | Flat types | Completed |
| 74 | Wings | Completed |
| 75 | Flats | Completed |
| 76 | Bulk flat import UI | Tested |
| 77 | Owners | Completed |
| 78 | Flat ownerships | Completed |
| 79 | Residents | Completed |
| 80 | Chart of accounts | Tested |
| 81 | Chart of accounts hierarchy UI | Tested |
| 82 | Bulk chart of accounts import UI | Tested |
| 83 | Charge types | Tested |
| 84 | Billing rules | Tested |
| 85 | Late fee / penalty rules | Tested |
| 86 | Late fee / penalty application | Tested |
| 87 | Scheduled Jobs | Tested |
| 88 | Invoices | Tested |
| 89 | Invoice generation | Tested |
| 90 | Invoice numbering settings | Tested |
| 91 | Manual invoices | Tested |
| 92 | Payments | Tested |
| 93 | Outstanding | Tested |
| 94 | Vendors | Tested |
| 95 | Expense Categories | Tested |
| 96 | Expenses | Tested |
| 97 | Expense Payments | Tested |
| 98 | Journal Entries | Tested |
| 99 | Account Transfers | Tested |
| 100 | Account Ledger | Tested |
| 101 | Trial Balance | Tested |
| 102 | Income vs Expense Report | Tested |
| 103 | Bank & Cash Accounts | Tested |
| 104 | Opening Balances | Tested |
| 105 | Balance Sheet Report | Tested |
| 106 | Reports | Tested |
| 107 | Settings | Not Started |

### Production Readiness

| # | Item | Status |
|---|------|--------|
| 76 | RBAC hardening | Not Started |
| 77 | Rate limiting | Not Started |
| 78 | Structured logging | Not Started |
| 79 | Health checks | Not Started |
| 80 | Dockerfile | Not Started |
| 81 | Docker Compose | Not Started |
| 82 | Environment templates | Not Started |
| 83 | Backup script | Not Started |
| 84 | Restore script | Not Started |
| 85 | Deployment documentation | Not Started |

---

## Phase 1 - Domain Model Design

Create detailed entity definitions.

Entities:

- Tenant
- User
- Society
- Wing
- Flat
- Owner
- Resident
- ChargeType
- ChartOfAccount
- BillingRule
- Invoice
- InvoiceLineItem
- Payment
- PaymentAllocation
- Vendor
- ExpenseCategory
- Expense
- AuditLog

Deliverables:

- Entity relationship diagram
- Database schema
- SQLAlchemy models
- Alembic migration

No frontend work should begin before this phase is complete.

---

## Phase 2 - Accounting Engine

Build accounting workflows.

Required functionality:

- Invoice generation
- Payment allocation
- Outstanding calculation

Invoice generation must support:

- Fixed amount
- Area based charges
- Parking based charges
- Manual charges
- Invoice regeneration prevention
- Duplicate protection
- Bulk generation

Payment allocation rules:

- One payment may pay multiple invoices.
- One invoice may have multiple payments.
- Partial payment must be supported.
- Excess payment becomes advance balance.

Outstanding calculation service must calculate:

- Invoice balance
- Customer balance
- Ageing buckets
- Overdue status

No report should calculate balances independently.

All reports must use the same centralized calculation service.

---

## Phase 3 - API Development

Create REST APIs.

Priority:

- Authentication
- Society management
- Flat management
- Billing rules
- Invoice management
- Payment management
- Expense management
- Dashboard APIs
- Reporting APIs

Requirements:

- OpenAPI documentation
- Validation
- Error handling
- Tenant isolation

---

## Phase 4 - Reporting Engine

Create reusable reporting framework.

Report categories:

- Operational reports
- Billing report
- Collection report
- Defaulter report
- Financial reports
- Income vs expense
- Vendor expense summary
- Outstanding report
- Resident reports
- Flat ledger
- Owner ledger

Exports:

- Excel
- PDF
- CSV

Reports must be generated from the backend.

---

## Phase 5 - Frontend

Only start after APIs are stable.

Page order:

1. Login
2. Dashboard
3. Flats
4. Owners
5. Billing rules
6. Invoice generation
7. Invoices
8. Payments
9. Expenses
10. Reports
11. Settings

---

## Phase 6 - Security

Implement:

- RBAC
- JWT validation
- Audit logging
- Input validation
- Rate limiting

Roles:

- Super Admin
- Society Admin
- Treasurer
- Accountant
- Auditor
- Read Only Resident

---

## Phase 7 - Production Readiness

Create:

- Dockerfiles
- Docker Compose
- Environment templates
- Backup scripts
- Restore scripts

Requirements:

- One-command deployment
- Automated database migration
- Health checks
- Structured logging

---

## Testing Strategy

Minimum unit test coverage:

- Billing engine
- Payment allocation
- Outstanding calculations
- Ageing calculations

Target:

- 80%+ coverage on business logic

Integration tests must validate:

- Invoice creation
- Payment processing
- Expense creation
- Report generation
- Tenant isolation

---

## Coding Priorities

Priority order:

1. Data correctness
2. Accounting correctness
3. Report accuracy
4. Security
5. Extensibility
6. Performance
7. UI polish

---

## Definition of MVP Completion

The MVP is complete when a real housing society can:

- Configure maintenance rules
- Generate monthly bills
- Record collections
- Track outstanding dues
- Record expenses
- Generate AGM reports
- Export accounting reports

without using Excel.
