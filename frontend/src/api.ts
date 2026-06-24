export type Tenant = {
  id: string;
  name: string;
  slug: string;
  status: string;
  subscription_plan: string;
  billing_email: string | null;
  phone: string | null;
  timezone: string;
  locale: string;
  currency: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type TenantCreatePayload = {
  name: string;
  slug: string;
  subscription_plan: string;
  billing_email?: string | null;
  phone?: string | null;
  timezone: string;
  locale: string;
  currency: string;
};

export type TenantUpdatePayload = TenantCreatePayload & {
  metadata?: Record<string, unknown>;
};

export type CurrentUser = {
  id: string;
  email: string | null;
  mobile_number: string | null;
  full_name: string;
  status: string;
  is_platform_superuser: boolean;
};

export type AccessTenant = {
  id: string;
  name: string;
  slug: string;
  status: string;
  roles: string[];
};

export type AccessSociety = {
  id: string;
  tenant_id: string;
  name: string;
  status: string;
  roles: string[];
};

export type MyAccess = {
  is_platform_superuser: boolean;
  tenants: AccessTenant[];
  societies: AccessSociety[];
};

export type ManagedUserMembership = {
  id: string;
  role: string;
  status: string;
};

export type ManagedUserSocietyMembership = ManagedUserMembership & {
  society_id: string;
  society_name: string;
};

export type ManagedUser = {
  id: string;
  keycloak_subject: string;
  email: string | null;
  mobile_number: string | null;
  full_name: string;
  status: string;
  is_platform_superuser: boolean;
  tenant_memberships: ManagedUserMembership[];
  society_memberships: ManagedUserSocietyMembership[];
  created_at: string;
  updated_at: string;
};

export type ManagedUserCreatePayload = {
  full_name: string;
  email?: string | null;
  mobile_number?: string | null;
  temporary_password: string;
  tenant_roles: string[];
  society_roles: Array<{
    society_id: string;
    role: string;
  }>;
};

export type Society = {
  id: string;
  tenant_id: string;
  name: string;
  registration_number: string | null;
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  country: string;
  timezone: string;
  locale: string;
  currency: string;
  financial_year_start_month: number;
  receivable_account_id: string | null;
  payable_account_id: string | null;
  member_advance_account_id: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type SocietyPayload = {
  name: string;
  registration_number?: string | null;
  address_line1?: string | null;
  address_line2?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  country: string;
  timezone: string;
  locale: string;
  currency: string;
  financial_year_start_month: number;
  receivable_account_id?: string | null;
  payable_account_id?: string | null;
  member_advance_account_id?: string | null;
};

export type Building = {
  id: string;
  tenant_id: string;
  society_id: string;
  name: string;
  code: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type BuildingPayload = {
  name: string;
  code?: string | null;
};

export type Wing = {
  id: string;
  tenant_id: string;
  society_id: string;
  building_id: string;
  name: string;
  code: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type WingPayload = {
  name: string;
  code?: string | null;
};

export type Flat = {
  id: string;
  tenant_id: string;
  society_id: string;
  building_id: string;
  wing_id: string | null;
  floor_id: string | null;
  flat_type_id: string | null;
  flat_number: string;
  floor_number: number | null;
  carpet_area_sqft: string | null;
  built_up_area_sqft: string | null;
  parking_count: number | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type FlatPayload = {
  wing_id?: string | null;
  floor_id?: string | null;
  flat_type_id?: string | null;
  flat_number: string;
  floor_number?: number | null;
  carpet_area_sqft?: string | null;
  built_up_area_sqft?: string | null;
  parking_count?: number | null;
};

export type FlatImportRowInput = {
  flat_number: string | null;
  flat_type_code: string | null;
  floor_label: string | null;
  wing_code: string | null;
};

export type FlatImportResolvedReference = {
  id: string | null;
  label: string | null;
};

export type FlatImportPreviewRow = {
  row_number: number;
  input: FlatImportRowInput;
  status: "valid" | "invalid";
  errors: string[];
  resolved: {
    flat_type: FlatImportResolvedReference | null;
    floor: FlatImportResolvedReference | null;
    wing: FlatImportResolvedReference | null;
  };
};

export type FlatImportPreviewResponse = {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  rows: FlatImportPreviewRow[];
};

export type FlatImportConfirmResponse = {
  imported_count: number;
  flat_ids: string[];
};

export type FlatType = {
  id: string;
  tenant_id: string;
  society_id: string;
  name: string;
  code: string | null;
  unit_category: string;
  bedroom_count: number | null;
  bathroom_count: number | null;
  carpet_area_sqft: string | null;
  built_up_area_sqft: string | null;
  default_parking_count: number;
  status: string;
  created_at: string;
  updated_at: string;
};

export type FlatTypePayload = {
  name: string;
  code?: string | null;
  unit_category: string;
  bedroom_count?: number | null;
  bathroom_count?: number | null;
  carpet_area_sqft?: string | null;
  built_up_area_sqft?: string | null;
  default_parking_count: number;
};

export type ChargeType = {
  id: string;
  tenant_id: string;
  society_id: string;
  name: string;
  code: string | null;
  description: string | null;
  revenue_account_id: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ChargeTypePayload = {
  name: string;
  code?: string | null;
  description?: string | null;
  revenue_account_id: string;
};

export type BillingRule = {
  id: string;
  tenant_id: string;
  society_id: string;
  charge_type_id: string;
  name: string;
  calculation_method: string;
  amount: string | null;
  area_basis: string | null;
  frequency: string;
  generation_day: number;
  due_day: number;
  billing_period_timing: string;
  next_generation_date: string | null;
  scope_type: string;
  building_id: string | null;
  wing_id: string | null;
  flat_type_id: string | null;
  effective_from: string;
  effective_to: string | null;
  description: string | null;
  late_fee_rule_ids: string[];
  status: string;
  created_at: string;
  updated_at: string;
};

export type BillingRulePayload = {
  charge_type_id: string;
  name: string;
  calculation_method: string;
  amount?: string | null;
  area_basis?: string | null;
  frequency: string;
  generation_day: number;
  due_day: number;
  billing_period_timing: string;
  next_generation_date?: string | null;
  scope_type: string;
  building_id?: string | null;
  wing_id?: string | null;
  flat_type_id?: string | null;
  effective_from: string;
  effective_to?: string | null;
  description?: string | null;
  late_fee_rule_ids?: string[];
};

export type Invoice = {
  id: string;
  tenant_id: string;
  society_id: string;
  flat_id: string;
  owner_id: string | null;
  journal_entry_id: string | null;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  billing_period_start: string;
  billing_period_end: string;
  total_amount: string;
  amount_paid: string;
  amount_due: string;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type InvoiceListFilters = {
  flat_id?: string;
  status?: string;
  invoice_date_from?: string;
  invoice_date_to?: string;
  due_date_from?: string;
  due_date_to?: string;
  page?: number;
  page_size?: number;
};

export type PaginatedResponse<T> = {
  items: T[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
};

export type InvoiceLineItem = {
  id: string;
  tenant_id: string;
  society_id: string;
  invoice_id: string;
  charge_type_id: string;
  billing_rule_id: string | null;
  line_number: number;
  description: string;
  quantity: string;
  unit_amount: string;
  line_amount: string;
  created_at: string;
  updated_at: string;
};

export type InvoiceDetail = Invoice & {
  line_items: InvoiceLineItem[];
};

export type ManualInvoiceLinePayload = {
  charge_type_id: string;
  description: string;
  quantity: string;
  unit_amount: string;
};

export type ManualInvoicePayload = {
  flat_id: string;
  owner_id?: string | null;
  invoice_date: string;
  due_date: string;
  billing_period_start: string;
  billing_period_end: string;
  notes?: string | null;
  late_fee_rule_ids?: string[];
  line_items: ManualInvoiceLinePayload[];
};

export type InvoiceBulkCancelResponse = {
  requested_count: number;
  cancelled_count: number;
  failed_count: number;
  results: {
    invoice_id: string;
    status: string;
    invoice_number: string | null;
    error: string | null;
  }[];
};

export type DocumentSequence = {
  id: string;
  tenant_id: string;
  society_id: string;
  document_type: string;
  prefix: string;
  include_period: boolean;
  include_financial_year: boolean;
  separator: string;
  next_sequence: number;
  padding: number;
  reset_policy: string;
  current_reset_key: string;
  created_at: string;
  updated_at: string;
};

export type DocumentSequencePayload = {
  prefix: string;
  include_period: boolean;
  include_financial_year: boolean;
  separator: string;
  next_sequence: number;
  padding: number;
  reset_policy: string;
};

export type InvoiceGenerationPayload = {
  billing_period_start: string;
  billing_period_end: string;
  invoice_date: string;
  due_date: string;
  billing_rule_ids: string[];
  flat_ids?: string[];
};

export type InvoiceGenerationLinePreview = {
  billing_rule_id: string;
  charge_type_id: string;
  description: string;
  quantity: string;
  unit_amount: string;
  line_amount: string;
};

export type InvoiceGenerationPreviewRow = {
  flat_id: string;
  flat_number: string;
  owner_id: string | null;
  status: "valid" | "invalid" | "skipped";
  errors: string[];
  total_amount: string;
  lines: InvoiceGenerationLinePreview[];
};

export type InvoiceGenerationPreviewResponse = {
  billing_period_start: string;
  billing_period_end: string;
  invoice_date: string;
  due_date: string;
  total_flats: number;
  valid_rows: number;
  invalid_rows: number;
  skipped_rows: number;
  invoice_count: number;
  total_amount: string;
  rows: InvoiceGenerationPreviewRow[];
};

export type InvoiceGenerationConfirmResponse = {
  generated_count: number;
  invoice_ids: string[];
};

export type LateFeeRule = {
  id: string;
  tenant_id: string;
  society_id: string;
  charge_type_id: string;
  name: string;
  calculation_method: string;
  amount: string;
  grace_days: number;
  repeat_interval_days: number | null;
  max_applications_per_invoice: number | null;
  effective_from: string;
  effective_to: string | null;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type LateFeeRulePayload = {
  charge_type_id: string;
  name: string;
  calculation_method: string;
  amount: string;
  grace_days: number;
  repeat_interval_days?: number | null;
  max_applications_per_invoice?: number | null;
  effective_from: string;
  effective_to?: string | null;
  description?: string | null;
};

export type LateFeePreviewPayload = {
  as_of_date: string;
  late_fee_rule_ids: string[];
};

export type LateFeePreviewRow = {
  original_invoice_id: string;
  original_invoice_number: string;
  flat_id: string;
  flat_number: string;
  due_date: string;
  applied_as_of_date: string;
  days_overdue: number;
  amount_due: string;
  late_fee_rule_id: string;
  late_fee_rule_name: string;
  status: "valid" | "invalid" | "skipped";
  errors: string[];
  penalty_amount: string;
};

export type LateFeePreviewResponse = {
  as_of_date: string;
  invoice_count: number;
  valid_rows: number;
  invalid_rows: number;
  skipped_rows: number;
  total_penalty_amount: string;
  rows: LateFeePreviewRow[];
};

export type LateFeeApplyResponse = {
  generated_count: number;
  invoice_ids: string[];
};

export type ScheduledBillingRuleDue = {
  billing_rule_id: string;
  billing_rule_name: string;
  charge_type_id: string;
  next_generation_date: string | null;
  frequency: string;
  generation_day: number;
  due_day: number;
  status: string;
  reason: string;
};

export type ScheduledLateFeeRuleDue = {
  late_fee_rule_id: string;
  late_fee_rule_name: string;
  charge_type_id: string;
  grace_days: number;
  eligible_invoice_count: number;
  total_penalty_amount: string;
  status: string;
  reason: string;
};

export type ScheduledDueWork = {
  tenant_id: string;
  society_id: string;
  as_of_date: string;
  billing_due_count: number;
  late_fee_due_count: number;
  billing_rules: ScheduledBillingRuleDue[];
  late_fee_rules: ScheduledLateFeeRuleDue[];
};

export type ScheduledJobRun = {
  id: string;
  tenant_id: string;
  society_id: string;
  job_type: string;
  run_mode: string;
  status: string;
  as_of_date: string;
  started_at: string | null;
  finished_at: string | null;
  summary: string | null;
  error_message: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type ScheduledRunDueJobsPayload = {
  as_of_date: string;
  include_billing: boolean;
  include_late_fees: boolean;
};

export type ScheduledRunDueJobsResponse = {
  billing_job_run: ScheduledJobRun | null;
  late_fee_job_run: ScheduledJobRun | null;
  generated_invoice_count: number;
  generated_penalty_invoice_count: number;
  billing_rule_count: number;
  late_fee_rule_count: number;
};

export type Payment = {
  id: string;
  tenant_id: string;
  society_id: string;
  flat_id: string;
  owner_id: string | null;
  deposit_account_id: string | null;
  journal_entry_id: string | null;
  payment_date: string;
  amount: string;
  unapplied_amount: string;
  payment_mode: string;
  reference_number: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type PaymentAllocation = {
  id: string;
  tenant_id: string;
  society_id: string;
  payment_id: string;
  invoice_id: string;
  allocated_amount: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type PaymentCancelledPenaltyInvoice = {
  id: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  total_amount: string;
  amount_due: string;
  status: string;
};

export type PaymentDetail = Payment & {
  allocations: PaymentAllocation[];
  auto_cancelled_penalty_invoices: PaymentCancelledPenaltyInvoice[];
};

export type PaymentRegisterRow = {
  id: string;
  tenant_id: string;
  society_id: string;
  flat_id: string;
  flat_number: string;
  building_id: string;
  building_name: string;
  wing_id: string | null;
  wing_name: string | null;
  deposit_account_id: string | null;
  journal_entry_id: string | null;
  payment_date: string;
  amount: string;
  unapplied_amount: string;
  payment_mode: string;
  reference_number: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type PaymentRegisterFilters = {
  flat_id?: string;
  flat_number?: string;
  status?: string;
  payment_mode?: string;
  payment_date_from?: string;
  payment_date_to?: string;
  page?: number;
  page_size?: number;
};

export type PaymentAllocationPayload = {
  invoice_id: string;
  allocated_amount: string;
};

export type PaymentPayload = {
  flat_id: string;
  owner_id?: string | null;
  deposit_account_id?: string | null;
  payment_date: string;
  amount: string;
  payment_mode: string;
  reference_number?: string | null;
  notes?: string | null;
  allocations: PaymentAllocationPayload[];
};

export type AgeingBuckets = {
  current: string;
  days_1_30: string;
  days_31_60: string;
  days_61_90: string;
  days_90_plus: string;
};

export type OutstandingFlatRow = {
  flat_id: string;
  flat_number: string;
  building_id: string;
  building_name: string;
  wing_id: string | null;
  wing_name: string | null;
  invoice_count: number;
  total_outstanding: string;
  overdue_amount: string;
  oldest_due_date: string | null;
  ageing: AgeingBuckets;
};

export type OutstandingSummary = {
  society_id: string;
  as_of_date: string;
  flat_count: number;
  flats_with_outstanding: number;
  invoice_count: number;
  total_outstanding: string;
  overdue_amount: string;
  ageing: AgeingBuckets;
  rows: OutstandingFlatRow[];
};

export type FlatLedgerLine = {
  line_date: string;
  source_type: string;
  source_id: string;
  reference_number: string | null;
  description: string;
  debit_amount: string;
  credit_amount: string;
  running_balance: string;
  status: string;
};

export type FlatLedger = {
  tenant_id: string;
  society_id: string;
  flat_id: string;
  flat_number: string;
  date_from: string | null;
  date_to: string | null;
  opening_balance: string;
  total_debits: string;
  total_credits: string;
  closing_balance: string;
  lines: FlatLedgerLine[];
};

export type ChartOfAccount = {
  id: string;
  tenant_id: string;
  society_id: string;
  parent_account_id: string | null;
  account_code: string;
  account_name: string;
  account_type: string;
  normal_balance: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ChartOfAccountPayload = {
  parent_account_id?: string | null;
  account_code: string;
  account_name: string;
  account_type: string;
  normal_balance: string;
  description?: string | null;
};

export type ChartOfAccountImportRowInput = {
  account_code: string | null;
  parent_account_code: string | null;
  account_name: string | null;
  account_type: string | null;
  normal_balance: string | null;
  description: string | null;
};

export type ChartOfAccountImportPreviewRow = {
  row_number: number;
  input: ChartOfAccountImportRowInput;
  status: "valid" | "invalid";
  errors: string[];
};

export type ChartOfAccountImportPreviewResponse = {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  rows: ChartOfAccountImportPreviewRow[];
};

export type ChartOfAccountImportConfirmResponse = {
  imported_count: number;
  account_ids: string[];
};

export type BuildingFloor = {
  id: string;
  tenant_id: string;
  society_id: string;
  building_id: string;
  floor_label: string;
  floor_number: number;
  status: string;
  created_at: string;
  updated_at: string;
};

export type BuildingFloorPayload = {
  floor_label: string;
  floor_number: number;
};

export type Owner = {
  id: string;
  tenant_id: string;
  society_id: string;
  user_id: string | null;
  owner_type: string;
  full_name: string;
  email: string | null;
  mobile_number: string | null;
  tax_identifier: string | null;
  billing_address: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type OwnerPayload = {
  user_id?: string | null;
  owner_type: string;
  full_name: string;
  email?: string | null;
  mobile_number?: string | null;
  tax_identifier?: string | null;
  billing_address?: string | null;
};

export type Vendor = {
  id: string;
  tenant_id: string;
  society_id: string;
  vendor_code: string;
  vendor_name: string;
  vendor_type: string;
  contact_person: string | null;
  email: string | null;
  mobile_number: string | null;
  tax_identifier: string | null;
  billing_address: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type VendorPayload = {
  vendor_code: string;
  vendor_name: string;
  vendor_type: string;
  contact_person?: string | null;
  email?: string | null;
  mobile_number?: string | null;
  tax_identifier?: string | null;
  billing_address?: string | null;
};

export type ExpenseCategory = {
  id: string;
  tenant_id: string;
  society_id: string;
  name: string;
  code: string | null;
  description: string | null;
  expense_account_id: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ExpenseCategoryPayload = {
  name: string;
  code?: string | null;
  description?: string | null;
  expense_account_id: string;
};

export type Expense = {
  id: string;
  tenant_id: string;
  society_id: string;
  vendor_id: string | null;
  expense_category_id: string;
  expense_account_id: string;
  payment_account_id: string | null;
  journal_entry_id: string | null;
  expense_type: string;
  vendor_bill_number: string | null;
  reference_number: string | null;
  expense_date: string;
  due_date: string;
  description: string;
  amount: string;
  tax_amount: string;
  total_amount: string;
  amount_paid: string;
  amount_due: string;
  status: string;
  payment_status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type ExpensePayload = {
  vendor_id?: string | null;
  expense_category_id: string;
  payment_account_id?: string | null;
  expense_type: string;
  vendor_bill_number?: string | null;
  reference_number?: string | null;
  expense_date: string;
  due_date: string;
  description: string;
  amount: string;
  tax_amount?: string;
  notes?: string | null;
};

export type ExpensePayment = {
  id: string;
  tenant_id: string;
  society_id: string;
  vendor_id: string | null;
  payment_account_id: string;
  journal_entry_id: string | null;
  payment_date: string;
  amount: string;
  unapplied_amount: string;
  payment_mode: string;
  reference_number: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type ExpensePaymentAllocationPayload = {
  expense_id: string;
  allocated_amount: string;
};

export type ExpensePaymentPayload = {
  vendor_id?: string | null;
  payment_account_id: string;
  payment_date: string;
  amount: string;
  payment_mode: string;
  reference_number?: string | null;
  notes?: string | null;
  allocations: ExpensePaymentAllocationPayload[];
};

export type JournalEntry = {
  id: string;
  tenant_id: string;
  society_id: string;
  journal_date: string;
  source_type: string;
  source_id: string | null;
  reversal_of_entry_id: string | null;
  reference_number: string | null;
  description: string;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type JournalLine = {
  id: string;
  tenant_id: string;
  society_id: string;
  journal_entry_id: string;
  account_id: string;
  line_number: number;
  description: string | null;
  debit_amount: string;
  credit_amount: string;
  created_at: string;
  updated_at: string;
};

export type JournalEntryDetail = JournalEntry & {
  lines: JournalLine[];
};

export type JournalLinePayload = {
  account_id: string;
  description?: string | null;
  debit_amount?: string;
  credit_amount?: string;
};

export type JournalEntryPayload = {
  journal_date: string;
  reference_number?: string | null;
  description: string;
  notes?: string | null;
  lines: JournalLinePayload[];
};

export type OpeningBalanceJournalPayload = {
  opening_date: string;
  reference_number?: string | null;
  notes?: string | null;
  lines: JournalLinePayload[];
};

export type AccountTransfer = {
  id: string;
  tenant_id: string;
  society_id: string;
  from_account_id: string;
  to_account_id: string;
  journal_entry_id: string | null;
  transfer_date: string;
  amount: string;
  transfer_mode: string;
  reference_number: string | null;
  description: string;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type AccountTransferPayload = {
  from_account_id: string;
  to_account_id: string;
  transfer_date: string;
  amount: string;
  transfer_mode: string;
  reference_number?: string | null;
  description: string;
  notes?: string | null;
};

export type OtherIncomeReceipt = {
  id: string;
  tenant_id: string;
  society_id: string;
  income_account_id: string;
  deposit_account_id: string;
  journal_entry_id: string | null;
  receipt_date: string;
  payer_name: string;
  payer_type: string;
  amount: string;
  receipt_mode: string;
  reference_number: string | null;
  description: string;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type OtherIncomeReceiptPayload = {
  receipt_date: string;
  payer_name: string;
  payer_type: string;
  income_account_id: string;
  deposit_account_id: string;
  amount: string;
  receipt_mode: string;
  reference_number?: string | null;
  description: string;
  notes?: string | null;
};

export type AccountLedgerLine = {
  journal_entry_id: string;
  journal_line_id: string;
  journal_date: string;
  source_type: string;
  source_id: string | null;
  reference_number: string | null;
  description: string;
  line_description: string | null;
  debit_amount: string;
  credit_amount: string;
  running_balance: string;
};

export type AccountLedger = {
  tenant_id: string;
  society_id: string;
  account_id: string;
  account_code: string;
  account_name: string;
  account_type: string;
  normal_balance: string;
  date_from: string | null;
  date_to: string | null;
  opening_balance: string;
  total_debits: string;
  total_credits: string;
  closing_balance: string;
  lines: AccountLedgerLine[];
};

export type TrialBalanceRow = {
  account_id: string;
  account_code: string;
  account_name: string;
  account_type: string;
  normal_balance: string;
  status: string;
  debit_balance: string;
  credit_balance: string;
};

export type TrialBalance = {
  tenant_id: string;
  society_id: string;
  as_of_date: string;
  total_debits: string;
  total_credits: string;
  is_balanced: boolean;
  rows: TrialBalanceRow[];
};

export type IncomeExpenseRow = {
  account_id: string;
  account_code: string;
  account_name: string;
  account_type: string;
  amount: string;
};

export type IncomeExpenseReport = {
  tenant_id: string;
  society_id: string;
  period_start: string;
  period_end: string;
  total_income: string;
  total_expense: string;
  net_surplus: string;
  income_rows: IncomeExpenseRow[];
  expense_rows: IncomeExpenseRow[];
};

export type BalanceSheetRow = {
  account_id: string | null;
  account_code: string;
  account_name: string;
  account_type: string;
  amount: string;
};

export type BalanceSheetReport = {
  tenant_id: string;
  society_id: string;
  as_of_date: string;
  total_assets: string;
  total_liabilities: string;
  total_equity: string;
  current_surplus: string;
  total_liabilities_and_equity: string;
  is_balanced: boolean;
  asset_rows: BalanceSheetRow[];
  liability_rows: BalanceSheetRow[];
  equity_rows: BalanceSheetRow[];
};

export type BillingReportRow = {
  invoice_id: string;
  invoice_number: string;
  flat_number: string;
  building_name: string;
  wing_name: string | null;
  invoice_date: string;
  due_date: string;
  billing_period_start: string;
  billing_period_end: string;
  total_amount: string;
  amount_paid: string;
  amount_due: string;
  status: string;
};

export type BillingReport = {
  society_id: string;
  period_start: string;
  period_end: string;
  invoice_count: number;
  total_billed: string;
  total_paid: string;
  total_due: string;
  rows: BillingReportRow[];
};

export type CollectionReportRow = {
  payment_id: string;
  payment_date: string;
  flat_number: string;
  building_name: string;
  wing_name: string | null;
  payment_mode: string;
  reference_number: string | null;
  amount: string;
  unapplied_amount: string;
  status: string;
};

export type CollectionReport = {
  society_id: string;
  period_start: string;
  period_end: string;
  payment_count: number;
  total_collected: string;
  total_unapplied: string;
  rows: CollectionReportRow[];
};

export type ExpenseOperationalReportRow = {
  expense_id: string;
  expense_date: string;
  due_date: string;
  category_name: string;
  vendor_name: string | null;
  expense_type: string;
  reference_number: string | null;
  vendor_bill_number: string | null;
  description: string;
  amount: string;
  tax_amount: string;
  total_amount: string;
  amount_paid: string;
  amount_due: string;
  status: string;
  payment_status: string;
};

export type ExpenseOperationalReport = {
  society_id: string;
  period_start: string;
  period_end: string;
  expense_count: number;
  total_expense: string;
  total_paid: string;
  total_due: string;
  rows: ExpenseOperationalReportRow[];
};

export type DefaulterReportRow = {
  flat_id: string;
  flat_number: string;
  building_name: string;
  wing_name: string | null;
  invoice_count: number;
  overdue_amount: string;
  oldest_due_date: string | null;
  days_overdue: number;
};

export type DefaulterReport = {
  society_id: string;
  as_of_date: string;
  defaulter_count: number;
  total_overdue: string;
  rows: DefaulterReportRow[];
};

export type FlatOwnership = {
  id: string;
  tenant_id: string;
  society_id: string;
  flat_id: string;
  owner_id: string;
  ownership_type: string;
  ownership_percentage: string | null;
  effective_from: string;
  effective_to: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type FlatOwnershipPayload = {
  owner_id: string;
  ownership_type: string;
  ownership_percentage?: string | null;
  effective_from: string;
  effective_to?: string | null;
};

export type Resident = {
  id: string;
  tenant_id: string;
  society_id: string;
  flat_id: string;
  owner_id: string | null;
  user_id: string | null;
  resident_type: string;
  full_name: string;
  email: string | null;
  mobile_number: string | null;
  move_in_date: string;
  move_out_date: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ResidentPayload = {
  owner_id?: string | null;
  user_id?: string | null;
  resident_type: string;
  full_name: string;
  email?: string | null;
  mobile_number?: string | null;
  move_in_date: string;
  move_out_date?: string | null;
};

export type LeaseAgreement = {
  id: string;
  tenant_id: string;
  society_id: string;
  building_id: string;
  flat_id: string;
  owner_id: string;
  resident_id: string | null;
  tenant_name: string;
  tenant_email: string | null;
  tenant_mobile_number: string | null;
  agreement_start_date: string;
  agreement_end_date: string;
  move_in_date: string;
  move_out_date: string | null;
  monthly_rent: string | null;
  security_deposit: string | null;
  police_verification_status: string;
  document_reference: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type LeaseAgreementPayload = {
  owner_id: string;
  resident_id?: string | null;
  tenant_name: string;
  tenant_email?: string | null;
  tenant_mobile_number?: string | null;
  agreement_start_date: string;
  agreement_end_date: string;
  move_in_date: string;
  move_out_date?: string | null;
  monthly_rent?: string | null;
  security_deposit?: string | null;
  police_verification_status: string;
  document_reference?: string | null;
  notes?: string | null;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

async function apiRequest<T>(path: string, token: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers
    }
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${response.status}`;
    throw new Error(typeof message === "string" ? message : "Request failed");
  }

  return response.json() as Promise<T>;
}

async function tenantApiRequest<T>(
  path: string,
  token: string,
  tenantId: string,
  options: RequestInit = {}
): Promise<T> {
  return apiRequest<T>(path, token, {
    ...options,
    headers: {
      "X-Tenant-Id": tenantId,
      ...options.headers
    }
  });
}

async function tenantApiBlobRequest(
  path: string,
  token: string,
  tenantId: string,
  options: RequestInit = {}
): Promise<Blob> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Tenant-Id": tenantId,
      ...options.headers
    }
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${response.status}`;
    throw new Error(typeof message === "string" ? message : "Request failed");
  }

  return response.blob();
}

export function listTenants(token: string): Promise<Tenant[]> {
  return apiRequest<Tenant[]>("/platform/tenants", token);
}

export function createTenant(token: string, payload: TenantCreatePayload): Promise<Tenant> {
  return apiRequest<Tenant>("/platform/tenants", token, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateTenant(
  token: string,
  tenantId: string,
  payload: TenantUpdatePayload
): Promise<Tenant> {
  return apiRequest<Tenant>(`/platform/tenants/${tenantId}`, token, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function suspendTenant(token: string, tenantId: string): Promise<Tenant> {
  return apiRequest<Tenant>(`/platform/tenants/${tenantId}/suspend`, token, {
    method: "POST"
  });
}

export function activateTenant(token: string, tenantId: string): Promise<Tenant> {
  return apiRequest<Tenant>(`/platform/tenants/${tenantId}/activate`, token, {
    method: "POST"
  });
}

export function getCurrentUser(token: string): Promise<CurrentUser> {
  return apiRequest<CurrentUser>("/auth/me", token);
}

export function getMyAccess(token: string): Promise<MyAccess> {
  return apiRequest<MyAccess>("/auth/my-access", token);
}

export function listManagedUsers(token: string, tenantId: string): Promise<ManagedUser[]> {
  return tenantApiRequest<ManagedUser[]>("/users", token, tenantId);
}

export function createManagedUser(
  token: string,
  tenantId: string,
  payload: ManagedUserCreatePayload
): Promise<ManagedUser> {
  return tenantApiRequest<ManagedUser>("/users", token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function suspendManagedUser(
  token: string,
  tenantId: string,
  userId: string
): Promise<ManagedUser> {
  return tenantApiRequest<ManagedUser>(`/users/${userId}/suspend`, token, tenantId, {
    method: "POST"
  });
}

export function activateManagedUser(
  token: string,
  tenantId: string,
  userId: string
): Promise<ManagedUser> {
  return tenantApiRequest<ManagedUser>(`/users/${userId}/activate`, token, tenantId, {
    method: "POST"
  });
}

export function listSocieties(token: string, tenantId: string): Promise<Society[]> {
  return tenantApiRequest<Society[]>("/societies", token, tenantId);
}

export function createSociety(
  token: string,
  tenantId: string,
  payload: SocietyPayload
): Promise<Society> {
  return tenantApiRequest<Society>("/societies", token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateSociety(
  token: string,
  tenantId: string,
  societyId: string,
  payload: SocietyPayload
): Promise<Society> {
  return tenantApiRequest<Society>(`/societies/${societyId}`, token, tenantId, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function suspendSociety(token: string, tenantId: string, societyId: string): Promise<Society> {
  return tenantApiRequest<Society>(`/societies/${societyId}/suspend`, token, tenantId, {
    method: "POST"
  });
}

export function activateSociety(token: string, tenantId: string, societyId: string): Promise<Society> {
  return tenantApiRequest<Society>(`/societies/${societyId}/activate`, token, tenantId, {
    method: "POST"
  });
}

export function listBuildings(
  token: string,
  tenantId: string,
  societyId: string
): Promise<Building[]> {
  return tenantApiRequest<Building[]>(`/societies/${societyId}/buildings`, token, tenantId);
}

export function createBuilding(
  token: string,
  tenantId: string,
  societyId: string,
  payload: BuildingPayload
): Promise<Building> {
  return tenantApiRequest<Building>(`/societies/${societyId}/buildings`, token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateBuilding(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  payload: BuildingPayload
): Promise<Building> {
  return tenantApiRequest<Building>(
    `/societies/${societyId}/buildings/${buildingId}`,
    token,
    tenantId,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    }
  );
}

export function suspendBuilding(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string
): Promise<Building> {
  return tenantApiRequest<Building>(
    `/societies/${societyId}/buildings/${buildingId}/suspend`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function activateBuilding(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string
): Promise<Building> {
  return tenantApiRequest<Building>(
    `/societies/${societyId}/buildings/${buildingId}/activate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function listWings(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string
): Promise<Wing[]> {
  return tenantApiRequest<Wing[]>(
    `/societies/${societyId}/buildings/${buildingId}/wings`,
    token,
    tenantId
  );
}

export function createWing(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  payload: WingPayload
): Promise<Wing> {
  return tenantApiRequest<Wing>(
    `/societies/${societyId}/buildings/${buildingId}/wings`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function updateWing(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  wingId: string,
  payload: WingPayload
): Promise<Wing> {
  return tenantApiRequest<Wing>(
    `/societies/${societyId}/buildings/${buildingId}/wings/${wingId}`,
    token,
    tenantId,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    }
  );
}

export function suspendWing(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  wingId: string
): Promise<Wing> {
  return tenantApiRequest<Wing>(
    `/societies/${societyId}/buildings/${buildingId}/wings/${wingId}/suspend`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function activateWing(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  wingId: string
): Promise<Wing> {
  return tenantApiRequest<Wing>(
    `/societies/${societyId}/buildings/${buildingId}/wings/${wingId}/activate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function listFlats(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string
): Promise<Flat[]> {
  return tenantApiRequest<Flat[]>(
    `/societies/${societyId}/buildings/${buildingId}/flats`,
    token,
    tenantId
  );
}

export function listFlatTypes(token: string, tenantId: string, societyId: string): Promise<FlatType[]> {
  return tenantApiRequest<FlatType[]>(`/societies/${societyId}/flat-types`, token, tenantId);
}

export function getFlatLedger(
  token: string,
  tenantId: string,
  societyId: string,
  flatId: string,
  filters: { date_from?: string; date_to?: string } = {}
): Promise<FlatLedger> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  return tenantApiRequest<FlatLedger>(
    `/societies/${societyId}/flats/${flatId}/ledger${query ? `?${query}` : ""}`,
    token,
    tenantId
  );
}

export function createFlatType(
  token: string,
  tenantId: string,
  societyId: string,
  payload: FlatTypePayload
): Promise<FlatType> {
  return tenantApiRequest<FlatType>(`/societies/${societyId}/flat-types`, token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateFlatType(
  token: string,
  tenantId: string,
  societyId: string,
  flatTypeId: string,
  payload: FlatTypePayload
): Promise<FlatType> {
  return tenantApiRequest<FlatType>(`/societies/${societyId}/flat-types/${flatTypeId}`, token, tenantId, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function inactivateFlatType(
  token: string,
  tenantId: string,
  societyId: string,
  flatTypeId: string
): Promise<FlatType> {
  return tenantApiRequest<FlatType>(
    `/societies/${societyId}/flat-types/${flatTypeId}/inactivate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function activateFlatType(
  token: string,
  tenantId: string,
  societyId: string,
  flatTypeId: string
): Promise<FlatType> {
  return tenantApiRequest<FlatType>(
    `/societies/${societyId}/flat-types/${flatTypeId}/activate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function listChartOfAccounts(
  token: string,
  tenantId: string,
  societyId: string
): Promise<ChartOfAccount[]> {
  return tenantApiRequest<ChartOfAccount[]>(
    `/societies/${societyId}/chart-of-accounts`,
    token,
    tenantId
  );
}

export function createChartOfAccount(
  token: string,
  tenantId: string,
  societyId: string,
  payload: ChartOfAccountPayload
): Promise<ChartOfAccount> {
  return tenantApiRequest<ChartOfAccount>(
    `/societies/${societyId}/chart-of-accounts`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function updateChartOfAccount(
  token: string,
  tenantId: string,
  societyId: string,
  accountId: string,
  payload: ChartOfAccountPayload
): Promise<ChartOfAccount> {
  return tenantApiRequest<ChartOfAccount>(
    `/societies/${societyId}/chart-of-accounts/${accountId}`,
    token,
    tenantId,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    }
  );
}

export function inactivateChartOfAccount(
  token: string,
  tenantId: string,
  societyId: string,
  accountId: string
): Promise<ChartOfAccount> {
  return tenantApiRequest<ChartOfAccount>(
    `/societies/${societyId}/chart-of-accounts/${accountId}/inactivate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function activateChartOfAccount(
  token: string,
  tenantId: string,
  societyId: string,
  accountId: string
): Promise<ChartOfAccount> {
  return tenantApiRequest<ChartOfAccount>(
    `/societies/${societyId}/chart-of-accounts/${accountId}/activate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function listBillingRules(
  token: string,
  tenantId: string,
  societyId: string
): Promise<BillingRule[]> {
  return tenantApiRequest<BillingRule[]>(`/societies/${societyId}/billing-rules`, token, tenantId);
}

export function createBillingRule(
  token: string,
  tenantId: string,
  societyId: string,
  payload: BillingRulePayload
): Promise<BillingRule> {
  return tenantApiRequest<BillingRule>(`/societies/${societyId}/billing-rules`, token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateBillingRule(
  token: string,
  tenantId: string,
  societyId: string,
  billingRuleId: string,
  payload: BillingRulePayload
): Promise<BillingRule> {
  return tenantApiRequest<BillingRule>(
    `/societies/${societyId}/billing-rules/${billingRuleId}`,
    token,
    tenantId,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    }
  );
}

export function inactivateBillingRule(
  token: string,
  tenantId: string,
  societyId: string,
  billingRuleId: string
): Promise<BillingRule> {
  return tenantApiRequest<BillingRule>(
    `/societies/${societyId}/billing-rules/${billingRuleId}/inactivate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function activateBillingRule(
  token: string,
  tenantId: string,
  societyId: string,
  billingRuleId: string
): Promise<BillingRule> {
  return tenantApiRequest<BillingRule>(
    `/societies/${societyId}/billing-rules/${billingRuleId}/activate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function listInvoices(
  token: string,
  tenantId: string,
  societyId: string,
  filters: InvoiceListFilters = {}
): Promise<PaginatedResponse<Invoice>> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  return tenantApiRequest<PaginatedResponse<Invoice>>(
    `/societies/${societyId}/invoices${query ? `?${query}` : ""}`,
    token,
    tenantId
  );
}

export function listPayments(
  token: string,
  tenantId: string,
  societyId: string
): Promise<Payment[]> {
  return tenantApiRequest<Payment[]>(`/societies/${societyId}/payments`, token, tenantId);
}

export function listPaymentRegister(
  token: string,
  tenantId: string,
  societyId: string,
  filters: PaymentRegisterFilters = {}
): Promise<PaginatedResponse<PaymentRegisterRow>> {
  const params = new URLSearchParams();
  if (filters.flat_id) params.set("flat_id", filters.flat_id);
  if (filters.flat_number) params.set("flat_number", filters.flat_number);
  if (filters.status) params.set("status", filters.status);
  if (filters.payment_mode) params.set("payment_mode", filters.payment_mode);
  if (filters.payment_date_from) params.set("payment_date_from", filters.payment_date_from);
  if (filters.payment_date_to) params.set("payment_date_to", filters.payment_date_to);
  if (filters.page) params.set("page", String(filters.page));
  if (filters.page_size) params.set("page_size", String(filters.page_size));
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return tenantApiRequest<PaginatedResponse<PaymentRegisterRow>>(
    `/societies/${societyId}/payments/register${suffix}`,
    token,
    tenantId
  );
}

export function exportPaymentRegister(
  token: string,
  tenantId: string,
  societyId: string,
  filters: PaymentRegisterFilters,
  exportFormat: "xlsx" | "pdf"
): Promise<Blob> {
  const params = new URLSearchParams({ export_format: exportFormat });
  if (filters.flat_id) params.set("flat_id", filters.flat_id);
  if (filters.flat_number) params.set("flat_number", filters.flat_number);
  if (filters.status) params.set("status", filters.status);
  if (filters.payment_mode) params.set("payment_mode", filters.payment_mode);
  if (filters.payment_date_from) params.set("payment_date_from", filters.payment_date_from);
  if (filters.payment_date_to) params.set("payment_date_to", filters.payment_date_to);
  return tenantApiBlobRequest(
    `/societies/${societyId}/payments/register/export?${params.toString()}`,
    token,
    tenantId
  );
}

export function createPayment(
  token: string,
  tenantId: string,
  societyId: string,
  payload: PaymentPayload
): Promise<PaymentDetail> {
  return tenantApiRequest<PaymentDetail>(`/societies/${societyId}/payments`, token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function reversePayment(
  token: string,
  tenantId: string,
  societyId: string,
  paymentId: string,
  reason: string
): Promise<PaymentDetail> {
  return tenantApiRequest<PaymentDetail>(`/societies/${societyId}/payments/${paymentId}/reverse`, token, tenantId, {
    method: "POST",
    body: JSON.stringify({ reason })
  });
}

export function getOutstandingSummary(
  token: string,
  tenantId: string,
  societyId: string,
  asOfDate: string
): Promise<OutstandingSummary> {
  const params = new URLSearchParams({ as_of_date: asOfDate });
  return tenantApiRequest<OutstandingSummary>(
    `/societies/${societyId}/outstanding?${params.toString()}`,
    token,
    tenantId
  );
}

export function createManualInvoice(
  token: string,
  tenantId: string,
  societyId: string,
  payload: ManualInvoicePayload
): Promise<Invoice> {
  return tenantApiRequest<Invoice>(`/societies/${societyId}/invoices`, token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function cancelInvoice(
  token: string,
  tenantId: string,
  societyId: string,
  invoiceId: string,
  reason: string
): Promise<Invoice> {
  return tenantApiRequest<Invoice>(
    `/societies/${societyId}/invoices/${invoiceId}/cancel`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify({ reason })
    }
  );
}

export function bulkCancelInvoices(
  token: string,
  tenantId: string,
  societyId: string,
  invoiceIds: string[],
  reason: string
): Promise<InvoiceBulkCancelResponse> {
  return tenantApiRequest<InvoiceBulkCancelResponse>(
    `/societies/${societyId}/invoices/bulk-cancel`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify({ invoice_ids: invoiceIds, reason })
    }
  );
}

export function getInvoice(
  token: string,
  tenantId: string,
  societyId: string,
  invoiceId: string
): Promise<InvoiceDetail> {
  return tenantApiRequest<InvoiceDetail>(
    `/societies/${societyId}/invoices/${invoiceId}`,
    token,
    tenantId
  );
}

export function getInvoiceSequence(
  token: string,
  tenantId: string,
  societyId: string
): Promise<DocumentSequence> {
  return tenantApiRequest<DocumentSequence>(
    `/societies/${societyId}/document-sequences/invoice`,
    token,
    tenantId
  );
}

export function updateInvoiceSequence(
  token: string,
  tenantId: string,
  societyId: string,
  payload: DocumentSequencePayload
): Promise<DocumentSequence> {
  return tenantApiRequest<DocumentSequence>(
    `/societies/${societyId}/document-sequences/invoice`,
    token,
    tenantId,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    }
  );
}

export function previewInvoiceGeneration(
  token: string,
  tenantId: string,
  societyId: string,
  payload: InvoiceGenerationPayload
): Promise<InvoiceGenerationPreviewResponse> {
  return tenantApiRequest<InvoiceGenerationPreviewResponse>(
    `/societies/${societyId}/invoices/generation/preview`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function confirmInvoiceGeneration(
  token: string,
  tenantId: string,
  societyId: string,
  payload: InvoiceGenerationPayload
): Promise<InvoiceGenerationConfirmResponse> {
  return tenantApiRequest<InvoiceGenerationConfirmResponse>(
    `/societies/${societyId}/invoices/generation/confirm`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function listLateFeeRules(
  token: string,
  tenantId: string,
  societyId: string
): Promise<LateFeeRule[]> {
  return tenantApiRequest<LateFeeRule[]>(`/societies/${societyId}/late-fees/rules`, token, tenantId);
}

export function createLateFeeRule(
  token: string,
  tenantId: string,
  societyId: string,
  payload: LateFeeRulePayload
): Promise<LateFeeRule> {
  return tenantApiRequest<LateFeeRule>(`/societies/${societyId}/late-fees/rules`, token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateLateFeeRule(
  token: string,
  tenantId: string,
  societyId: string,
  lateFeeRuleId: string,
  payload: LateFeeRulePayload
): Promise<LateFeeRule> {
  return tenantApiRequest<LateFeeRule>(
    `/societies/${societyId}/late-fees/rules/${lateFeeRuleId}`,
    token,
    tenantId,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    }
  );
}

export function inactivateLateFeeRule(
  token: string,
  tenantId: string,
  societyId: string,
  lateFeeRuleId: string
): Promise<LateFeeRule> {
  return tenantApiRequest<LateFeeRule>(
    `/societies/${societyId}/late-fees/rules/${lateFeeRuleId}/inactivate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function activateLateFeeRule(
  token: string,
  tenantId: string,
  societyId: string,
  lateFeeRuleId: string
): Promise<LateFeeRule> {
  return tenantApiRequest<LateFeeRule>(
    `/societies/${societyId}/late-fees/rules/${lateFeeRuleId}/activate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function previewLateFees(
  token: string,
  tenantId: string,
  societyId: string,
  payload: LateFeePreviewPayload
): Promise<LateFeePreviewResponse> {
  return tenantApiRequest<LateFeePreviewResponse>(
    `/societies/${societyId}/late-fees/preview`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function applyLateFees(
  token: string,
  tenantId: string,
  societyId: string,
  payload: LateFeePreviewPayload
): Promise<LateFeeApplyResponse> {
  return tenantApiRequest<LateFeeApplyResponse>(
    `/societies/${societyId}/late-fees/apply`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function getScheduledDueWork(
  token: string,
  tenantId: string,
  societyId: string,
  asOfDate: string
): Promise<ScheduledDueWork> {
  const params = new URLSearchParams({ as_of_date: asOfDate });
  return tenantApiRequest<ScheduledDueWork>(
    `/societies/${societyId}/scheduled-jobs/due?${params.toString()}`,
    token,
    tenantId
  );
}

export function listScheduledJobRuns(
  token: string,
  tenantId: string,
  societyId: string
): Promise<ScheduledJobRun[]> {
  return tenantApiRequest<ScheduledJobRun[]>(`/societies/${societyId}/scheduled-jobs/runs`, token, tenantId);
}

export function runScheduledDueJobs(
  token: string,
  tenantId: string,
  societyId: string,
  payload: ScheduledRunDueJobsPayload
): Promise<ScheduledRunDueJobsResponse> {
  return tenantApiRequest<ScheduledRunDueJobsResponse>(
    `/societies/${societyId}/scheduled-jobs/run-due`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function previewChartOfAccountImport(
  token: string,
  tenantId: string,
  societyId: string,
  rows: ChartOfAccountImportRowInput[]
): Promise<ChartOfAccountImportPreviewResponse> {
  return tenantApiRequest<ChartOfAccountImportPreviewResponse>(
    `/societies/${societyId}/chart-of-accounts/import/preview`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify({ rows })
    }
  );
}

export function confirmChartOfAccountImport(
  token: string,
  tenantId: string,
  societyId: string,
  rows: ChartOfAccountImportRowInput[]
): Promise<ChartOfAccountImportConfirmResponse> {
  return tenantApiRequest<ChartOfAccountImportConfirmResponse>(
    `/societies/${societyId}/chart-of-accounts/import/confirm`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify({ rows })
    }
  );
}

export function listChargeTypes(token: string, tenantId: string, societyId: string): Promise<ChargeType[]> {
  return tenantApiRequest<ChargeType[]>(`/societies/${societyId}/charge-types`, token, tenantId);
}

export function createChargeType(
  token: string,
  tenantId: string,
  societyId: string,
  payload: ChargeTypePayload
): Promise<ChargeType> {
  return tenantApiRequest<ChargeType>(`/societies/${societyId}/charge-types`, token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateChargeType(
  token: string,
  tenantId: string,
  societyId: string,
  chargeTypeId: string,
  payload: ChargeTypePayload
): Promise<ChargeType> {
  return tenantApiRequest<ChargeType>(
    `/societies/${societyId}/charge-types/${chargeTypeId}`,
    token,
    tenantId,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    }
  );
}

export function inactivateChargeType(
  token: string,
  tenantId: string,
  societyId: string,
  chargeTypeId: string
): Promise<ChargeType> {
  return tenantApiRequest<ChargeType>(
    `/societies/${societyId}/charge-types/${chargeTypeId}/inactivate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function activateChargeType(
  token: string,
  tenantId: string,
  societyId: string,
  chargeTypeId: string
): Promise<ChargeType> {
  return tenantApiRequest<ChargeType>(
    `/societies/${societyId}/charge-types/${chargeTypeId}/activate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function listBuildingFloors(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string
): Promise<BuildingFloor[]> {
  return tenantApiRequest<BuildingFloor[]>(
    `/societies/${societyId}/buildings/${buildingId}/floors`,
    token,
    tenantId
  );
}

export function createBuildingFloor(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  payload: BuildingFloorPayload
): Promise<BuildingFloor> {
  return tenantApiRequest<BuildingFloor>(
    `/societies/${societyId}/buildings/${buildingId}/floors`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function updateBuildingFloor(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  floorId: string,
  payload: BuildingFloorPayload
): Promise<BuildingFloor> {
  return tenantApiRequest<BuildingFloor>(
    `/societies/${societyId}/buildings/${buildingId}/floors/${floorId}`,
    token,
    tenantId,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    }
  );
}

export function inactivateBuildingFloor(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  floorId: string
): Promise<BuildingFloor> {
  return tenantApiRequest<BuildingFloor>(
    `/societies/${societyId}/buildings/${buildingId}/floors/${floorId}/inactivate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function activateBuildingFloor(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  floorId: string
): Promise<BuildingFloor> {
  return tenantApiRequest<BuildingFloor>(
    `/societies/${societyId}/buildings/${buildingId}/floors/${floorId}/activate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function createFlat(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  payload: FlatPayload
): Promise<Flat> {
  return tenantApiRequest<Flat>(
    `/societies/${societyId}/buildings/${buildingId}/flats`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function updateFlat(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string,
  payload: FlatPayload
): Promise<Flat> {
  return tenantApiRequest<Flat>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}`,
    token,
    tenantId,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    }
  );
}

export function inactivateFlat(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string
): Promise<Flat> {
  return tenantApiRequest<Flat>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/inactivate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function activateFlat(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string
): Promise<Flat> {
  return tenantApiRequest<Flat>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/activate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function previewFlatImport(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  rows: FlatImportRowInput[]
): Promise<FlatImportPreviewResponse> {
  return tenantApiRequest<FlatImportPreviewResponse>(
    `/societies/${societyId}/buildings/${buildingId}/flats/import/preview`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify({ rows })
    }
  );
}

export function confirmFlatImport(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  rows: FlatImportRowInput[]
): Promise<FlatImportConfirmResponse> {
  return tenantApiRequest<FlatImportConfirmResponse>(
    `/societies/${societyId}/buildings/${buildingId}/flats/import/confirm`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify({ rows })
    }
  );
}

export function listOwners(token: string, tenantId: string, societyId: string): Promise<Owner[]> {
  return tenantApiRequest<Owner[]>(`/societies/${societyId}/owners`, token, tenantId);
}

export function createOwner(
  token: string,
  tenantId: string,
  societyId: string,
  payload: OwnerPayload
): Promise<Owner> {
  return tenantApiRequest<Owner>(`/societies/${societyId}/owners`, token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateOwner(
  token: string,
  tenantId: string,
  societyId: string,
  ownerId: string,
  payload: OwnerPayload
): Promise<Owner> {
  return tenantApiRequest<Owner>(`/societies/${societyId}/owners/${ownerId}`, token, tenantId, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function inactivateOwner(
  token: string,
  tenantId: string,
  societyId: string,
  ownerId: string
): Promise<Owner> {
  return tenantApiRequest<Owner>(
    `/societies/${societyId}/owners/${ownerId}/inactivate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function activateOwner(
  token: string,
  tenantId: string,
  societyId: string,
  ownerId: string
): Promise<Owner> {
  return tenantApiRequest<Owner>(
    `/societies/${societyId}/owners/${ownerId}/activate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function listVendors(token: string, tenantId: string, societyId: string): Promise<Vendor[]> {
  return tenantApiRequest<Vendor[]>(`/societies/${societyId}/vendors`, token, tenantId);
}

export function createVendor(
  token: string,
  tenantId: string,
  societyId: string,
  payload: VendorPayload
): Promise<Vendor> {
  return tenantApiRequest<Vendor>(`/societies/${societyId}/vendors`, token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateVendor(
  token: string,
  tenantId: string,
  societyId: string,
  vendorId: string,
  payload: VendorPayload
): Promise<Vendor> {
  return tenantApiRequest<Vendor>(`/societies/${societyId}/vendors/${vendorId}`, token, tenantId, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function inactivateVendor(
  token: string,
  tenantId: string,
  societyId: string,
  vendorId: string
): Promise<Vendor> {
  return tenantApiRequest<Vendor>(
    `/societies/${societyId}/vendors/${vendorId}/inactivate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function activateVendor(
  token: string,
  tenantId: string,
  societyId: string,
  vendorId: string
): Promise<Vendor> {
  return tenantApiRequest<Vendor>(
    `/societies/${societyId}/vendors/${vendorId}/activate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function listExpenseCategories(
  token: string,
  tenantId: string,
  societyId: string
): Promise<ExpenseCategory[]> {
  return tenantApiRequest<ExpenseCategory[]>(`/societies/${societyId}/expense-categories`, token, tenantId);
}

export function createExpenseCategory(
  token: string,
  tenantId: string,
  societyId: string,
  payload: ExpenseCategoryPayload
): Promise<ExpenseCategory> {
  return tenantApiRequest<ExpenseCategory>(`/societies/${societyId}/expense-categories`, token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateExpenseCategory(
  token: string,
  tenantId: string,
  societyId: string,
  categoryId: string,
  payload: ExpenseCategoryPayload
): Promise<ExpenseCategory> {
  return tenantApiRequest<ExpenseCategory>(
    `/societies/${societyId}/expense-categories/${categoryId}`,
    token,
    tenantId,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    }
  );
}

export function inactivateExpenseCategory(
  token: string,
  tenantId: string,
  societyId: string,
  categoryId: string
): Promise<ExpenseCategory> {
  return tenantApiRequest<ExpenseCategory>(
    `/societies/${societyId}/expense-categories/${categoryId}/inactivate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function activateExpenseCategory(
  token: string,
  tenantId: string,
  societyId: string,
  categoryId: string
): Promise<ExpenseCategory> {
  return tenantApiRequest<ExpenseCategory>(
    `/societies/${societyId}/expense-categories/${categoryId}/activate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function listExpenses(token: string, tenantId: string, societyId: string): Promise<Expense[]> {
  return tenantApiRequest<Expense[]>(`/societies/${societyId}/expenses`, token, tenantId);
}

export function createExpense(
  token: string,
  tenantId: string,
  societyId: string,
  payload: ExpensePayload
): Promise<Expense> {
  return tenantApiRequest<Expense>(`/societies/${societyId}/expenses`, token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateExpense(
  token: string,
  tenantId: string,
  societyId: string,
  expenseId: string,
  payload: ExpensePayload
): Promise<Expense> {
  return tenantApiRequest<Expense>(`/societies/${societyId}/expenses/${expenseId}`, token, tenantId, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function approveExpense(
  token: string,
  tenantId: string,
  societyId: string,
  expenseId: string
): Promise<Expense> {
  return tenantApiRequest<Expense>(
    `/societies/${societyId}/expenses/${expenseId}/approve`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function cancelExpense(
  token: string,
  tenantId: string,
  societyId: string,
  expenseId: string,
  reason: string
): Promise<Expense> {
  return tenantApiRequest<Expense>(`/societies/${societyId}/expenses/${expenseId}/cancel`, token, tenantId, {
    method: "POST",
    body: JSON.stringify({ reason })
  });
}

export function listExpensePayments(
  token: string,
  tenantId: string,
  societyId: string
): Promise<ExpensePayment[]> {
  return tenantApiRequest<ExpensePayment[]>(`/societies/${societyId}/expense-payments`, token, tenantId);
}

export function createExpensePayment(
  token: string,
  tenantId: string,
  societyId: string,
  payload: ExpensePaymentPayload
): Promise<ExpensePayment> {
  return tenantApiRequest<ExpensePayment>(`/societies/${societyId}/expense-payments`, token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listJournals(token: string, tenantId: string, societyId: string): Promise<JournalEntry[]> {
  return tenantApiRequest<JournalEntry[]>(`/societies/${societyId}/journals`, token, tenantId);
}

export function getJournal(
  token: string,
  tenantId: string,
  societyId: string,
  journalEntryId: string
): Promise<JournalEntryDetail> {
  return tenantApiRequest<JournalEntryDetail>(
    `/societies/${societyId}/journals/${journalEntryId}`,
    token,
    tenantId
  );
}

export function createJournal(
  token: string,
  tenantId: string,
  societyId: string,
  payload: JournalEntryPayload
): Promise<JournalEntryDetail> {
  return tenantApiRequest<JournalEntryDetail>(`/societies/${societyId}/journals`, token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function createOpeningBalanceJournal(
  token: string,
  tenantId: string,
  societyId: string,
  payload: OpeningBalanceJournalPayload
): Promise<JournalEntryDetail> {
  return tenantApiRequest<JournalEntryDetail>(
    `/societies/${societyId}/journals/opening-balance`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function reverseJournal(
  token: string,
  tenantId: string,
  societyId: string,
  journalEntryId: string,
  reason: string
): Promise<JournalEntry> {
  return tenantApiRequest<JournalEntry>(
    `/societies/${societyId}/journals/${journalEntryId}/reverse`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify({ reason })
    }
  );
}

export function listAccountTransfers(
  token: string,
  tenantId: string,
  societyId: string
): Promise<AccountTransfer[]> {
  return tenantApiRequest<AccountTransfer[]>(`/societies/${societyId}/account-transfers`, token, tenantId);
}

export function createAccountTransfer(
  token: string,
  tenantId: string,
  societyId: string,
  payload: AccountTransferPayload
): Promise<AccountTransfer> {
  return tenantApiRequest<AccountTransfer>(`/societies/${societyId}/account-transfers`, token, tenantId, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listOtherIncomeReceipts(
  token: string,
  tenantId: string,
  societyId: string
): Promise<OtherIncomeReceipt[]> {
  return tenantApiRequest<OtherIncomeReceipt[]>(
    `/societies/${societyId}/other-income-receipts`,
    token,
    tenantId
  );
}

export function createOtherIncomeReceipt(
  token: string,
  tenantId: string,
  societyId: string,
  payload: OtherIncomeReceiptPayload
): Promise<OtherIncomeReceipt> {
  return tenantApiRequest<OtherIncomeReceipt>(
    `/societies/${societyId}/other-income-receipts`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function reverseOtherIncomeReceipt(
  token: string,
  tenantId: string,
  societyId: string,
  receiptId: string,
  reason: string
): Promise<OtherIncomeReceipt> {
  return tenantApiRequest<OtherIncomeReceipt>(
    `/societies/${societyId}/other-income-receipts/${receiptId}/reverse`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify({ reason })
    }
  );
}

export function getAccountLedger(
  token: string,
  tenantId: string,
  societyId: string,
  accountId: string,
  dateFrom?: string,
  dateTo?: string
): Promise<AccountLedger> {
  const params = new URLSearchParams();
  if (dateFrom) {
    params.set("date_from", dateFrom);
  }
  if (dateTo) {
    params.set("date_to", dateTo);
  }
  const query = params.toString();
  return tenantApiRequest<AccountLedger>(
    `/societies/${societyId}/accounts/${accountId}/ledger${query ? `?${query}` : ""}`,
    token,
    tenantId
  );
}

export function getTrialBalance(
  token: string,
  tenantId: string,
  societyId: string,
  asOfDate: string
): Promise<TrialBalance> {
  const params = new URLSearchParams({ as_of_date: asOfDate });
  return tenantApiRequest<TrialBalance>(
    `/societies/${societyId}/trial-balance?${params.toString()}`,
    token,
    tenantId
  );
}

export function getIncomeExpenseReport(
  token: string,
  tenantId: string,
  societyId: string,
  periodStart: string,
  periodEnd: string
): Promise<IncomeExpenseReport> {
  const params = new URLSearchParams({ period_start: periodStart, period_end: periodEnd });
  return tenantApiRequest<IncomeExpenseReport>(
    `/societies/${societyId}/reports/income-expense?${params.toString()}`,
    token,
    tenantId
  );
}

export function exportIncomeExpenseReport(
  token: string,
  tenantId: string,
  societyId: string,
  periodStart: string,
  periodEnd: string,
  exportFormat: "xlsx" | "pdf"
): Promise<Blob> {
  const params = new URLSearchParams({
    period_start: periodStart,
    period_end: periodEnd,
    export_format: exportFormat
  });
  return tenantApiBlobRequest(
    `/societies/${societyId}/reports/income-expense/export?${params.toString()}`,
    token,
    tenantId
  );
}

export function getBalanceSheetReport(
  token: string,
  tenantId: string,
  societyId: string,
  asOfDate: string
): Promise<BalanceSheetReport> {
  const params = new URLSearchParams({ as_of_date: asOfDate });
  return tenantApiRequest<BalanceSheetReport>(
    `/societies/${societyId}/reports/balance-sheet?${params.toString()}`,
    token,
    tenantId
  );
}

export function exportBalanceSheetReport(
  token: string,
  tenantId: string,
  societyId: string,
  asOfDate: string,
  exportFormat: "xlsx" | "pdf"
): Promise<Blob> {
  const params = new URLSearchParams({ as_of_date: asOfDate, export_format: exportFormat });
  return tenantApiBlobRequest(
    `/societies/${societyId}/reports/balance-sheet/export?${params.toString()}`,
    token,
    tenantId
  );
}

export type PeriodOperationalReportKind = "billing" | "collection" | "expenses";
export type AsOfOperationalReportKind = "defaulters" | "outstanding";

export function getBillingReport(
  token: string,
  tenantId: string,
  societyId: string,
  periodStart: string,
  periodEnd: string
): Promise<BillingReport> {
  const params = new URLSearchParams({ period_start: periodStart, period_end: periodEnd });
  return tenantApiRequest<BillingReport>(`/societies/${societyId}/reports/billing?${params.toString()}`, token, tenantId);
}

export function getCollectionReport(
  token: string,
  tenantId: string,
  societyId: string,
  periodStart: string,
  periodEnd: string
): Promise<CollectionReport> {
  const params = new URLSearchParams({ period_start: periodStart, period_end: periodEnd });
  return tenantApiRequest<CollectionReport>(`/societies/${societyId}/reports/collection?${params.toString()}`, token, tenantId);
}

export function getExpenseOperationalReport(
  token: string,
  tenantId: string,
  societyId: string,
  periodStart: string,
  periodEnd: string
): Promise<ExpenseOperationalReport> {
  const params = new URLSearchParams({ period_start: periodStart, period_end: periodEnd });
  return tenantApiRequest<ExpenseOperationalReport>(`/societies/${societyId}/reports/expenses?${params.toString()}`, token, tenantId);
}

export function getDefaulterReport(
  token: string,
  tenantId: string,
  societyId: string,
  asOfDate: string
): Promise<DefaulterReport> {
  const params = new URLSearchParams({ as_of_date: asOfDate });
  return tenantApiRequest<DefaulterReport>(`/societies/${societyId}/reports/defaulters?${params.toString()}`, token, tenantId);
}

export function exportPeriodOperationalReport(
  token: string,
  tenantId: string,
  societyId: string,
  reportKind: PeriodOperationalReportKind,
  periodStart: string,
  periodEnd: string,
  exportFormat: "xlsx" | "pdf"
): Promise<Blob> {
  const params = new URLSearchParams({ period_start: periodStart, period_end: periodEnd, export_format: exportFormat });
  return tenantApiBlobRequest(`/societies/${societyId}/reports/${reportKind}/export?${params.toString()}`, token, tenantId);
}

export function exportAsOfOperationalReport(
  token: string,
  tenantId: string,
  societyId: string,
  reportKind: AsOfOperationalReportKind,
  asOfDate: string,
  exportFormat: "xlsx" | "pdf"
): Promise<Blob> {
  const params = new URLSearchParams({ as_of_date: asOfDate, export_format: exportFormat });
  return tenantApiBlobRequest(`/societies/${societyId}/reports/${reportKind}/export?${params.toString()}`, token, tenantId);
}

export function listFlatOwnerships(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string
): Promise<FlatOwnership[]> {
  return tenantApiRequest<FlatOwnership[]>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/ownerships`,
    token,
    tenantId
  );
}

export function createFlatOwnership(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string,
  payload: FlatOwnershipPayload
): Promise<FlatOwnership> {
  return tenantApiRequest<FlatOwnership>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/ownerships`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function updateFlatOwnership(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string,
  ownershipId: string,
  payload: FlatOwnershipPayload
): Promise<FlatOwnership> {
  return tenantApiRequest<FlatOwnership>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/ownerships/${ownershipId}`,
    token,
    tenantId,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    }
  );
}

export function closeFlatOwnership(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string,
  ownershipId: string,
  effectiveTo: string
): Promise<FlatOwnership> {
  return tenantApiRequest<FlatOwnership>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/ownerships/${ownershipId}/close`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify({ effective_to: effectiveTo })
    }
  );
}

export function activateFlatOwnership(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string,
  ownershipId: string
): Promise<FlatOwnership> {
  return tenantApiRequest<FlatOwnership>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/ownerships/${ownershipId}/activate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function listResidents(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string
): Promise<Resident[]> {
  return tenantApiRequest<Resident[]>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/residents`,
    token,
    tenantId
  );
}

export function createResident(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string,
  payload: ResidentPayload
): Promise<Resident> {
  return tenantApiRequest<Resident>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/residents`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function updateResident(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string,
  residentId: string,
  payload: ResidentPayload
): Promise<Resident> {
  return tenantApiRequest<Resident>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/residents/${residentId}`,
    token,
    tenantId,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    }
  );
}

export function moveOutResident(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string,
  residentId: string,
  moveOutDate: string
): Promise<Resident> {
  return tenantApiRequest<Resident>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/residents/${residentId}/move-out`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify({ move_out_date: moveOutDate })
    }
  );
}

export function activateResident(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string,
  residentId: string
): Promise<Resident> {
  return tenantApiRequest<Resident>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/residents/${residentId}/activate`,
    token,
    tenantId,
    { method: "POST" }
  );
}

export function listLeaseAgreements(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string
): Promise<LeaseAgreement[]> {
  return tenantApiRequest<LeaseAgreement[]>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/lease-agreements`,
    token,
    tenantId
  );
}

export function createLeaseAgreement(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string,
  payload: LeaseAgreementPayload
): Promise<LeaseAgreement> {
  return tenantApiRequest<LeaseAgreement>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/lease-agreements`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function updateLeaseAgreement(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string,
  leaseAgreementId: string,
  payload: LeaseAgreementPayload
): Promise<LeaseAgreement> {
  return tenantApiRequest<LeaseAgreement>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/lease-agreements/${leaseAgreementId}`,
    token,
    tenantId,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    }
  );
}

export function terminateLeaseAgreement(
  token: string,
  tenantId: string,
  societyId: string,
  buildingId: string,
  flatId: string,
  leaseAgreementId: string,
  moveOutDate: string,
  reason: string
): Promise<LeaseAgreement> {
  return tenantApiRequest<LeaseAgreement>(
    `/societies/${societyId}/buildings/${buildingId}/flats/${flatId}/lease-agreements/${leaseAgreementId}/terminate`,
    token,
    tenantId,
    {
      method: "POST",
      body: JSON.stringify({ move_out_date: moveOutDate, reason })
    }
  );
}
