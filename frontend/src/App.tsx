import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import {
  activateBuilding,
  activateBuildingFloor,
  activateBillingRule,
  activateChartOfAccount,
  activateChargeType,
  activateExpenseCategory,
  activateFlat,
  activateFlatOwnership,
  activateFlatType,
  activateLateFeeRule,
  activateManagedUser,
  activateOwner,
  activateResident,
  activateSociety,
  activateTenant,
  activateVendor,
  activateWing,
  approveExpense,
  applyLateFees,
  bulkCancelInvoices,
  cancelInvoice,
  cancelExpense,
  closeFlatOwnership,
  confirmChartOfAccountImport,
  confirmFlatImport,
  confirmInvoiceGeneration,
  createAccountTransfer,
  createBuilding,
  createBuildingFloor,
  createBillingRule,
  createChartOfAccount,
  createChargeType,
  createExpenseCategory,
  createExpensePayment,
  createExpense,
  createFlat,
  createFlatOwnership,
  createFlatType,
  createJournal,
  createLateFeeRule,
  createLeaseAgreement,
  createManagedUser,
  createManualInvoice,
  createOpeningBalanceJournal,
  createOtherIncomeReceipt,
  createOwner,
  createPayment,
  createResident,
  createSociety,
  createTenant,
  createVendor,
  createWing,
  exportBalanceSheetReport,
  exportIncomeExpenseReport,
  exportAsOfOperationalReport,
  exportPaymentRegister,
  exportPeriodOperationalReport,
  getCurrentUser,
  getAccountLedger,
  getBalanceSheetReport,
  getBillingReport,
  getCollectionReport,
  getDefaulterReport,
  getExpenseOperationalReport,
  getFlatLedger,
  getIncomeExpenseReport,
  getInvoice,
  getInvoiceSequence,
  getJournal,
  getMyAccess,
  getOutstandingSummary,
  getScheduledDueWork,
  getTrialBalance,
  inactivateBillingRule,
  inactivateChartOfAccount,
  inactivateChargeType,
  inactivateExpenseCategory,
  inactivateFlat,
  inactivateBuildingFloor,
  inactivateFlatType,
  inactivateLateFeeRule,
  inactivateOwner,
  inactivateVendor,
  listAccountTransfers,
  listBuildings,
  listBuildingFloors,
  listBillingRules,
  listChartOfAccounts,
  listFlatOwnerships,
  listFlats,
  listFlatTypes,
  listChargeTypes,
  listExpenseCategories,
  listExpensePayments,
  listExpenses,
  listInvoices,
  listJournals,
  listLateFeeRules,
  listLeaseAgreements,
  listManagedUsers,
  listOtherIncomeReceipts,
  listPaymentRegister,
  listOwners,
  listResidents,
  listScheduledJobRuns,
  listSocieties,
  listTenants,
  listVendors,
  listWings,
  moveOutResident,
  previewChartOfAccountImport,
  previewFlatImport,
  previewInvoiceGeneration,
  previewLateFees,
  reverseJournal,
  reverseOtherIncomeReceipt,
  reversePayment,
  runScheduledDueJobs,
  suspendBuilding,
  suspendManagedUser,
  suspendSociety,
  suspendTenant,
  suspendWing,
  terminateLeaseAgreement,
  updateBuilding,
  updateBuildingFloor,
  updateBillingRule,
  updateChartOfAccount,
  updateChargeType,
  updateExpenseCategory,
  updateExpense,
  updateFlat,
  updateFlatOwnership,
  updateFlatType,
  updateInvoiceSequence,
  updateLateFeeRule,
  updateLeaseAgreement,
  updateOwner,
  updateResident,
  updateSociety,
  updateTenant,
  updateVendor,
  updateWing,
  type AccessSociety,
  type AccessTenant,
  type AccountLedger,
  type AccountTransfer,
  type AccountTransferPayload,
  type BalanceSheetReport,
  type BillingReport,
  type BillingRule,
  type BillingRulePayload,
  type Building,
  type BuildingFloor,
  type BuildingFloorPayload,
  type BuildingPayload,
  type ChartOfAccount,
  type ChartOfAccountImportPreviewResponse,
  type ChartOfAccountImportRowInput,
  type ChartOfAccountPayload,
  type ChargeType,
  type ChargeTypePayload,
  type CollectionReport,
  type CurrentUser,
  type DefaulterReport,
  type DocumentSequence,
  type DocumentSequencePayload,
  type Expense,
  type ExpenseCategory,
  type ExpenseCategoryPayload,
  type ExpensePayload,
  type ExpensePayment,
  type ExpensePaymentPayload,
  type ExpenseOperationalReport,
  type Flat,
  type FlatImportPreviewResponse,
  type FlatImportRowInput,
  type FlatLedger,
  type FlatOwnership,
  type FlatOwnershipPayload,
  type FlatPayload,
  type FlatType,
  type FlatTypePayload,
  type Invoice,
  type InvoiceDetail,
  type InvoiceGenerationPayload,
  type InvoiceGenerationPreviewResponse,
  type InvoiceListFilters,
  type IncomeExpenseReport,
  type JournalEntry,
  type JournalEntryDetail,
  type JournalEntryPayload,
  type LateFeePreviewPayload,
  type LateFeePreviewResponse,
  type LateFeeRule,
  type LateFeeRulePayload,
  type LeaseAgreement,
  type LeaseAgreementPayload,
  type ManagedUser,
  type ManagedUserCreatePayload,
  type OpeningBalanceJournalPayload,
  type ManualInvoicePayload,
  type MyAccess,
  type OtherIncomeReceipt,
  type OtherIncomeReceiptPayload,
  type Owner,
  type OwnerPayload,
  type OutstandingSummary,
  type PaymentDetail,
  type PaymentPayload,
  type PaymentRegisterRow,
  type Resident,
  type ResidentPayload,
  type ScheduledDueWork,
  type ScheduledJobRun,
  type ScheduledRunDueJobsPayload,
  type Society,
  type SocietyPayload,
  type Tenant,
  type TrialBalance,
  type Vendor,
  type VendorPayload,
  type Wing,
  type WingPayload
} from "./api";
import { clearKeycloakTokens, initKeycloak, keycloak, saveKeycloakTokens } from "./keycloak";

type SessionState = "loading" | "anonymous" | "authenticated";
type Workspace =
  | "dashboard"
  | "tenants"
  | "users"
  | "societies"
  | "buildings"
  | "floors"
  | "flatTypes"
  | "chartOfAccounts"
  | "bankCashAccounts"
  | "accountLedgers"
  | "openingBalances"
  | "trialBalance"
  | "incomeExpense"
  | "balanceSheet"
  | "operationalReports"
  | "journals"
  | "accountTransfers"
  | "otherIncome"
  | "chargeTypes"
  | "expenseCategories"
  | "expenses"
  | "numberingSettings"
  | "billingRules"
  | "lateFeeRules"
  | "lateFeeApplication"
  | "scheduledJobs"
  | "invoiceGeneration"
  | "manualInvoices"
  | "invoices"
  | "payments"
  | "paymentRegister"
  | "outstanding"
  | "vendors"
  | "wings"
  | "flats"
  | "flatLedgers"
  | "owners"
  | "ownerships"
  | "residents"
  | "leaseAgreements";

const tenantFormDefaults = {
  name: "",
  slug: "",
  subscription_plan: "starter",
  billing_email: "",
  phone: "",
  timezone: "Asia/Kolkata",
  locale: "en-IN",
  currency: "INR"
};

const societyFormDefaults = {
  name: "",
  registration_number: "",
  address_line1: "",
  address_line2: "",
  city: "",
  state: "",
  postal_code: "",
  country: "India",
  timezone: "Asia/Kolkata",
  locale: "en-IN",
  currency: "INR",
  financial_year_start_month: 4,
  receivable_account_id: "",
  payable_account_id: "",
  member_advance_account_id: ""
};

const buildingFormDefaults = {
  name: "",
  code: ""
};

const wingFormDefaults = {
  name: "",
  code: ""
};

const flatFormDefaults = {
  wing_id: "",
  floor_id: "",
  flat_type_id: "",
  flat_number: "",
  floor_number: "",
  carpet_area_sqft: "",
  built_up_area_sqft: "",
  parking_count: ""
};

const flatTypeFormDefaults = {
  name: "",
  code: "",
  unit_category: "residential",
  bedroom_count: "",
  bathroom_count: "",
  carpet_area_sqft: "",
  built_up_area_sqft: "",
  default_parking_count: 0
};

const chargeTypeFormDefaults = {
  name: "",
  code: "",
  description: "",
  revenue_account_id: ""
};

const expenseCategoryFormDefaults = {
  name: "",
  code: "",
  description: "",
  expense_account_id: ""
};

const expenseFormDefaults = {
  vendor_id: "",
  expense_category_id: "",
  payment_account_id: "",
  expense_type: "vendor_bill",
  vendor_bill_number: "",
  reference_number: "",
  expense_date: "",
  due_date: "",
  description: "",
  amount: "",
  tax_amount: "0.00",
  notes: ""
};

const expensePaymentFormDefaults = {
  vendor_id: "",
  payment_account_id: "",
  payment_date: "",
  amount: "",
  payment_mode: "bank_transfer",
  reference_number: "",
  notes: ""
};

const journalLineDefaults = () => ({
  account_id: "",
  description: "",
  debit_amount: "",
  credit_amount: ""
});

const journalFormDefaults = () => ({
  journal_date: todayIsoDate(),
  reference_number: "",
  description: "",
  notes: "",
  lines: [journalLineDefaults(), journalLineDefaults()]
});

const bankCashAccountFormDefaults = {
  account_code: "",
  account_name: "",
  description: ""
};

const openingBalanceFormDefaults = () => ({
  opening_date: todayIsoDate(),
  reference_number: "",
  notes: "",
  lines: [journalLineDefaults(), journalLineDefaults()]
});

const accountTransferFormDefaults = {
  from_account_id: "",
  to_account_id: "",
  transfer_date: "",
  amount: "",
  transfer_mode: "bank_transfer",
  reference_number: "",
  description: "",
  notes: ""
};

const otherIncomeFormDefaults = {
  receipt_date: "",
  payer_name: "",
  payer_type: "bank",
  income_account_id: "",
  deposit_account_id: "",
  amount: "",
  receipt_mode: "bank_transfer",
  reference_number: "",
  description: "",
  notes: ""
};

const accountLedgerFilterDefaults = {
  account_id: "",
  date_from: "",
  date_to: ""
};

const flatLedgerFilterDefaults = {
  building_id: "",
  flat_id: "",
  date_from: "",
  date_to: ""
};

const trialBalanceFilterDefaults = {
  as_of_date: todayIsoDate()
};

const incomeExpenseFilterDefaults = {
  period_start: todayIsoDate().slice(0, 8) + "01",
  period_end: todayIsoDate()
};

const balanceSheetFilterDefaults = {
  as_of_date: todayIsoDate()
};

const billingRuleFormDefaults = {
  charge_type_id: "",
  name: "",
  calculation_method: "fixed",
  amount: "",
  area_basis: "",
  frequency: "monthly",
  generation_day: 1,
  due_day: 10,
  billing_period_timing: "current_period",
  next_generation_date: "",
  scope_type: "all_flats",
  building_id: "",
  wing_id: "",
  flat_type_id: "",
  effective_from: "",
  effective_to: "",
  description: "",
  late_fee_rule_ids: [] as string[]
};

const lateFeeRuleFormDefaults = {
  charge_type_id: "",
  name: "",
  calculation_method: "fixed",
  amount: "",
  grace_days: 0,
  repeat_interval_days: "",
  max_applications_per_invoice: "",
  effective_from: "",
  effective_to: "",
  description: ""
};

const lateFeeApplicationDefaults = {
  as_of_date: todayIsoDate(),
  late_fee_rule_ids: [] as string[]
};

const scheduledJobFilterDefaults = {
  as_of_date: todayIsoDate()
};

const invoiceSequenceFormDefaults = {
  prefix: "INV",
  include_period: true,
  include_financial_year: false,
  separator: "-",
  next_sequence: 1,
  padding: 5,
  reset_policy: "never"
};

const manualInvoiceFormDefaults = {
  building_id: "",
  flat_id: "",
  charge_type_id: "",
  description: "",
  quantity: "1.00",
  unit_amount: "",
  invoice_date: "",
  due_date: "",
  billing_period_start: "",
  billing_period_end: "",
  notes: "",
  late_fee_rule_ids: [] as string[]
};

const invoiceFilterDefaults = {
  month: "",
  invoice_date_from: "",
  invoice_date_to: "",
  due_date_from: "",
  due_date_to: "",
  flat_id: "",
  status: "",
  page: 1,
  page_size: 50
};

const paymentFormDefaults = {
  building_id: "",
  flat_id: "",
  deposit_account_id: "",
  payment_date: "",
  amount: "",
  payment_mode: "upi",
  reference_number: "",
  notes: ""
};

const paymentRegisterFilterDefaults = {
  month: "",
  payment_date_from: "",
  payment_date_to: "",
  flat_number: "",
  status: "",
  payment_mode: "",
  page: 1,
  page_size: 50
};

const paymentModes = ["cash", "bank_transfer", "cheque", "upi", "card", "other"];
const paymentStatuses = ["received", "reversed"];
const otherIncomePayerTypes = ["bank", "vendor", "resident", "external_party", "other"];

const chartOfAccountFormDefaults = {
  parent_account_id: "",
  account_code: "",
  account_name: "",
  account_type: "income",
  normal_balance: "credit",
  description: ""
};

const buildingFloorFormDefaults = {
  floor_label: "",
  floor_number: 0
};

const ownerFormDefaults = {
  owner_type: "individual",
  full_name: "",
  email: "",
  mobile_number: "",
  tax_identifier: "",
  billing_address: ""
};

const vendorFormDefaults = {
  vendor_code: "",
  vendor_name: "",
  vendor_type: "company",
  contact_person: "",
  email: "",
  mobile_number: "",
  tax_identifier: "",
  billing_address: ""
};

const ownershipFormDefaults = {
  owner_id: "",
  ownership_type: "primary_owner",
  ownership_percentage: "100",
  effective_from: "",
  effective_to: ""
};

const residentFormDefaults = {
  owner_id: "",
  resident_type: "owner_occupier",
  full_name: "",
  email: "",
  mobile_number: "",
  move_in_date: "",
  move_out_date: ""
};

const leaseAgreementFormDefaults = {
  owner_id: "",
  resident_id: "",
  tenant_name: "",
  tenant_email: "",
  tenant_mobile_number: "",
  agreement_start_date: "",
  agreement_end_date: "",
  move_in_date: "",
  move_out_date: "",
  monthly_rent: "",
  security_deposit: "",
  police_verification_status: "pending",
  document_reference: "",
  notes: ""
};

const managedUserFormDefaults = {
  full_name: "",
  email: "",
  mobile_number: "",
  temporary_password: "",
  tenant_admin: false,
  society_id: "",
  society_role: ""
};

const tenantPlans = ["starter", "professional", "enterprise"];
const currencies = ["INR", "USD", "AED"];
const timezones = ["Asia/Kolkata", "Asia/Dubai", "UTC"];
const locales = ["en-IN", "en-US", "en-AE"];
const ownerTypes = ["individual", "company", "trust", "other"];
const vendorTypes = ["individual", "company", "firm", "other"];
const ownershipTypes = ["primary_owner", "co_owner"];
const residentTypes = ["owner_occupier", "tenant", "family_member", "staff", "other"];
const policeVerificationStatuses = ["not_required", "pending", "completed"];
const societyRoles = [
  "society_admin",
  "treasurer",
  "accountant",
  "auditor",
  "committee_member",
  "flat_owner",
  "read_only_resident"
];
const unitCategories = ["residential", "commercial", "shop", "office", "parking", "other"];
const accountTypes = ["asset", "liability", "equity", "income", "expense"];
const normalBalances = ["debit", "credit"];
const billingCalculationMethods = ["fixed", "area_based", "parking_based", "flat_type_fixed", "manual"];
const billingFrequencies = ["monthly", "quarterly", "half_yearly", "yearly", "one_time"];
const billingScopeTypes = ["all_flats", "building", "wing", "flat_type"];
const billingAreaBases = ["carpet_area", "built_up_area"];
const billingPeriodTimings = ["current_period", "next_period"];
const lateFeeCalculationMethods = ["fixed", "percent_of_due"];
const invoiceStatuses = ["issued", "partially_paid", "paid", "overdue", "cancelled"];
const documentResetPolicies = ["never", "monthly", "financial_year"];
const operationalReportTypes = [
  { value: "billing", label: "Billing Report", mode: "period" },
  { value: "collection", label: "Collection Report", mode: "period" },
  { value: "expenses", label: "Expense Report", mode: "period" },
  { value: "defaulters", label: "Defaulter Report", mode: "as_of" },
  { value: "outstanding", label: "Outstanding Report", mode: "as_of" }
] as const;
type OperationalReportType = (typeof operationalReportTypes)[number]["value"];
type OperationalReportResult =
  | BillingReport
  | CollectionReport
  | ExpenseOperationalReport
  | DefaulterReport
  | OutstandingSummary;
type ReasonDialogState = {
  title: string;
  description: string;
  reasonLabel: string;
  confirmLabel: string;
  errorMessage: string;
  onConfirm: (reason: string) => Promise<void>;
};
const contextStorageKey = "propelsync.admin.context";
const financialYearMonths = [
  { label: "January", value: 1 },
  { label: "April", value: 4 },
  { label: "July", value: 7 },
  { label: "October", value: 10 }
];

type StoredAdminContext = Partial<{
  workspace: Workspace;
  tenantId: string;
  societyId: string;
  buildingId: string;
  flatId: string;
}>;

function readStoredAdminContext(): StoredAdminContext {
  const raw = window.localStorage.getItem(contextStorageKey);
  if (!raw) {
    return {};
  }

  try {
    return JSON.parse(raw) as StoredAdminContext;
  } catch {
    window.localStorage.removeItem(contextStorageKey);
    return {};
  }
}

function storeAdminContext(context: StoredAdminContext): void {
  window.localStorage.setItem(contextStorageKey, JSON.stringify(context));
}

function nullableText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function nullableNumber(value: string): number | null {
  const trimmed = value.trim();
  return trimmed ? Number(trimmed) : null;
}

function toIsoDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function monthDateRange(monthValue: string): { from: string; to: string } {
  const [year, month] = monthValue.split("-").map(Number);
  if (!year || !month) {
    return { from: "", to: "" };
  }
  const from = new Date(Date.UTC(year, month - 1, 1));
  const to = new Date(Date.UTC(year, month, 0));
  return { from: toIsoDate(from), to: toIsoDate(to) };
}

function buildOldestFirstPaymentAllocations(openInvoices: Invoice[], amount: string): Record<string, string> {
  let remainingAmount = Number(amount) || 0;
  const allocations: Record<string, string> = {};
  if (remainingAmount <= 0) {
    return allocations;
  }

  openInvoices.forEach((invoice) => {
    if (remainingAmount <= 0) {
      return;
    }
    const invoiceBalance = Number(invoice.amount_due) || 0;
    const allocatedAmount = Math.min(remainingAmount, invoiceBalance);
    if (allocatedAmount > 0) {
      allocations[invoice.id] = allocatedAmount.toFixed(2);
      remainingAmount = Number((remainingAmount - allocatedAmount).toFixed(2));
    }
  });
  return allocations;
}

function paymentInvoiceLabel(invoice: Invoice | undefined): string {
  if (!invoice) {
    return "Invoice";
  }
  const note = invoice.notes?.toLowerCase() ?? "";
  if (note.includes("late fee") || note.includes("penalty")) {
    return "Penalty";
  }
  return "Invoice";
}

function currentMonthInvoiceGenerationDefaults(): InvoiceGenerationPayload {
  const now = new Date();
  const periodStart = new Date(Date.UTC(now.getFullYear(), now.getMonth(), 1));
  const periodEnd = new Date(Date.UTC(now.getFullYear(), now.getMonth() + 1, 0));
  const invoiceDate = new Date(Date.UTC(now.getFullYear(), now.getMonth(), 1));
  const dueDate = new Date(Date.UTC(now.getFullYear(), now.getMonth(), 10));
  return {
    billing_period_start: toIsoDate(periodStart),
    billing_period_end: toIsoDate(periodEnd),
    invoice_date: toIsoDate(invoiceDate),
    due_date: toIsoDate(dueDate),
    billing_rule_ids: [],
    flat_ids: []
  };
}

function nextBuildingFloorNumber(floors: BuildingFloor[]): number {
  if (!floors.length) {
    return 0;
  }
  return Math.max(...floors.map((floor) => floor.floor_number)) + 1;
}

function parseCsvLine(line: string): string[] {
  const values: string[] = [];
  let current = "";
  let isQuoted = false;

  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    const nextCharacter = line[index + 1];

    if (character === "\"" && isQuoted && nextCharacter === "\"") {
      current += "\"";
      index += 1;
    } else if (character === "\"") {
      isQuoted = !isQuoted;
    } else if (character === "," && !isQuoted) {
      values.push(current.trim());
      current = "";
    } else {
      current += character;
    }
  }

  values.push(current.trim());
  return values;
}

function parseFlatImportCsv(content: string): FlatImportRowInput[] {
  const lines = content
    .replace(/^\uFEFF/, "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (!lines.length) {
    return [];
  }

  const headers = parseCsvLine(lines[0]).map((header) => header.trim().toLowerCase());
  return lines.slice(1).map((line) => {
    const values = parseCsvLine(line);
    const row = Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
    return {
      flat_number: row.flat_number || null,
      flat_type_code: row.flat_type_code || null,
      floor_label: row.floor_label || null,
      wing_code: row.wing_code || null
    };
  });
}

function parseChartOfAccountImportCsv(content: string): ChartOfAccountImportRowInput[] {
  const lines = content
    .replace(/^\uFEFF/, "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (!lines.length) {
    return [];
  }

  const headers = parseCsvLine(lines[0]).map((header) => header.trim().toLowerCase());
  return lines.slice(1).map((line) => {
    const values = parseCsvLine(line);
    const row = Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
    return {
      account_code: row.account_code || null,
      parent_account_code: row.parent_account_code || null,
      account_name: row.account_name || null,
      account_type: row.account_type || null,
      normal_balance: row.normal_balance || null,
      description: row.description || null
    };
  });
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

function tenantFromAccess(tenant: AccessTenant): Tenant {
  return {
    id: tenant.id,
    name: tenant.name,
    slug: tenant.slug,
    status: tenant.status,
    subscription_plan: "",
    billing_email: null,
    phone: null,
    timezone: "",
    locale: "",
    currency: "",
    metadata: {},
    created_at: "",
    updated_at: ""
  };
}

function societyFromAccess(society: AccessSociety): Society {
  return {
    id: society.id,
    tenant_id: society.tenant_id,
    name: society.name,
    registration_number: null,
    address_line1: null,
    address_line2: null,
    city: null,
    state: null,
    postal_code: null,
    country: "",
    timezone: "",
    locale: "",
    currency: "",
    financial_year_start_month: 4,
    receivable_account_id: null,
    payable_account_id: null,
    member_advance_account_id: null,
    status: society.status,
    created_at: "",
    updated_at: ""
  };
}

function App() {
  const storedContext = useMemo(readStoredAdminContext, []);
  const [sessionState, setSessionState] = useState<SessionState>("loading");
  const [token, setToken] = useState("");
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [myAccess, setMyAccess] = useState<MyAccess | null>(null);
  const [workspace, setWorkspace] = useState<Workspace>(storedContext.workspace ?? "dashboard");
  const [formWorkspace, setFormWorkspace] = useState<Workspace | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({
    platform: true,
    society: true,
    building: true,
    flat: true,
    billing: true,
    reports: false
  });
  const [reasonDialog, setReasonDialog] = useState<ReasonDialogState | null>(null);
  const [reasonDialogText, setReasonDialogText] = useState("");

  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [selectedTenantId, setSelectedTenantId] = useState(storedContext.tenantId ?? "");
  const [tenantForm, setTenantForm] = useState(tenantFormDefaults);
  const [editingTenantId, setEditingTenantId] = useState<string | null>(null);
  const [isLoadingTenants, setIsLoadingTenants] = useState(false);
  const [managedUsers, setManagedUsers] = useState<ManagedUser[]>([]);
  const [managedUserForm, setManagedUserForm] = useState(managedUserFormDefaults);
  const [isLoadingManagedUsers, setIsLoadingManagedUsers] = useState(false);

  const [societies, setSocieties] = useState<Society[]>([]);
  const [selectedSocietyId, setSelectedSocietyId] = useState(storedContext.societyId ?? "");
  const [societyForm, setSocietyForm] = useState(societyFormDefaults);
  const [editingSocietyId, setEditingSocietyId] = useState<string | null>(null);
  const [isLoadingSocieties, setIsLoadingSocieties] = useState(false);

  const [buildings, setBuildings] = useState<Building[]>([]);
  const [selectedBuildingId, setSelectedBuildingId] = useState(storedContext.buildingId ?? "");
  const [buildingForm, setBuildingForm] = useState(buildingFormDefaults);
  const [editingBuildingId, setEditingBuildingId] = useState<string | null>(null);
  const [isLoadingBuildings, setIsLoadingBuildings] = useState(false);

  const [buildingFloors, setBuildingFloors] = useState<BuildingFloor[]>([]);
  const [buildingFloorForm, setBuildingFloorForm] = useState(buildingFloorFormDefaults);
  const [editingBuildingFloorId, setEditingBuildingFloorId] = useState<string | null>(null);
  const [isLoadingBuildingFloors, setIsLoadingBuildingFloors] = useState(false);

  const [flatTypes, setFlatTypes] = useState<FlatType[]>([]);
  const [flatTypeForm, setFlatTypeForm] = useState(flatTypeFormDefaults);
  const [editingFlatTypeId, setEditingFlatTypeId] = useState<string | null>(null);
  const [isLoadingFlatTypes, setIsLoadingFlatTypes] = useState(false);

  const [chargeTypes, setChargeTypes] = useState<ChargeType[]>([]);
  const [chargeTypeForm, setChargeTypeForm] = useState(chargeTypeFormDefaults);
  const [editingChargeTypeId, setEditingChargeTypeId] = useState<string | null>(null);
  const [isLoadingChargeTypes, setIsLoadingChargeTypes] = useState(false);
  const [expenseCategories, setExpenseCategories] = useState<ExpenseCategory[]>([]);
  const [expenseCategoryForm, setExpenseCategoryForm] = useState(expenseCategoryFormDefaults);
  const [editingExpenseCategoryId, setEditingExpenseCategoryId] = useState<string | null>(null);
  const [isLoadingExpenseCategories, setIsLoadingExpenseCategories] = useState(false);

  const [billingRules, setBillingRules] = useState<BillingRule[]>([]);
  const [billingRuleForm, setBillingRuleForm] = useState({
    ...billingRuleFormDefaults,
    effective_from: todayIsoDate()
  });
  const [editingBillingRuleId, setEditingBillingRuleId] = useState<string | null>(null);
  const [isLoadingBillingRules, setIsLoadingBillingRules] = useState(false);
  const [lateFeeRules, setLateFeeRules] = useState<LateFeeRule[]>([]);
  const [lateFeeRuleForm, setLateFeeRuleForm] = useState({
    ...lateFeeRuleFormDefaults,
    effective_from: todayIsoDate()
  });
  const [editingLateFeeRuleId, setEditingLateFeeRuleId] = useState<string | null>(null);
  const [isLoadingLateFeeRules, setIsLoadingLateFeeRules] = useState(false);
  const [lateFeeApplicationForm, setLateFeeApplicationForm] =
    useState<LateFeePreviewPayload>(lateFeeApplicationDefaults);
  const [lateFeePreview, setLateFeePreview] = useState<LateFeePreviewResponse | null>(null);
  const [scheduledJobFilters, setScheduledJobFilters] = useState(scheduledJobFilterDefaults);
  const [scheduledDueWork, setScheduledDueWork] = useState<ScheduledDueWork | null>(null);
  const [scheduledJobRuns, setScheduledJobRuns] = useState<ScheduledJobRun[]>([]);
  const [isLoadingScheduledJobs, setIsLoadingScheduledJobs] = useState(false);
  const [invoiceSequence, setInvoiceSequence] = useState<DocumentSequence | null>(null);
  const [invoiceSequenceForm, setInvoiceSequenceForm] = useState(invoiceSequenceFormDefaults);
  const [isLoadingInvoiceSequence, setIsLoadingInvoiceSequence] = useState(false);

  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [invoiceTotalItems, setInvoiceTotalItems] = useState(0);
  const [invoiceTotalPages, setInvoiceTotalPages] = useState(0);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const [selectedInvoiceDetail, setSelectedInvoiceDetail] = useState<InvoiceDetail | null>(null);
  const [selectedInvoiceIds, setSelectedInvoiceIds] = useState<string[]>([]);
  const [isLoadingInvoices, setIsLoadingInvoices] = useState(false);
  const [invoiceFilters, setInvoiceFilters] = useState(invoiceFilterDefaults);
  const [invoiceGenerationForm, setInvoiceGenerationForm] = useState<InvoiceGenerationPayload>(
    currentMonthInvoiceGenerationDefaults
  );
  const [invoiceGenerationPreview, setInvoiceGenerationPreview] =
    useState<InvoiceGenerationPreviewResponse | null>(null);
  const [manualInvoiceForm, setManualInvoiceForm] = useState({
    ...manualInvoiceFormDefaults,
    invoice_date: todayIsoDate(),
    due_date: todayIsoDate(),
    billing_period_start: todayIsoDate(),
    billing_period_end: todayIsoDate()
  });
  const [paymentForm, setPaymentForm] = useState({
    ...paymentFormDefaults,
    payment_date: todayIsoDate()
  });
  const [paymentOpenInvoiceRows, setPaymentOpenInvoiceRows] = useState<Invoice[]>([]);
  const [isLoadingPaymentOpenInvoices, setIsLoadingPaymentOpenInvoices] = useState(false);
  const [paymentAllocations, setPaymentAllocations] = useState<Record<string, string>>({});
  const [lastPaymentResult, setLastPaymentResult] = useState<{
    payment: PaymentDetail;
    invoices: Invoice[];
  } | null>(null);
  const [paymentRegisterRows, setPaymentRegisterRows] = useState<PaymentRegisterRow[]>([]);
  const [paymentRegisterFilters, setPaymentRegisterFilters] = useState(paymentRegisterFilterDefaults);
  const [paymentRegisterTotalItems, setPaymentRegisterTotalItems] = useState(0);
  const [paymentRegisterTotalPages, setPaymentRegisterTotalPages] = useState(0);
  const [isLoadingPaymentRegister, setIsLoadingPaymentRegister] = useState(false);
  const [outstandingAsOfDate, setOutstandingAsOfDate] = useState(todayIsoDate());
  const [outstandingSummary, setOutstandingSummary] = useState<OutstandingSummary | null>(null);
  const [isLoadingOutstanding, setIsLoadingOutstanding] = useState(false);

  const [chartOfAccounts, setChartOfAccounts] = useState<ChartOfAccount[]>([]);
  const [chartOfAccountForm, setChartOfAccountForm] = useState(chartOfAccountFormDefaults);
  const [editingChartOfAccountId, setEditingChartOfAccountId] = useState<string | null>(null);
  const [isLoadingChartOfAccounts, setIsLoadingChartOfAccounts] = useState(false);
  const [isChartOfAccountImportOpen, setIsChartOfAccountImportOpen] = useState(false);
  const [chartOfAccountImportFileName, setChartOfAccountImportFileName] = useState("");
  const [chartOfAccountImportRows, setChartOfAccountImportRows] = useState<
    ChartOfAccountImportRowInput[]
  >([]);
  const [chartOfAccountImportPreview, setChartOfAccountImportPreview] =
    useState<ChartOfAccountImportPreviewResponse | null>(null);
  const [journals, setJournals] = useState<JournalEntry[]>([]);
  const [selectedOpeningBalanceDetail, setSelectedOpeningBalanceDetail] =
    useState<JournalEntryDetail | null>(null);
  const [journalForm, setJournalForm] = useState(journalFormDefaults);
  const [isLoadingJournals, setIsLoadingJournals] = useState(false);
  const [bankCashAccountForm, setBankCashAccountForm] = useState(bankCashAccountFormDefaults);
  const [openingBalanceForm, setOpeningBalanceForm] = useState(openingBalanceFormDefaults);
  const [accountTransfers, setAccountTransfers] = useState<AccountTransfer[]>([]);
  const [accountTransferForm, setAccountTransferForm] = useState({
    ...accountTransferFormDefaults,
    transfer_date: todayIsoDate()
  });
  const [isLoadingAccountTransfers, setIsLoadingAccountTransfers] = useState(false);
  const [otherIncomeReceipts, setOtherIncomeReceipts] = useState<OtherIncomeReceipt[]>([]);
  const [otherIncomeForm, setOtherIncomeForm] = useState({
    ...otherIncomeFormDefaults,
    receipt_date: todayIsoDate()
  });
  const [isLoadingOtherIncomeReceipts, setIsLoadingOtherIncomeReceipts] = useState(false);
  const [accountLedgerFilters, setAccountLedgerFilters] = useState(accountLedgerFilterDefaults);
  const [accountLedger, setAccountLedger] = useState<AccountLedger | null>(null);
  const [isLoadingAccountLedger, setIsLoadingAccountLedger] = useState(false);
  const [flatLedgerFilters, setFlatLedgerFilters] = useState(flatLedgerFilterDefaults);
  const [flatLedger, setFlatLedger] = useState<FlatLedger | null>(null);
  const [isLoadingFlatLedger, setIsLoadingFlatLedger] = useState(false);
  const [trialBalanceFilters, setTrialBalanceFilters] = useState(trialBalanceFilterDefaults);
  const [trialBalance, setTrialBalance] = useState<TrialBalance | null>(null);
  const [isLoadingTrialBalance, setIsLoadingTrialBalance] = useState(false);
  const [incomeExpenseFilters, setIncomeExpenseFilters] = useState(incomeExpenseFilterDefaults);
  const [incomeExpenseReport, setIncomeExpenseReport] = useState<IncomeExpenseReport | null>(null);
  const [isLoadingIncomeExpense, setIsLoadingIncomeExpense] = useState(false);
  const [balanceSheetFilters, setBalanceSheetFilters] = useState(balanceSheetFilterDefaults);
  const [balanceSheetReport, setBalanceSheetReport] = useState<BalanceSheetReport | null>(null);
  const [isLoadingBalanceSheet, setIsLoadingBalanceSheet] = useState(false);
  const [operationalReportType, setOperationalReportType] = useState<OperationalReportType>("billing");
  const [operationalReportFilters, setOperationalReportFilters] = useState({
    period_start: todayIsoDate().slice(0, 8) + "01",
    period_end: todayIsoDate(),
    as_of_date: todayIsoDate()
  });
  const [operationalReport, setOperationalReport] = useState<OperationalReportResult | null>(null);
  const [isLoadingOperationalReport, setIsLoadingOperationalReport] = useState(false);

  const [wings, setWings] = useState<Wing[]>([]);
  const [wingForm, setWingForm] = useState(wingFormDefaults);
  const [editingWingId, setEditingWingId] = useState<string | null>(null);
  const [isLoadingWings, setIsLoadingWings] = useState(false);

  const [flats, setFlats] = useState<Flat[]>([]);
  const [selectedFlatId, setSelectedFlatId] = useState(storedContext.flatId ?? "");
  const [flatForm, setFlatForm] = useState(flatFormDefaults);
  const [editingFlatId, setEditingFlatId] = useState<string | null>(null);
  const [isLoadingFlats, setIsLoadingFlats] = useState(false);
  const [isFlatImportOpen, setIsFlatImportOpen] = useState(false);
  const [flatImportFileName, setFlatImportFileName] = useState("");
  const [flatImportRows, setFlatImportRows] = useState<FlatImportRowInput[]>([]);
  const [flatImportPreview, setFlatImportPreview] = useState<FlatImportPreviewResponse | null>(null);

  const [ownerships, setOwnerships] = useState<FlatOwnership[]>([]);
  const [ownershipForm, setOwnershipForm] = useState(ownershipFormDefaults);
  const [editingOwnershipId, setEditingOwnershipId] = useState<string | null>(null);
  const [isLoadingOwnerships, setIsLoadingOwnerships] = useState(false);

  const [residents, setResidents] = useState<Resident[]>([]);
  const [residentForm, setResidentForm] = useState(residentFormDefaults);
  const [editingResidentId, setEditingResidentId] = useState<string | null>(null);
  const [isLoadingResidents, setIsLoadingResidents] = useState(false);
  const [leaseAgreements, setLeaseAgreements] = useState<LeaseAgreement[]>([]);
  const [leaseAgreementForm, setLeaseAgreementForm] = useState(leaseAgreementFormDefaults);
  const [editingLeaseAgreementId, setEditingLeaseAgreementId] = useState<string | null>(null);
  const [isLoadingLeaseAgreements, setIsLoadingLeaseAgreements] = useState(false);

  const [owners, setOwners] = useState<Owner[]>([]);
  const [ownerForm, setOwnerForm] = useState(ownerFormDefaults);
  const [editingOwnerId, setEditingOwnerId] = useState<string | null>(null);
  const [isLoadingOwners, setIsLoadingOwners] = useState(false);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [vendorForm, setVendorForm] = useState(vendorFormDefaults);
  const [editingVendorId, setEditingVendorId] = useState<string | null>(null);
  const [isLoadingVendors, setIsLoadingVendors] = useState(false);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [expenseForm, setExpenseForm] = useState({
    ...expenseFormDefaults,
    expense_date: todayIsoDate(),
    due_date: todayIsoDate()
  });
  const [editingExpenseId, setEditingExpenseId] = useState<string | null>(null);
  const [isLoadingExpenses, setIsLoadingExpenses] = useState(false);
  const [expensePayments, setExpensePayments] = useState<ExpensePayment[]>([]);
  const [expensePaymentForm, setExpensePaymentForm] = useState({
    ...expensePaymentFormDefaults,
    payment_date: todayIsoDate()
  });
  const [expensePaymentAllocations, setExpensePaymentAllocations] = useState<Record<string, string>>({});
  const [isLoadingExpensePayments, setIsLoadingExpensePayments] = useState(false);

  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const parsedToken = keycloak.tokenParsed as { email?: string; name?: string } | undefined;
  const userName = currentUser?.full_name ?? parsedToken?.name ?? parsedToken?.email ?? "Platform user";
  const selectedTenant = tenants.find((tenant) => tenant.id === selectedTenantId) ?? null;
  const tenantSocieties = societies.filter((society) => society.tenant_id === selectedTenantId);
  const selectedSociety = tenantSocieties.find((society) => society.id === selectedSocietyId) ?? null;
  const selectedTenantSocietyId = selectedSociety ? selectedSocietyId : "";
  const selectedBuilding = buildings.find((building) => building.id === selectedBuildingId) ?? null;
  const selectedFlat = flats.find((flat) => flat.id === selectedFlatId) ?? null;
  const isPlatformUser = Boolean(myAccess?.is_platform_superuser);
  const selectedTenantRoles =
    myAccess?.tenants.find((tenant) => tenant.id === selectedTenantId)?.roles ?? [];
  const canManageTenantSocieties = isPlatformUser || selectedTenantRoles.includes("tenant_admin");
  const canManageUsers =
    isPlatformUser ||
    selectedTenantRoles.includes("tenant_admin") ||
    Boolean(
      myAccess?.societies.some(
        (society) => society.tenant_id === selectedTenantId && society.roles.includes("society_admin")
      )
    );
  const userRoleLabel = isPlatformUser
    ? "Platform Superuser"
    : selectedTenantRoles.includes("tenant_admin")
      ? "Tenant Admin"
      : myAccess?.societies.some((society) => society.roles.includes("society_admin"))
        ? "Society Admin"
        : "User";
  const showBuildingContext = ["floors", "wings", "flats", "ownerships", "residents", "leaseAgreements"].includes(
    workspace
  );
  const showFlatContext = ["ownerships", "residents", "leaseAgreements"].includes(workspace);
  const breadcrumbParts =
    workspace === "tenants"
      ? ["Platform Administration"]
      : workspace === "users"
        ? [selectedTenant?.name]
      : workspace === "dashboard"
        ? ["Society Dashboard"]
      : workspace === "societies"
        ? [selectedTenant?.name]
      : [
          "buildings",
          "flatTypes",
          "chartOfAccounts",
          "bankCashAccounts",
          "accountLedgers",
          "openingBalances",
          "trialBalance",
          "incomeExpense",
          "balanceSheet",
          "paymentRegister",
          "journals",
          "accountTransfers",
          "otherIncome",
          "chargeTypes",
          "expenseCategories",
          "expenses",
          "numberingSettings",
          "billingRules",
          "lateFeeRules",
          "lateFeeApplication",
          "scheduledJobs",
          "invoiceGeneration",
          "manualInvoices",
          "invoices",
          "payments",
          "outstanding",
          "vendors",
          "owners"
        ].includes(workspace)
        ? [selectedTenant?.name, selectedSociety?.name]
      : ["floors", "wings", "flats"].includes(workspace)
        ? [selectedTenant?.name, selectedSociety?.name, selectedBuilding?.name]
      : ["ownerships", "residents", "leaseAgreements"].includes(workspace)
        ? [selectedTenant?.name, selectedSociety?.name, selectedBuilding?.name, selectedFlat?.flat_number]
      : [selectedTenant?.name, selectedSociety?.name];
  const breadcrumbLabel = breadcrumbParts.filter(Boolean).join(" / ") || "Tenant";
  const isTenantFormOpen = formWorkspace === "tenants" || Boolean(editingTenantId);
  const isManagedUserFormOpen = formWorkspace === "users";
  const isSocietyFormOpen = formWorkspace === "societies" || Boolean(editingSocietyId);
  const isBuildingFormOpen = formWorkspace === "buildings" || Boolean(editingBuildingId);
  const isBuildingFloorFormOpen = formWorkspace === "floors" || Boolean(editingBuildingFloorId);
  const isFlatTypeFormOpen = formWorkspace === "flatTypes" || Boolean(editingFlatTypeId);
  const isChartOfAccountFormOpen =
    formWorkspace === "chartOfAccounts" || Boolean(editingChartOfAccountId);
  const isBankCashAccountFormOpen = formWorkspace === "bankCashAccounts";
  const isOpeningBalanceFormOpen = formWorkspace === "openingBalances";
  const isJournalFormOpen = formWorkspace === "journals";
  const isAccountTransferFormOpen = formWorkspace === "accountTransfers";
  const isOtherIncomeFormOpen = formWorkspace === "otherIncome";
  const isChargeTypeFormOpen = formWorkspace === "chargeTypes" || Boolean(editingChargeTypeId);
  const isExpenseCategoryFormOpen =
    formWorkspace === "expenseCategories" || Boolean(editingExpenseCategoryId);
  const isExpenseFormOpen = formWorkspace === "expenses" || Boolean(editingExpenseId);
  const isBillingRuleFormOpen = formWorkspace === "billingRules" || Boolean(editingBillingRuleId);
  const isLateFeeRuleFormOpen = formWorkspace === "lateFeeRules" || Boolean(editingLateFeeRuleId);
  const isWingFormOpen = formWorkspace === "wings" || Boolean(editingWingId);
  const isFlatFormOpen = formWorkspace === "flats" || Boolean(editingFlatId);
  const isOwnerFormOpen = formWorkspace === "owners" || Boolean(editingOwnerId);
  const isVendorFormOpen = formWorkspace === "vendors" || Boolean(editingVendorId);
  const isOwnershipFormOpen = formWorkspace === "ownerships" || Boolean(editingOwnershipId);
  const isResidentFormOpen = formWorkspace === "residents" || Boolean(editingResidentId);
  const isLeaseAgreementFormOpen =
    formWorkspace === "leaseAgreements" || Boolean(editingLeaseAgreementId);
  const isCurrentFormOpen =
    (workspace === "tenants" && isTenantFormOpen) ||
    (workspace === "users" && isManagedUserFormOpen) ||
    (workspace === "societies" && isSocietyFormOpen) ||
    (workspace === "buildings" && isBuildingFormOpen) ||
    (workspace === "floors" && isBuildingFloorFormOpen) ||
    (workspace === "flatTypes" && isFlatTypeFormOpen) ||
    (workspace === "chartOfAccounts" && isChartOfAccountFormOpen) ||
    (workspace === "bankCashAccounts" && isBankCashAccountFormOpen) ||
    (workspace === "openingBalances" && isOpeningBalanceFormOpen) ||
    (workspace === "journals" && isJournalFormOpen) ||
    (workspace === "accountTransfers" && isAccountTransferFormOpen) ||
    (workspace === "otherIncome" && isOtherIncomeFormOpen) ||
    (workspace === "chargeTypes" && isChargeTypeFormOpen) ||
    (workspace === "expenseCategories" && isExpenseCategoryFormOpen) ||
    (workspace === "expenses" && isExpenseFormOpen) ||
    (workspace === "billingRules" && isBillingRuleFormOpen) ||
    (workspace === "lateFeeRules" && isLateFeeRuleFormOpen) ||
    (workspace === "wings" && isWingFormOpen) ||
    (workspace === "flats" && isFlatFormOpen) ||
    (workspace === "owners" && isOwnerFormOpen) ||
    (workspace === "vendors" && isVendorFormOpen) ||
    (workspace === "ownerships" && isOwnershipFormOpen) ||
    (workspace === "residents" && isResidentFormOpen) ||
    (workspace === "leaseAgreements" && isLeaseAgreementFormOpen);
  const createActionLabel =
    workspace === "tenants"
      ? "Add Tenant"
      : workspace === "users"
        ? "Add User"
      : workspace === "societies"
        ? "Add Society"
        : workspace === "buildings"
          ? "Add Building"
          : workspace === "floors"
            ? "Add Floor"
            : workspace === "flatTypes"
              ? "Add Flat Type"
              : workspace === "chartOfAccounts"
                ? "Add Account"
                : workspace === "bankCashAccounts"
                  ? "Add Bank/Cash Account"
                : workspace === "openingBalances"
                  ? "Add Opening Balance"
                : workspace === "journals"
                  ? "Add Journal"
                  : workspace === "accountTransfers"
                    ? "Add Transfer"
                    : workspace === "otherIncome"
                      ? "Add Receipt"
                    : workspace === "chargeTypes"
                      ? "Add Charge Type"
                : workspace === "expenseCategories"
                  ? "Add Expense Category"
                : workspace === "expenses"
                  ? "Add Expense"
                : workspace === "numberingSettings"
                  ? ""
                : workspace === "billingRules"
                  ? "Add Billing Rule"
                : workspace === "lateFeeRules"
                  ? "Add Penalty Rule"
                  : workspace === "wings"
                    ? "Add Wing"
                    : workspace === "flats"
                      ? "Add Flat"
                      : workspace === "owners"
                        ? "Add Owner"
                      : workspace === "vendors"
                        ? "Add Vendor"
                        : workspace === "ownerships"
                          ? "Assign Owner"
                          : workspace === "residents"
                            ? "Add Resident"
                            : workspace === "leaseAgreements"
                              ? "Add Lease"
                            : "";
  const canOpenCurrentForm =
    (workspace === "tenants" && isPlatformUser) ||
    (workspace === "users" && canManageUsers && Boolean(selectedTenantId)) ||
    (workspace === "societies" && canManageTenantSocieties) ||
    (workspace === "buildings" && Boolean(selectedSocietyId)) ||
    (workspace === "flatTypes" && Boolean(selectedSocietyId)) ||
    (workspace === "chartOfAccounts" && Boolean(selectedSocietyId)) ||
    (workspace === "bankCashAccounts" && Boolean(selectedSocietyId)) ||
    (workspace === "openingBalances" && Boolean(selectedSocietyId)) ||
    (workspace === "journals" && Boolean(selectedSocietyId)) ||
    (workspace === "accountTransfers" && Boolean(selectedSocietyId)) ||
    (workspace === "otherIncome" && Boolean(selectedSocietyId)) ||
    (workspace === "chargeTypes" && Boolean(selectedSocietyId)) ||
    (workspace === "expenseCategories" && Boolean(selectedSocietyId)) ||
    (workspace === "expenses" && Boolean(selectedSocietyId)) ||
    (workspace === "numberingSettings" && Boolean(selectedSocietyId)) ||
    (workspace === "billingRules" && Boolean(selectedSocietyId)) ||
    (workspace === "lateFeeRules" && Boolean(selectedSocietyId)) ||
    (workspace === "scheduledJobs" && Boolean(selectedSocietyId)) ||
    (workspace === "invoiceGeneration" && Boolean(selectedSocietyId)) ||
    (workspace === "manualInvoices" && Boolean(selectedSocietyId)) ||
    (workspace === "invoices" && Boolean(selectedSocietyId)) ||
    (workspace === "payments" && Boolean(selectedSocietyId)) ||
    (workspace === "outstanding" && Boolean(selectedSocietyId)) ||
    (workspace === "owners" && Boolean(selectedSocietyId)) ||
    (workspace === "vendors" && Boolean(selectedSocietyId)) ||
    (workspace === "floors" && Boolean(selectedBuildingId)) ||
    (workspace === "wings" && Boolean(selectedBuildingId)) ||
    (workspace === "flats" && Boolean(selectedBuildingId)) ||
    (workspace === "ownerships" && Boolean(selectedFlatId)) ||
    (workspace === "residents" && Boolean(selectedFlatId)) ||
    (workspace === "leaseAgreements" && Boolean(selectedFlatId));

  const activeTenantCount = useMemo(
    () => tenants.filter((tenant) => tenant.status === "active").length,
    [tenants]
  );

  const activeSocietyCount = useMemo(
    () => societies.filter((society) => society.status === "active").length,
    [societies]
  );

  const activeBuildingCount = useMemo(
    () => buildings.filter((building) => building.status === "active").length,
    [buildings]
  );

  const activeBuildingFloorCount = useMemo(
    () => buildingFloors.filter((floor) => floor.status === "active").length,
    [buildingFloors]
  );

  const activeFlatTypeCount = useMemo(
    () => flatTypes.filter((flatType) => flatType.status === "active").length,
    [flatTypes]
  );

  const activeChargeTypeCount = useMemo(
    () => chargeTypes.filter((chargeType) => chargeType.status === "active").length,
    [chargeTypes]
  );

  const activeBillingRuleCount = useMemo(
    () => billingRules.filter((rule) => rule.status === "active").length,
    [billingRules]
  );

  const selectableBillingRules = useMemo(
    () =>
      billingRules.filter(
        (rule) => rule.status === "active" && rule.calculation_method !== "manual"
      ),
    [billingRules]
  );

  const openInvoiceCount = useMemo(
    () => invoices.filter((invoice) => !["paid", "cancelled"].includes(invoice.status)).length,
    [invoices]
  );

  const activeAssetAccounts = useMemo(
    () =>
      chartOfAccounts.filter(
        (account) => account.status === "active" && account.account_type === "asset"
      ),
    [chartOfAccounts]
  );
  const activeLiabilityAccounts = useMemo(
    () =>
      chartOfAccounts.filter(
        (account) => account.status === "active" && account.account_type === "liability"
      ),
    [chartOfAccounts]
  );
  const activeExpenseAccounts = useMemo(
    () =>
      chartOfAccounts.filter(
        (account) => account.status === "active" && account.account_type === "expense"
      ),
    [chartOfAccounts]
  );
  const activeIncomeAccounts = useMemo(
    () =>
      chartOfAccounts.filter(
        (account) => account.status === "active" && account.account_type === "income"
      ),
    [chartOfAccounts]
  );

  const paymentOpenInvoices = useMemo(
    () =>
      paymentOpenInvoiceRows
        .filter(
          (invoice) =>
            invoice.flat_id === paymentForm.flat_id &&
            !["paid", "cancelled"].includes(invoice.status) &&
            Number(invoice.amount_due) > 0
        )
        .sort((left, right) => {
          const dueDateComparison = left.due_date.localeCompare(right.due_date);
          if (dueDateComparison !== 0) {
            return dueDateComparison;
          }
          const invoiceDateComparison = left.invoice_date.localeCompare(right.invoice_date);
          if (invoiceDateComparison !== 0) {
            return invoiceDateComparison;
          }
          return left.invoice_number.localeCompare(right.invoice_number);
        }),
    [paymentOpenInvoiceRows, paymentForm.flat_id]
  );

  const paymentAllocatedTotal = useMemo(
    () =>
      Object.values(paymentAllocations).reduce(
        (total, value) => total + (Number(value) || 0),
        0
      ),
    [paymentAllocations]
  );
  const expensePaymentOpenExpenses = useMemo(
    () =>
      expenses.filter(
        (expense) =>
          expense.status !== "cancelled" &&
          expense.payment_status !== "paid" &&
          Number(expense.amount_due) > 0 &&
          (!expensePaymentForm.vendor_id || expense.vendor_id === expensePaymentForm.vendor_id)
      ),
    [expensePaymentForm.vendor_id, expenses]
  );
  const expensePaymentAllocatedTotal = useMemo(
    () =>
      Object.values(expensePaymentAllocations).reduce(
        (total, value) => total + (Number(value) || 0),
        0
      ),
    [expensePaymentAllocations]
  );

  const activeChartOfAccountCount = useMemo(
    () => chartOfAccounts.filter((account) => account.status === "active").length,
    [chartOfAccounts]
  );

  const activeJournalAccounts = useMemo(
    () => chartOfAccounts.filter((account) => account.status === "active"),
    [chartOfAccounts]
  );

  const bankCashAccounts = useMemo(
    () => chartOfAccounts.filter((account) => account.account_type === "asset"),
    [chartOfAccounts]
  );

  const journalDebitTotal = useMemo(
    () =>
      journalForm.lines.reduce(
        (total, line) => total + (Number(line.debit_amount) || 0),
        0
      ),
    [journalForm.lines]
  );

  const journalCreditTotal = useMemo(
    () =>
      journalForm.lines.reduce(
        (total, line) => total + (Number(line.credit_amount) || 0),
        0
      ),
    [journalForm.lines]
  );

  const isJournalBalanced =
    journalDebitTotal > 0 &&
    journalCreditTotal > 0 &&
    Math.round(journalDebitTotal * 100) === Math.round(journalCreditTotal * 100);

  const openingBalanceDebitTotal = useMemo(
    () =>
      openingBalanceForm.lines.reduce(
        (total, line) => total + (Number(line.debit_amount) || 0),
        0
      ),
    [openingBalanceForm.lines]
  );

  const openingBalanceCreditTotal = useMemo(
    () =>
      openingBalanceForm.lines.reduce(
        (total, line) => total + (Number(line.credit_amount) || 0),
        0
      ),
    [openingBalanceForm.lines]
  );

  const isOpeningBalanceBalanced =
    openingBalanceDebitTotal > 0 &&
    openingBalanceCreditTotal > 0 &&
    Math.round(openingBalanceDebitTotal * 100) === Math.round(openingBalanceCreditTotal * 100);

  const selectedTransferFromAccount =
    activeAssetAccounts.find((account) => account.id === accountTransferForm.from_account_id) ?? null;
  const selectedTransferToAccount =
    activeAssetAccounts.find((account) => account.id === accountTransferForm.to_account_id) ?? null;
  const selectedOtherIncomeAccount =
    activeIncomeAccounts.find((account) => account.id === otherIncomeForm.income_account_id) ?? null;
  const selectedOtherIncomeDepositAccount =
    activeAssetAccounts.find((account) => account.id === otherIncomeForm.deposit_account_id) ?? null;

  const incomeAccounts = useMemo(
    () =>
      chartOfAccounts.filter(
        (account) => account.status === "active" && account.account_type === "income"
      ),
    [chartOfAccounts]
  );
  const activeChargeTypes = useMemo(
    () => chargeTypes.filter((chargeType) => chargeType.status === "active"),
    [chargeTypes]
  );
  const activeLateFeeRules = useMemo(
    () => lateFeeRules.filter((rule) => rule.status === "active"),
    [lateFeeRules]
  );
  const activeBuildings = useMemo(
    () => buildings.filter((building) => building.status === "active"),
    [buildings]
  );
  const activeWings = useMemo(
    () => wings.filter((wing) => wing.status === "active"),
    [wings]
  );
  const activeFlatTypes = useMemo(
    () => flatTypes.filter((flatType) => flatType.status === "active"),
    [flatTypes]
  );
  const parentAccountOptions = useMemo(
    () =>
      chartOfAccounts.filter(
        (account) => account.status === "active" && account.id !== editingChartOfAccountId
      ),
    [chartOfAccounts, editingChartOfAccountId]
  );

  const activeWingCount = useMemo(
    () => wings.filter((wing) => wing.status === "active").length,
    [wings]
  );

  const activeFlatCount = useMemo(
    () => flats.filter((flat) => flat.status === "active").length,
    [flats]
  );

  const activeOwnerCount = useMemo(
    () => owners.filter((owner) => owner.status === "active").length,
    [owners]
  );

  const activeOwnershipCount = useMemo(
    () => ownerships.filter((ownership) => ownership.status === "active").length,
    [ownerships]
  );

  const activeResidentCount = useMemo(
    () => residents.filter((resident) => resident.status === "active").length,
    [residents]
  );

  useEffect(() => {
    if (sessionState !== "authenticated") {
      return;
    }

    storeAdminContext({
      workspace,
      tenantId: selectedTenantId,
      societyId: selectedSocietyId,
      buildingId: selectedBuildingId,
      flatId: selectedFlatId
    });
  }, [
    selectedBuildingId,
    selectedFlatId,
    selectedSocietyId,
    selectedTenantId,
    sessionState,
    workspace
  ]);

  useEffect(() => {
    let isMounted = true;

    initKeycloak()
      .then((authenticated) => {
        if (!isMounted) {
          return;
        }
        setSessionState(authenticated ? "authenticated" : "anonymous");
        setToken(keycloak.token ?? "");
      })
      .catch(() => {
        if (isMounted) {
          setError("Unable to connect to Keycloak.");
          setSessionState("anonymous");
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  async function refreshToken(): Promise<string> {
    await keycloak.updateToken(30);
    saveKeycloakTokens();
    const freshToken = keycloak.token ?? "";
    setToken(freshToken);
    return freshToken;
  }

  function openReasonDialog(dialog: ReasonDialogState) {
    setReasonDialog(dialog);
    setReasonDialogText("");
    setError("");
    setNotice("");
  }

  function closeReasonDialog() {
    if (isSaving) {
      return;
    }
    setReasonDialog(null);
    setReasonDialogText("");
  }

  async function handleReasonDialogSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!reasonDialog) {
      return;
    }
    const reason = reasonDialogText.trim();
    if (reason.length < 3) {
      setError("Reason must be at least 3 characters.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      await reasonDialog.onConfirm(reason);
      setReasonDialog(null);
      setReasonDialogText("");
    } catch (err) {
      setError(err instanceof Error ? err.message : reasonDialog.errorMessage);
    } finally {
      setIsSaving(false);
    }
  }

  const refreshTenants = useCallback(async (authToken = token) => {
    setIsLoadingTenants(true);
    setError("");
    try {
      if (myAccess && !myAccess.is_platform_superuser) {
        const rows = myAccess.tenants.map(tenantFromAccess);
        setTenants(rows);
        setSelectedTenantId((current) => {
          if (current && rows.some((tenant) => tenant.id === current)) {
            return current;
          }
          return rows[0]?.id ?? "";
        });
        return;
      }
      const rows = await listTenants(authToken);
      setTenants(rows);
      setSelectedTenantId((current) => {
        if (current && rows.some((tenant) => tenant.id === current)) {
          return current;
        }
        return rows[0]?.id ?? "";
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load tenants.");
    } finally {
      setIsLoadingTenants(false);
    }
  }, [myAccess, token]);

  const refreshManagedUsers = useCallback(async (tenantId = selectedTenantId, authToken = token) => {
    if (!tenantId || !canManageUsers) {
      setManagedUsers([]);
      return;
    }

    setIsLoadingManagedUsers(true);
    setError("");
    try {
      setManagedUsers(await listManagedUsers(authToken, tenantId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load users.");
    } finally {
      setIsLoadingManagedUsers(false);
    }
  }, [canManageUsers, selectedTenantId, token]);

  const refreshSocieties = useCallback(async (tenantId = selectedTenantId, authToken = token) => {
    if (!tenantId) {
      setSocieties([]);
      return;
    }

    setIsLoadingSocieties(true);
    setError("");
    try {
      let rows: Society[];
      if (myAccess && !myAccess.is_platform_superuser && !canManageTenantSocieties) {
        rows = myAccess.societies
          .filter((society) => society.tenant_id === tenantId)
          .map(societyFromAccess);
      } else {
        rows = await listSocieties(authToken, tenantId);
      }
      setSocieties(rows);
      setSelectedSocietyId((current) => {
        if (current && rows.some((society) => society.id === current)) {
          return current;
        }
        return rows[0]?.id ?? "";
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load societies.");
    } finally {
      setIsLoadingSocieties(false);
    }
  }, [canManageTenantSocieties, myAccess, selectedTenantId, token]);

  const refreshBuildings = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setBuildings([]);
      setSelectedBuildingId("");
      setBuildingFloors([]);
      setWings([]);
      setFlats([]);
      setSelectedFlatId("");
      setOwnerships([]);
      setResidents([]);
      setLeaseAgreements([]);
      return;
    }

    setIsLoadingBuildings(true);
    setError("");
    try {
      const rows = await listBuildings(authToken, tenantId, societyId);
      setBuildings(rows);
      setSelectedBuildingId((current) => {
        if (current && rows.some((building) => building.id === current)) {
          return current;
        }
        return rows[0]?.id ?? "";
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load buildings.");
    } finally {
      setIsLoadingBuildings(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshFlatTypes = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setFlatTypes([]);
      return;
    }

    setIsLoadingFlatTypes(true);
    setError("");
    try {
      setFlatTypes(await listFlatTypes(authToken, tenantId, societyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load flat types.");
    } finally {
      setIsLoadingFlatTypes(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshChargeTypes = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setChargeTypes([]);
      return;
    }

    setIsLoadingChargeTypes(true);
    setError("");
    try {
      setChargeTypes(await listChargeTypes(authToken, tenantId, societyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load charge types.");
    } finally {
      setIsLoadingChargeTypes(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshExpenseCategories = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setExpenseCategories([]);
      return;
    }

    setIsLoadingExpenseCategories(true);
    setError("");
    try {
      setExpenseCategories(await listExpenseCategories(authToken, tenantId, societyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load expense categories.");
    } finally {
      setIsLoadingExpenseCategories(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshBillingRules = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setBillingRules([]);
      return;
    }

    setIsLoadingBillingRules(true);
    setError("");
    try {
      setBillingRules(await listBillingRules(authToken, tenantId, societyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load billing rules.");
    } finally {
      setIsLoadingBillingRules(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshLateFeeRules = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setLateFeeRules([]);
      return;
    }

    setIsLoadingLateFeeRules(true);
    setError("");
    try {
      setLateFeeRules(await listLateFeeRules(authToken, tenantId, societyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load late fee rules.");
    } finally {
      setIsLoadingLateFeeRules(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshScheduledJobs = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setScheduledDueWork(null);
      setScheduledJobRuns([]);
      return;
    }

    setIsLoadingScheduledJobs(true);
    setError("");
    try {
      const [dueWork, runs] = await Promise.all([
        getScheduledDueWork(authToken, tenantId, societyId, scheduledJobFilters.as_of_date),
        listScheduledJobRuns(authToken, tenantId, societyId)
      ]);
      setScheduledDueWork(dueWork);
      setScheduledJobRuns(runs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load scheduled jobs.");
    } finally {
      setIsLoadingScheduledJobs(false);
    }
  }, [scheduledJobFilters.as_of_date, selectedSocietyId, selectedTenantId, token]);

  const refreshInvoiceSequence = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setInvoiceSequence(null);
      setInvoiceSequenceForm(invoiceSequenceFormDefaults);
      return;
    }

    setIsLoadingInvoiceSequence(true);
    setError("");
    try {
      const sequence = await getInvoiceSequence(authToken, tenantId, societyId);
      setInvoiceSequence(sequence);
      setInvoiceSequenceForm({
        prefix: sequence.prefix,
        include_period: sequence.include_period,
        include_financial_year: sequence.include_financial_year,
        separator: sequence.separator,
        next_sequence: sequence.next_sequence,
        padding: sequence.padding,
        reset_policy: sequence.reset_policy
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load invoice numbering.");
    } finally {
      setIsLoadingInvoiceSequence(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshInvoices = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token,
    filters = invoiceFilterDefaults
  ) => {
    if (!tenantId || !societyId) {
      setInvoices([]);
      setInvoiceTotalItems(0);
      setInvoiceTotalPages(0);
      setSelectedInvoiceId("");
      setSelectedInvoiceDetail(null);
      return;
    }

    setIsLoadingInvoices(true);
    setError("");
    try {
      const requestFilters: InvoiceListFilters = {
        flat_id: filters.flat_id || undefined,
        status: filters.status || undefined,
        invoice_date_from: filters.invoice_date_from || undefined,
        invoice_date_to: filters.invoice_date_to || undefined,
        due_date_from: filters.due_date_from || undefined,
        due_date_to: filters.due_date_to || undefined,
        page: filters.page,
        page_size: filters.page_size
      };
      const response = await listInvoices(authToken, tenantId, societyId, requestFilters);
      const rows = response.items;
      setInvoices(rows);
      setSelectedInvoiceIds((current) => current.filter((invoiceId) => rows.some((invoice) => invoice.id === invoiceId)));
      setInvoiceTotalItems(response.total_items);
      setInvoiceTotalPages(response.total_pages);
      setInvoiceFilters((current) =>
        current.page === response.page && current.page_size === response.page_size
          ? current
          : {
              ...current,
              page: response.page,
              page_size: response.page_size
            }
      );
      setSelectedInvoiceId((current) => {
        if (current && rows.some((invoice) => invoice.id === current)) {
          return current;
        }
        return "";
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load invoices.");
    } finally {
      setIsLoadingInvoices(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshPaymentRegister = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token,
    filters = paymentRegisterFilterDefaults
  ) => {
    if (!tenantId || !societyId) {
      setPaymentRegisterRows([]);
      setPaymentRegisterTotalItems(0);
      setPaymentRegisterTotalPages(0);
      return;
    }

    setIsLoadingPaymentRegister(true);
    setError("");
    try {
      const response = await listPaymentRegister(authToken, tenantId, societyId, {
        flat_number: filters.flat_number || undefined,
        status: filters.status || undefined,
        payment_mode: filters.payment_mode || undefined,
        payment_date_from: filters.payment_date_from || undefined,
        payment_date_to: filters.payment_date_to || undefined,
        page: filters.page,
        page_size: filters.page_size
      });
      setPaymentRegisterRows(response.items);
      setPaymentRegisterTotalItems(response.total_items);
      setPaymentRegisterTotalPages(response.total_pages);
      setPaymentRegisterFilters((current) =>
        current.page === response.page && current.page_size === response.page_size
          ? current
          : {
              ...current,
              page: response.page,
              page_size: response.page_size
            }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load payment register.");
    } finally {
      setIsLoadingPaymentRegister(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshPaymentOpenInvoices = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    flatId = paymentForm.flat_id,
    authToken = token
  ) => {
    if (!tenantId || !societyId || !flatId) {
      setPaymentOpenInvoiceRows([]);
      return;
    }

    setIsLoadingPaymentOpenInvoices(true);
    setError("");
    try {
      const firstPage = await listInvoices(authToken, tenantId, societyId, {
        flat_id: flatId,
        page: 1,
        page_size: 200
      });
      let rows = firstPage.items;
      for (let page = 2; page <= firstPage.total_pages; page += 1) {
        const response = await listInvoices(authToken, tenantId, societyId, {
          flat_id: flatId,
          page,
          page_size: 200
        });
        rows = [...rows, ...response.items];
      }
      setPaymentOpenInvoiceRows(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load open invoices for payment.");
      setPaymentOpenInvoiceRows([]);
    } finally {
      setIsLoadingPaymentOpenInvoices(false);
    }
  }, [paymentForm.flat_id, selectedSocietyId, selectedTenantId, token]);

  const refreshVendors = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setVendors([]);
      return;
    }

    setIsLoadingVendors(true);
    setError("");
    try {
      setVendors(await listVendors(authToken, tenantId, societyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load vendors.");
    } finally {
      setIsLoadingVendors(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshExpenses = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setExpenses([]);
      return;
    }

    setIsLoadingExpenses(true);
    setError("");
    try {
      setExpenses(await listExpenses(authToken, tenantId, societyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load expenses.");
    } finally {
      setIsLoadingExpenses(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshExpensePayments = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setExpensePayments([]);
      return;
    }

    setIsLoadingExpensePayments(true);
    setError("");
    try {
      setExpensePayments(await listExpensePayments(authToken, tenantId, societyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load expense payments.");
    } finally {
      setIsLoadingExpensePayments(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshOutstanding = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token,
    asOfDate = outstandingAsOfDate
  ) => {
    if (!tenantId || !societyId) {
      setOutstandingSummary(null);
      return;
    }

    setIsLoadingOutstanding(true);
    setError("");
    try {
      setOutstandingSummary(await getOutstandingSummary(authToken, tenantId, societyId, asOfDate));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load outstanding balances.");
    } finally {
      setIsLoadingOutstanding(false);
    }
  }, [outstandingAsOfDate, selectedSocietyId, selectedTenantId, token]);

  const refreshChartOfAccounts = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setChartOfAccounts([]);
      return;
    }

    setIsLoadingChartOfAccounts(true);
    setError("");
    try {
      setChartOfAccounts(await listChartOfAccounts(authToken, tenantId, societyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load chart of accounts.");
    } finally {
      setIsLoadingChartOfAccounts(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshJournals = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setJournals([]);
      return;
    }

    setIsLoadingJournals(true);
    setError("");
    try {
      setJournals(await listJournals(authToken, tenantId, societyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load journal entries.");
    } finally {
      setIsLoadingJournals(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshAccountTransfers = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setAccountTransfers([]);
      return;
    }

    setIsLoadingAccountTransfers(true);
    setError("");
    try {
      setAccountTransfers(await listAccountTransfers(authToken, tenantId, societyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load account transfers.");
    } finally {
      setIsLoadingAccountTransfers(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshOtherIncomeReceipts = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setOtherIncomeReceipts([]);
      return;
    }

    setIsLoadingOtherIncomeReceipts(true);
    setError("");
    try {
      setOtherIncomeReceipts(await listOtherIncomeReceipts(authToken, tenantId, societyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load other income receipts.");
    } finally {
      setIsLoadingOtherIncomeReceipts(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  const refreshAccountLedger = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token,
    filters = accountLedgerFilters
  ) => {
    if (!tenantId || !societyId || !filters.account_id) {
      setAccountLedger(null);
      return;
    }

    setIsLoadingAccountLedger(true);
    setError("");
    try {
      setAccountLedger(
        await getAccountLedger(
          authToken,
          tenantId,
          societyId,
          filters.account_id,
          filters.date_from || undefined,
          filters.date_to || undefined
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load account ledger.");
    } finally {
      setIsLoadingAccountLedger(false);
    }
  }, [accountLedgerFilters, selectedSocietyId, selectedTenantId, token]);

  const refreshFlatLedger = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token,
    filters = flatLedgerFilters
  ) => {
    if (!tenantId || !societyId || !filters.flat_id) {
      setFlatLedger(null);
      return;
    }

    setIsLoadingFlatLedger(true);
    setError("");
    try {
      setFlatLedger(
        await getFlatLedger(authToken, tenantId, societyId, filters.flat_id, {
          date_from: filters.date_from || undefined,
          date_to: filters.date_to || undefined
        })
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load flat ledger.");
    } finally {
      setIsLoadingFlatLedger(false);
    }
  }, [flatLedgerFilters, selectedSocietyId, selectedTenantId, token]);

  const refreshTrialBalance = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token,
    filters = trialBalanceFilters
  ) => {
    if (!tenantId || !societyId || !filters.as_of_date) {
      setTrialBalance(null);
      return;
    }

    setIsLoadingTrialBalance(true);
    setError("");
    try {
      setTrialBalance(await getTrialBalance(authToken, tenantId, societyId, filters.as_of_date));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load trial balance.");
    } finally {
      setIsLoadingTrialBalance(false);
    }
  }, [selectedSocietyId, selectedTenantId, token, trialBalanceFilters]);

  const refreshIncomeExpenseReport = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token,
    filters = incomeExpenseFilters
  ) => {
    if (!tenantId || !societyId || !filters.period_start || !filters.period_end) {
      setIncomeExpenseReport(null);
      return;
    }

    setIsLoadingIncomeExpense(true);
    setError("");
    try {
      setIncomeExpenseReport(
        await getIncomeExpenseReport(
          authToken,
          tenantId,
          societyId,
          filters.period_start,
          filters.period_end
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load income vs expense report.");
    } finally {
      setIsLoadingIncomeExpense(false);
    }
  }, [incomeExpenseFilters, selectedSocietyId, selectedTenantId, token]);

  const refreshBalanceSheetReport = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token,
    filters = balanceSheetFilters
  ) => {
    if (!tenantId || !societyId || !filters.as_of_date) {
      setBalanceSheetReport(null);
      setLateFeeRules([]);
      setLateFeePreview(null);
      setScheduledDueWork(null);
      setScheduledJobRuns([]);
      return;
    }

    setIsLoadingBalanceSheet(true);
    setError("");
    try {
      setBalanceSheetReport(
        await getBalanceSheetReport(authToken, tenantId, societyId, filters.as_of_date)
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load balance sheet.");
    } finally {
      setIsLoadingBalanceSheet(false);
    }
  }, [balanceSheetFilters, selectedSocietyId, selectedTenantId, token]);

  const refreshBuildingFloors = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    buildingId = selectedBuildingId,
    authToken = token
  ) => {
    if (!tenantId || !societyId || !buildingId) {
      setBuildingFloors([]);
      return;
    }

    setIsLoadingBuildingFloors(true);
    setError("");
    try {
      setBuildingFloors(await listBuildingFloors(authToken, tenantId, societyId, buildingId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load building floors.");
    } finally {
      setIsLoadingBuildingFloors(false);
    }
  }, [selectedBuildingId, selectedSocietyId, selectedTenantId, token]);

  const refreshWings = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    buildingId = selectedBuildingId,
    authToken = token
  ) => {
    if (!tenantId || !societyId || !buildingId) {
      setWings([]);
      return;
    }

    setIsLoadingWings(true);
    setError("");
    try {
      setWings(await listWings(authToken, tenantId, societyId, buildingId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load wings.");
    } finally {
      setIsLoadingWings(false);
    }
  }, [selectedBuildingId, selectedSocietyId, selectedTenantId, token]);

  const refreshFlats = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    buildingId = selectedBuildingId,
    authToken = token
  ) => {
    if (!tenantId || !societyId || !buildingId) {
      setFlats([]);
      setSelectedFlatId("");
      setOwnerships([]);
      setResidents([]);
      setLeaseAgreements([]);
      return;
    }

    setIsLoadingFlats(true);
    setError("");
    try {
      const rows = await listFlats(authToken, tenantId, societyId, buildingId);
      setFlats(rows);
      setSelectedFlatId((current) => {
        if (current && rows.some((flat) => flat.id === current)) {
          return current;
        }
        return rows[0]?.id ?? "";
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load flats.");
    } finally {
      setIsLoadingFlats(false);
    }
  }, [selectedBuildingId, selectedSocietyId, selectedTenantId, token]);

  const refreshOwnerships = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    buildingId = selectedBuildingId,
    flatId = selectedFlatId,
    authToken = token
  ) => {
    if (!tenantId || !societyId || !buildingId || !flatId) {
      setOwnerships([]);
      return;
    }

    setIsLoadingOwnerships(true);
    setError("");
    try {
      setOwnerships(await listFlatOwnerships(authToken, tenantId, societyId, buildingId, flatId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load flat ownerships.");
    } finally {
      setIsLoadingOwnerships(false);
    }
  }, [selectedBuildingId, selectedFlatId, selectedSocietyId, selectedTenantId, token]);

  const refreshResidents = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    buildingId = selectedBuildingId,
    flatId = selectedFlatId,
    authToken = token
  ) => {
    if (!tenantId || !societyId || !buildingId || !flatId) {
      setResidents([]);
      return;
    }

    setIsLoadingResidents(true);
    setError("");
    try {
      setResidents(await listResidents(authToken, tenantId, societyId, buildingId, flatId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load residents.");
    } finally {
      setIsLoadingResidents(false);
    }
  }, [selectedBuildingId, selectedFlatId, selectedSocietyId, selectedTenantId, token]);

  const refreshLeaseAgreements = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    buildingId = selectedBuildingId,
    flatId = selectedFlatId,
    authToken = token
  ) => {
    if (!tenantId || !societyId || !buildingId || !flatId) {
      setLeaseAgreements([]);
      return;
    }

    setIsLoadingLeaseAgreements(true);
    setError("");
    try {
      setLeaseAgreements(await listLeaseAgreements(authToken, tenantId, societyId, buildingId, flatId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load lease agreements.");
    } finally {
      setIsLoadingLeaseAgreements(false);
    }
  }, [selectedBuildingId, selectedFlatId, selectedSocietyId, selectedTenantId, token]);

  const refreshOwners = useCallback(async (
    tenantId = selectedTenantId,
    societyId = selectedSocietyId,
    authToken = token
  ) => {
    if (!tenantId || !societyId) {
      setOwners([]);
      return;
    }

    setIsLoadingOwners(true);
    setError("");
    try {
      setOwners(await listOwners(authToken, tenantId, societyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load owners.");
    } finally {
      setIsLoadingOwners(false);
    }
  }, [selectedSocietyId, selectedTenantId, token]);

  useEffect(() => {
    if (sessionState !== "authenticated" || !token) {
      return;
    }
    async function bootstrapAuthenticatedUser() {
      try {
        const [user, access] = await Promise.all([getCurrentUser(token), getMyAccess(token)]);
        setCurrentUser(user);
        setMyAccess(access);

        if (access.is_platform_superuser) {
          const rows = await listTenants(token);
          setTenants(rows);
          setSelectedTenantId((current) => {
            if (current && rows.some((tenant) => tenant.id === current)) {
              return current;
            }
            return rows[0]?.id ?? "";
          });
          return;
        }

        const accessibleTenants = access.tenants.map(tenantFromAccess);
        setTenants(accessibleTenants);
        setSelectedTenantId((current) => {
          if (current && accessibleTenants.some((tenant) => tenant.id === current)) {
            return current;
          }
          return accessibleTenants[0]?.id ?? "";
        });
        setWorkspace((current) =>
          current === "tenants" ? (access.societies.length ? "buildings" : "societies") : current
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load access.");
      }
    }

    void bootstrapAuthenticatedUser();
  }, [sessionState, token]);

  useEffect(() => {
    if (sessionState !== "authenticated" || !token || !selectedTenantId) {
      setManagedUsers([]);
      return;
    }
    void refreshManagedUsers(selectedTenantId, token);
    void refreshSocieties(selectedTenantId, token);
  }, [refreshManagedUsers, refreshSocieties, selectedTenantId, sessionState, token]);

  useEffect(() => {
    if (sessionState !== "authenticated" || !token || !selectedTenantId || !selectedSocietyId) {
      setOwners([]);
      setVendors([]);
      setExpenses([]);
      setExpensePayments([]);
      setChargeTypes([]);
      setExpenseCategories([]);
      setBillingRules([]);
      setInvoiceSequence(null);
      setInvoiceSequenceForm(invoiceSequenceFormDefaults);
      setInvoices([]);
      setPaymentRegisterRows([]);
      setPaymentRegisterTotalItems(0);
      setPaymentRegisterTotalPages(0);
      setSelectedInvoiceId("");
      setSelectedInvoiceDetail(null);
      setChartOfAccounts([]);
      setJournals([]);
      setSelectedOpeningBalanceDetail(null);
      setAccountTransfers([]);
      setOtherIncomeReceipts([]);
      setAccountLedger(null);
      setFlatLedger(null);
      setTrialBalance(null);
      setIncomeExpenseReport(null);
      setBalanceSheetReport(null);
      return;
    }
    void refreshBuildings(selectedTenantId, selectedSocietyId, token);
    void refreshOwners(selectedTenantId, selectedSocietyId, token);
    void refreshVendors(selectedTenantId, selectedSocietyId, token);
    void refreshExpenses(selectedTenantId, selectedSocietyId, token);
    void refreshExpensePayments(selectedTenantId, selectedSocietyId, token);
    void refreshFlatTypes(selectedTenantId, selectedSocietyId, token);
    void refreshChartOfAccounts(selectedTenantId, selectedSocietyId, token);
    void refreshJournals(selectedTenantId, selectedSocietyId, token);
    void refreshAccountTransfers(selectedTenantId, selectedSocietyId, token);
    void refreshOtherIncomeReceipts(selectedTenantId, selectedSocietyId, token);
    void refreshChargeTypes(selectedTenantId, selectedSocietyId, token);
    void refreshExpenseCategories(selectedTenantId, selectedSocietyId, token);
    void refreshBillingRules(selectedTenantId, selectedSocietyId, token);
    void refreshLateFeeRules(selectedTenantId, selectedSocietyId, token);
    void refreshScheduledJobs(selectedTenantId, selectedSocietyId, token);
    void refreshInvoiceSequence(selectedTenantId, selectedSocietyId, token);
    void refreshInvoices(selectedTenantId, selectedSocietyId, token);
    void refreshPaymentRegister(selectedTenantId, selectedSocietyId, token);
    void refreshOutstanding(selectedTenantId, selectedSocietyId, token);
  }, [
    refreshBillingRules,
    refreshLateFeeRules,
    refreshScheduledJobs,
    refreshAccountTransfers,
    refreshOtherIncomeReceipts,
    refreshBuildings,
    refreshChargeTypes,
    refreshChartOfAccounts,
    refreshExpenses,
    refreshExpensePayments,
    refreshFlatTypes,
    refreshExpenseCategories,
    refreshInvoiceSequence,
    refreshInvoices,
    refreshPaymentRegister,
    refreshJournals,
    refreshOutstanding,
    refreshOwners,
    refreshVendors,
    selectedSocietyId,
    selectedTenantId,
    sessionState,
    token
  ]);

  useEffect(() => {
    setAccountLedger(null);
    setAccountLedgerFilters(accountLedgerFilterDefaults);
    setPaymentRegisterRows([]);
    setPaymentRegisterFilters(paymentRegisterFilterDefaults);
    setPaymentRegisterTotalItems(0);
    setPaymentRegisterTotalPages(0);
    setFlatLedger(null);
    setFlatLedgerFilters(flatLedgerFilterDefaults);
    setTrialBalance(null);
    setTrialBalanceFilters(trialBalanceFilterDefaults);
    setIncomeExpenseReport(null);
    setIncomeExpenseFilters(incomeExpenseFilterDefaults);
    setBalanceSheetReport(null);
    setBalanceSheetFilters(balanceSheetFilterDefaults);
    setSelectedOpeningBalanceDetail(null);
  }, [selectedSocietyId, selectedTenantId]);

  useEffect(() => {
    if (
      sessionState !== "authenticated" ||
      !token ||
      !selectedTenantId ||
      !selectedSocietyId ||
      !selectedInvoiceId
    ) {
      setSelectedInvoiceDetail(null);
      return;
    }

    async function loadInvoiceDetail() {
      try {
        setSelectedInvoiceDetail(
          await getInvoice(token, selectedTenantId, selectedSocietyId, selectedInvoiceId)
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load invoice detail.");
      }
    }

    void loadInvoiceDetail();
  }, [selectedInvoiceId, selectedSocietyId, selectedTenantId, sessionState, token]);

  useEffect(() => {
    if (
      sessionState !== "authenticated" ||
      !token ||
      !selectedTenantId ||
      !selectedSocietyId ||
      !selectedBuildingId
    ) {
      setWings([]);
      setBuildingFloors([]);
      setFlats([]);
      return;
    }
    void refreshBuildingFloors(selectedTenantId, selectedSocietyId, selectedBuildingId, token);
    void refreshWings(selectedTenantId, selectedSocietyId, selectedBuildingId, token);
  }, [
    refreshBuildingFloors,
    refreshWings,
    selectedBuildingId,
    selectedSocietyId,
    selectedTenantId,
    sessionState,
    token
  ]);

  useEffect(() => {
    if (
      sessionState !== "authenticated" ||
      !token ||
      !selectedTenantId ||
      !selectedSocietyId ||
      !selectedBuildingId
    ) {
      setFlats([]);
      setSelectedFlatId("");
      setOwnerships([]);
      setResidents([]);
      setLeaseAgreements([]);
      return;
    }
    void refreshFlats(selectedTenantId, selectedSocietyId, selectedBuildingId, token);
  }, [
    refreshFlats,
    selectedBuildingId,
    selectedSocietyId,
    selectedTenantId,
    sessionState,
    token
  ]);

  useEffect(() => {
    if (
      sessionState !== "authenticated" ||
      !token ||
      !selectedTenantId ||
      !selectedSocietyId ||
      !selectedBuildingId ||
      !selectedFlatId
    ) {
      setOwnerships([]);
      setResidents([]);
      setLeaseAgreements([]);
      return;
    }
    void refreshOwnerships(selectedTenantId, selectedSocietyId, selectedBuildingId, selectedFlatId, token);
    void refreshResidents(selectedTenantId, selectedSocietyId, selectedBuildingId, selectedFlatId, token);
    void refreshLeaseAgreements(selectedTenantId, selectedSocietyId, selectedBuildingId, selectedFlatId, token);
  }, [
    refreshLeaseAgreements,
    refreshOwnerships,
    refreshResidents,
    selectedBuildingId,
    selectedFlatId,
    selectedSocietyId,
    selectedTenantId,
    sessionState,
    token
  ]);

  async function handleTenantSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError("");
    setNotice("");

    try {
      const authToken = await refreshToken();
      const payload = {
        name: tenantForm.name.trim(),
        slug: tenantForm.slug.trim(),
        subscription_plan: tenantForm.subscription_plan,
        billing_email: nullableText(tenantForm.billing_email),
        phone: nullableText(tenantForm.phone),
        timezone: tenantForm.timezone,
        locale: tenantForm.locale,
        currency: tenantForm.currency
      };

      if (editingTenantId) {
        await updateTenant(authToken, editingTenantId, { ...payload, metadata: {} });
      } else {
        await createTenant(authToken, payload);
      }

      setTenantForm(tenantFormDefaults);
      setEditingTenantId(null);
      setFormWorkspace(null);
      setNotice(editingTenantId ? "Tenant updated." : "Tenant created.");
      await refreshTenants(authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save tenant.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleManagedUserSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId) {
      setError("Select a tenant before adding a user.");
      return;
    }
    if (!managedUserForm.email.trim() && !managedUserForm.mobile_number.trim()) {
      setError("Enter either email or mobile number.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const societyRoles =
      managedUserForm.society_id && managedUserForm.society_role
        ? [{ society_id: managedUserForm.society_id, role: managedUserForm.society_role }]
        : [];
    const payload: ManagedUserCreatePayload = {
      full_name: managedUserForm.full_name.trim(),
      email: nullableText(managedUserForm.email),
      mobile_number: nullableText(managedUserForm.mobile_number),
      temporary_password: managedUserForm.temporary_password,
      tenant_roles: managedUserForm.tenant_admin ? ["tenant_admin"] : [],
      society_roles: societyRoles
    };

    try {
      const authToken = await refreshToken();
      await createManagedUser(authToken, selectedTenantId, payload);
      setManagedUserForm(managedUserFormDefaults);
      setFormWorkspace(null);
      setNotice("User provisioned.");
      await refreshManagedUsers(selectedTenantId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to provision user.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSocietySubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId) {
      setError("Select a tenant before saving a society.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: SocietyPayload = {
      name: societyForm.name.trim(),
      registration_number: nullableText(societyForm.registration_number),
      address_line1: nullableText(societyForm.address_line1),
      address_line2: nullableText(societyForm.address_line2),
      city: nullableText(societyForm.city),
      state: nullableText(societyForm.state),
      postal_code: nullableText(societyForm.postal_code),
      country: societyForm.country,
      timezone: societyForm.timezone,
      locale: societyForm.locale,
      currency: societyForm.currency,
      financial_year_start_month: societyForm.financial_year_start_month,
      receivable_account_id: societyForm.receivable_account_id || null,
      payable_account_id: societyForm.payable_account_id || null,
      member_advance_account_id: societyForm.member_advance_account_id || null
    };

    try {
      const authToken = await refreshToken();
      if (editingSocietyId) {
        await updateSociety(authToken, selectedTenantId, editingSocietyId, payload);
      } else {
        await createSociety(authToken, selectedTenantId, payload);
      }
      setSocietyForm(societyFormDefaults);
      setEditingSocietyId(null);
      setFormWorkspace(null);
      setNotice(editingSocietyId ? "Society updated." : "Society created.");
      await refreshSocieties(selectedTenantId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save society.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleBuildingSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before saving a building.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: BuildingPayload = {
      name: buildingForm.name.trim(),
      code: nullableText(buildingForm.code)
    };

    try {
      const authToken = await refreshToken();
      if (editingBuildingId) {
        await updateBuilding(authToken, selectedTenantId, selectedSocietyId, editingBuildingId, payload);
      } else {
        await createBuilding(authToken, selectedTenantId, selectedSocietyId, payload);
      }
      setBuildingForm(buildingFormDefaults);
      setEditingBuildingId(null);
      setFormWorkspace(null);
      setNotice(editingBuildingId ? "Building updated." : "Building created.");
      await refreshBuildings(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save building.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleFlatTypeSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before saving a flat type.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: FlatTypePayload = {
      name: flatTypeForm.name.trim(),
      code: nullableText(flatTypeForm.code),
      unit_category: flatTypeForm.unit_category,
      bedroom_count: nullableNumber(flatTypeForm.bedroom_count),
      bathroom_count: nullableNumber(flatTypeForm.bathroom_count),
      carpet_area_sqft: nullableText(flatTypeForm.carpet_area_sqft),
      built_up_area_sqft: nullableText(flatTypeForm.built_up_area_sqft),
      default_parking_count: flatTypeForm.default_parking_count
    };

    try {
      const authToken = await refreshToken();
      if (editingFlatTypeId) {
        await updateFlatType(authToken, selectedTenantId, selectedSocietyId, editingFlatTypeId, payload);
      } else {
        await createFlatType(authToken, selectedTenantId, selectedSocietyId, payload);
      }
      setFlatTypeForm(flatTypeFormDefaults);
      setEditingFlatTypeId(null);
      setFormWorkspace(null);
      setNotice(editingFlatTypeId ? "Flat type updated." : "Flat type created.");
      await refreshFlatTypes(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save flat type.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleChargeTypeSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before saving a charge type.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: ChargeTypePayload = {
      name: chargeTypeForm.name.trim(),
      code: nullableText(chargeTypeForm.code),
      description: nullableText(chargeTypeForm.description),
      revenue_account_id: chargeTypeForm.revenue_account_id
    };

    try {
      const authToken = await refreshToken();
      if (editingChargeTypeId) {
        await updateChargeType(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          editingChargeTypeId,
          payload
        );
      } else {
        await createChargeType(authToken, selectedTenantId, selectedSocietyId, payload);
      }
      setChargeTypeForm(chargeTypeFormDefaults);
      setEditingChargeTypeId(null);
      setFormWorkspace(null);
      setNotice(editingChargeTypeId ? "Charge type updated." : "Charge type created.");
      await refreshChargeTypes(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save charge type.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleExpenseCategorySubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before saving an expense category.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: ExpenseCategoryPayload = {
      name: expenseCategoryForm.name.trim(),
      code: nullableText(expenseCategoryForm.code),
      description: nullableText(expenseCategoryForm.description),
      expense_account_id: expenseCategoryForm.expense_account_id
    };

    try {
      const authToken = await refreshToken();
      if (editingExpenseCategoryId) {
        await updateExpenseCategory(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          editingExpenseCategoryId,
          payload
        );
      } else {
        await createExpenseCategory(authToken, selectedTenantId, selectedSocietyId, payload);
      }
      setExpenseCategoryForm(expenseCategoryFormDefaults);
      setEditingExpenseCategoryId(null);
      setFormWorkspace(null);
      setNotice(editingExpenseCategoryId ? "Expense category updated." : "Expense category created.");
      await refreshExpenseCategories(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save expense category.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleBillingRuleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before saving a billing rule.");
      return;
    }

    const payload: BillingRulePayload = {
      charge_type_id: billingRuleForm.charge_type_id,
      name: billingRuleForm.name.trim(),
      calculation_method: billingRuleForm.calculation_method,
      amount: billingRuleForm.amount.trim() ? billingRuleForm.amount.trim() : null,
      area_basis: billingRuleForm.area_basis || null,
      frequency: billingRuleForm.frequency,
      generation_day: Number(billingRuleForm.generation_day),
      due_day: Number(billingRuleForm.due_day),
      billing_period_timing: billingRuleForm.billing_period_timing,
      next_generation_date: nullableText(billingRuleForm.next_generation_date),
      scope_type: billingRuleForm.scope_type,
      building_id: billingRuleForm.building_id || null,
      wing_id: billingRuleForm.wing_id || null,
      flat_type_id: billingRuleForm.flat_type_id || null,
      effective_from: billingRuleForm.effective_from,
      effective_to: nullableText(billingRuleForm.effective_to),
      description: nullableText(billingRuleForm.description),
      late_fee_rule_ids: billingRuleForm.late_fee_rule_ids
    };

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (editingBillingRuleId) {
        await updateBillingRule(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          editingBillingRuleId,
          payload
        );
      } else {
        await createBillingRule(authToken, selectedTenantId, selectedSocietyId, payload);
      }
      setBillingRuleForm({ ...billingRuleFormDefaults, effective_from: todayIsoDate() });
      setEditingBillingRuleId(null);
      setFormWorkspace(null);
      setNotice(editingBillingRuleId ? "Billing rule updated." : "Billing rule created.");
      await refreshBillingRules(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save billing rule.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleLateFeeRuleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before saving a penalty rule.");
      return;
    }

    const payload: LateFeeRulePayload = {
      charge_type_id: lateFeeRuleForm.charge_type_id,
      name: lateFeeRuleForm.name.trim(),
      calculation_method: lateFeeRuleForm.calculation_method,
      amount: lateFeeRuleForm.amount.trim(),
      grace_days: Number(lateFeeRuleForm.grace_days),
      repeat_interval_days: lateFeeRuleForm.repeat_interval_days
        ? Number(lateFeeRuleForm.repeat_interval_days)
        : null,
      max_applications_per_invoice: lateFeeRuleForm.max_applications_per_invoice
        ? Number(lateFeeRuleForm.max_applications_per_invoice)
        : null,
      effective_from: lateFeeRuleForm.effective_from,
      effective_to: nullableText(lateFeeRuleForm.effective_to),
      description: nullableText(lateFeeRuleForm.description)
    };

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (editingLateFeeRuleId) {
        await updateLateFeeRule(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          editingLateFeeRuleId,
          payload
        );
      } else {
        await createLateFeeRule(authToken, selectedTenantId, selectedSocietyId, payload);
      }
      setLateFeeRuleForm({ ...lateFeeRuleFormDefaults, effective_from: todayIsoDate() });
      setEditingLateFeeRuleId(null);
      setFormWorkspace(null);
      setNotice(editingLateFeeRuleId ? "Penalty rule updated." : "Penalty rule created.");
      await refreshLateFeeRules(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save penalty rule.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleLateFeePreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before previewing penalties.");
      return;
    }
    if (!lateFeeApplicationForm.late_fee_rule_ids.length) {
      setError("Select at least one active penalty rule.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const preview = await previewLateFees(
        authToken,
        selectedTenantId,
        selectedSocietyId,
        lateFeeApplicationForm
      );
      setLateFeePreview(preview);
      setNotice(
        preview.valid_rows
          ? `Preview completed. ${preview.valid_rows} penalty invoices are ready.`
          : "Preview completed. No penalty invoices are ready."
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to preview penalties.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleLateFeeApply() {
    if (!selectedTenantId || !selectedSocietyId || !lateFeePreview || lateFeePreview.valid_rows === 0) {
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const result = await applyLateFees(
        authToken,
        selectedTenantId,
        selectedSocietyId,
        lateFeeApplicationForm
      );
      setLateFeePreview(null);
      setNotice(`${result.generated_count} penalty invoices generated.`);
      await refreshInvoices(selectedTenantId, selectedSocietyId, authToken);
      await refreshOutstanding(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to apply penalties.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleRunScheduledDueJobs() {
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before running due jobs.");
      return;
    }

    const payload: ScheduledRunDueJobsPayload = {
      as_of_date: scheduledJobFilters.as_of_date,
      include_billing: true,
      include_late_fees: true
    };

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const result = await runScheduledDueJobs(
        authToken,
        selectedTenantId,
        selectedSocietyId,
        payload
      );
      setNotice(
        `Due jobs completed. ${result.generated_invoice_count} billing invoices and ` +
          `${result.generated_penalty_invoice_count} penalty invoices generated.`
      );
      await refreshScheduledJobs(selectedTenantId, selectedSocietyId, authToken);
      await refreshInvoices(selectedTenantId, selectedSocietyId, authToken);
      await refreshOutstanding(selectedTenantId, selectedSocietyId, authToken);
      await refreshBillingRules(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run due jobs.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleInvoiceSequenceSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before saving invoice numbering.");
      return;
    }

    const payload: DocumentSequencePayload = {
      prefix: invoiceSequenceForm.prefix.trim().toUpperCase(),
      include_period: invoiceSequenceForm.include_period,
      include_financial_year: invoiceSequenceForm.include_financial_year,
      separator: invoiceSequenceForm.separator,
      next_sequence: Number(invoiceSequenceForm.next_sequence),
      padding: Number(invoiceSequenceForm.padding),
      reset_policy: invoiceSequenceForm.reset_policy
    };

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const sequence = await updateInvoiceSequence(
        authToken,
        selectedTenantId,
        selectedSocietyId,
        payload
      );
      setInvoiceSequence(sequence);
      setInvoiceSequenceForm({
        prefix: sequence.prefix,
        include_period: sequence.include_period,
        include_financial_year: sequence.include_financial_year,
        separator: sequence.separator,
        next_sequence: sequence.next_sequence,
        padding: sequence.padding,
        reset_policy: sequence.reset_policy
      });
      setNotice("Invoice numbering updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save invoice numbering.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleInvoiceGenerationPreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before generating invoices.");
      return;
    }
    if (!invoiceGenerationForm.billing_rule_ids.length) {
      setError("Select at least one billing rule to generate.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    setInvoiceGenerationPreview(null);

    try {
      const authToken = await refreshToken();
      const preview = await previewInvoiceGeneration(
        authToken,
        selectedTenantId,
        selectedSocietyId,
        invoiceGenerationForm
      );
      setInvoiceGenerationPreview(preview);
      setNotice(
        `Preview completed: ${preview.valid_rows} invoices ready, ${preview.invalid_rows} invalid, ${preview.skipped_rows} skipped.`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to preview invoice generation.");
    } finally {
      setIsSaving(false);
    }
  }

  function toggleInvoiceGenerationRule(ruleId: string) {
    setInvoiceGenerationPreview(null);
    setInvoiceGenerationForm((current) => {
      const isSelected = current.billing_rule_ids.includes(ruleId);
      return {
        ...current,
        billing_rule_ids: isSelected
          ? current.billing_rule_ids.filter((id) => id !== ruleId)
          : [...current.billing_rule_ids, ruleId]
      };
    });
  }

  function selectAllInvoiceGenerationRules() {
    setInvoiceGenerationPreview(null);
    setInvoiceGenerationForm((current) => ({
      ...current,
      billing_rule_ids: selectableBillingRules.map((rule) => rule.id)
    }));
  }

  function clearInvoiceGenerationRules() {
    setInvoiceGenerationPreview(null);
    setInvoiceGenerationForm((current) => ({
      ...current,
      billing_rule_ids: []
    }));
  }

  function toggleInvoiceGenerationFlat(flatId: string) {
    setInvoiceGenerationPreview(null);
    setInvoiceGenerationForm((current) => {
      const selectedFlatIds = current.flat_ids ?? [];
      const isSelected = selectedFlatIds.includes(flatId);
      return {
        ...current,
        flat_ids: isSelected ? selectedFlatIds.filter((id) => id !== flatId) : [...selectedFlatIds, flatId]
      };
    });
  }

  function selectAllInvoiceGenerationFlats() {
    setInvoiceGenerationPreview(null);
    setInvoiceGenerationForm((current) => ({
      ...current,
      flat_ids: flats.map((flat) => flat.id)
    }));
  }

  function clearInvoiceGenerationFlats() {
    setInvoiceGenerationPreview(null);
    setInvoiceGenerationForm((current) => ({
      ...current,
      flat_ids: []
    }));
  }

  async function handleInvoiceGenerationConfirm() {
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before generating invoices.");
      return;
    }
    if (!invoiceGenerationPreview || invoiceGenerationPreview.invalid_rows > 0) {
      setError("Preview must be completed with no invalid rows before invoices can be generated.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    try {
      const authToken = await refreshToken();
      const result = await confirmInvoiceGeneration(
        authToken,
        selectedTenantId,
        selectedSocietyId,
        invoiceGenerationForm
      );
      setInvoiceGenerationPreview(null);
      setSelectedInvoiceId(result.invoice_ids[0] ?? "");
      setNotice(`${result.generated_count} invoices generated.`);
      await refreshInvoices(selectedTenantId, selectedSocietyId, authToken);
      await refreshOutstanding(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to generate invoices.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleManualInvoiceBuildingChange(buildingId: string) {
    setManualInvoiceForm((current) => ({ ...current, building_id: buildingId, flat_id: "" }));
    if (!selectedTenantId || !selectedSocietyId || !buildingId) {
      setFlats([]);
      return;
    }
    const authToken = await refreshToken();
    await refreshFlats(selectedTenantId, selectedSocietyId, buildingId, authToken);
  }

  async function handleManualInvoiceSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before creating a manual invoice.");
      return;
    }

    const payload: ManualInvoicePayload = {
      flat_id: manualInvoiceForm.flat_id,
      owner_id: null,
      invoice_date: manualInvoiceForm.invoice_date,
      due_date: manualInvoiceForm.due_date,
      billing_period_start: manualInvoiceForm.billing_period_start,
      billing_period_end: manualInvoiceForm.billing_period_end,
      notes: nullableText(manualInvoiceForm.notes),
      late_fee_rule_ids: manualInvoiceForm.late_fee_rule_ids,
      line_items: [
        {
          charge_type_id: manualInvoiceForm.charge_type_id,
          description: manualInvoiceForm.description.trim(),
          quantity: manualInvoiceForm.quantity,
          unit_amount: manualInvoiceForm.unit_amount
        }
      ]
    };

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const invoice = await createManualInvoice(authToken, selectedTenantId, selectedSocietyId, payload);
      setManualInvoiceForm({
        ...manualInvoiceFormDefaults,
        building_id: manualInvoiceForm.building_id,
        invoice_date: todayIsoDate(),
        due_date: todayIsoDate(),
        billing_period_start: todayIsoDate(),
        billing_period_end: todayIsoDate(),
        late_fee_rule_ids: []
      });
      setSelectedInvoiceId(invoice.id);
      setNotice(`Manual invoice ${invoice.invoice_number} created.`);
      await refreshInvoices(selectedTenantId, selectedSocietyId, authToken);
      await refreshOutstanding(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create manual invoice.");
    } finally {
      setIsSaving(false);
    }
  }

  function handleInvoiceCancel(invoice: Invoice) {
    if (!selectedTenantId || !selectedSocietyId) {
      return;
    }
    openReasonDialog({
      title: "Cancel Invoice",
      description: `Record why invoice ${invoice.invoice_number} is being cancelled.`,
      reasonLabel: "Cancellation reason",
      confirmLabel: "Cancel Invoice",
      errorMessage: "Unable to cancel invoice.",
      onConfirm: async (reason) => {
        const authToken = await refreshToken();
        const cancelledInvoice = await cancelInvoice(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          invoice.id,
          reason
        );
        setNotice(`Invoice ${cancelledInvoice.invoice_number} cancelled.`);
        await refreshInvoices(selectedTenantId, selectedSocietyId, authToken);
        await refreshOutstanding(selectedTenantId, selectedSocietyId, authToken);
        if (selectedInvoiceId === invoice.id) {
          setSelectedInvoiceDetail(
            await getInvoice(authToken, selectedTenantId, selectedSocietyId, invoice.id)
          );
        }
      }
    });
  }

  function handleBulkInvoiceCancel() {
    if (!selectedTenantId || !selectedSocietyId) {
      return;
    }
    const cancellableInvoiceIds = selectedInvoiceIds.filter((invoiceId) => {
      const invoice = invoices.find((item) => item.id === invoiceId);
      return invoice && invoice.status !== "cancelled" && Number(invoice.amount_paid) === 0;
    });
    if (!cancellableInvoiceIds.length) {
      setError("Select at least one unpaid, non-cancelled invoice.");
      return;
    }

    openReasonDialog({
      title: "Cancel Selected Invoices",
      description: `Record why ${cancellableInvoiceIds.length} selected invoices are being cancelled.`,
      reasonLabel: "Bulk cancellation reason",
      confirmLabel: "Cancel Selected",
      errorMessage: "Unable to cancel selected invoices.",
      onConfirm: async (reason) => {
        const authToken = await refreshToken();
        const response = await bulkCancelInvoices(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          cancellableInvoiceIds,
          reason
        );
        setSelectedInvoiceIds([]);
        setNotice(
          `Bulk cancellation completed. ${response.cancelled_count} cancelled, ${response.failed_count} failed.`
        );
        await refreshInvoices(selectedTenantId, selectedSocietyId, authToken);
        await refreshOutstanding(selectedTenantId, selectedSocietyId, authToken);
        if (selectedInvoiceId && cancellableInvoiceIds.includes(selectedInvoiceId)) {
          setSelectedInvoiceId("");
          setSelectedInvoiceDetail(null);
        }
      }
    });
  }

  async function handlePaymentBuildingChange(buildingId: string) {
    setPaymentForm((current) => ({ ...current, building_id: buildingId, flat_id: "" }));
    setPaymentAllocations({});
    setPaymentOpenInvoiceRows([]);
    setLastPaymentResult(null);
    if (!selectedTenantId || !selectedSocietyId || !buildingId) {
      setFlats([]);
      return;
    }
    const authToken = await refreshToken();
    await refreshFlats(selectedTenantId, selectedSocietyId, buildingId, authToken);
  }

  async function handlePaymentFlatChange(flatId: string) {
    setPaymentForm((current) => ({ ...current, flat_id: flatId }));
    setPaymentAllocations({});
    setPaymentOpenInvoiceRows([]);
    setLastPaymentResult(null);
    if (!selectedTenantId || !selectedSocietyId || !flatId) {
      return;
    }

    setIsLoadingPaymentOpenInvoices(true);
    setError("");
    try {
      const authToken = await refreshToken();
      const firstPage = await listInvoices(authToken, selectedTenantId, selectedSocietyId, {
        flat_id: flatId,
        page: 1,
        page_size: 200
      });
      let rows = firstPage.items;
      for (let page = 2; page <= firstPage.total_pages; page += 1) {
        const response = await listInvoices(authToken, selectedTenantId, selectedSocietyId, {
          flat_id: flatId,
          page,
          page_size: 200
        });
        rows = [...rows, ...response.items];
      }
      setPaymentOpenInvoiceRows(rows);
      const openInvoicesForFlat = rows
        .filter(
          (invoice) =>
            invoice.flat_id === flatId &&
            !["paid", "cancelled"].includes(invoice.status) &&
            Number(invoice.amount_due) > 0
        )
        .sort((left, right) => {
          const dueDateComparison = left.due_date.localeCompare(right.due_date);
          if (dueDateComparison !== 0) {
            return dueDateComparison;
          }
          const invoiceDateComparison = left.invoice_date.localeCompare(right.invoice_date);
          if (invoiceDateComparison !== 0) {
            return invoiceDateComparison;
          }
          return left.invoice_number.localeCompare(right.invoice_number);
        });
      setPaymentAllocations(buildOldestFirstPaymentAllocations(openInvoicesForFlat, paymentForm.amount));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load open invoices for payment.");
    } finally {
      setIsLoadingPaymentOpenInvoices(false);
    }
  }

  function startInvoicePaymentCollection(invoice: Invoice) {
    const flat = flats.find((item) => item.id === invoice.flat_id);
    if (!flat) {
      setError("Unable to collect payment because the invoice flat is not loaded.");
      return;
    }
    if (invoice.status === "paid" || invoice.status === "cancelled" || Number(invoice.amount_due) <= 0) {
      setError("Only open invoices with a balance can be collected.");
      return;
    }

    setPaymentForm((current) => ({
      ...paymentFormDefaults,
      building_id: flat.building_id,
      flat_id: invoice.flat_id,
      deposit_account_id: current.deposit_account_id,
      payment_date: todayIsoDate(),
      amount: invoice.amount_due,
      payment_mode: current.payment_mode || paymentFormDefaults.payment_mode,
      reference_number: "",
      notes: `Collection for ${invoice.invoice_number}`
    }));
    setPaymentOpenInvoiceRows([invoice]);
    setPaymentAllocations({ [invoice.id]: invoice.amount_due });
    setSelectedInvoiceId("");
    setSelectedInvoiceDetail(null);
    setWorkspace("payments");
    setFormWorkspace(null);
    setNotice(`Collecting payment for ${invoice.invoice_number}.`);
    setError("");
  }

  async function handlePaymentSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before recording payment.");
      return;
    }

    const allocations = Object.entries(paymentAllocations)
      .filter(([, amount]) => Number(amount) > 0)
      .map(([invoiceId, amount]) => ({ invoice_id: invoiceId, allocated_amount: amount }));
    const payload: PaymentPayload = {
      flat_id: paymentForm.flat_id,
      owner_id: null,
      deposit_account_id: paymentForm.deposit_account_id || null,
      payment_date: paymentForm.payment_date,
      amount: paymentForm.amount,
      payment_mode: paymentForm.payment_mode,
      reference_number: nullableText(paymentForm.reference_number),
      notes: nullableText(paymentForm.notes),
      allocations
    };

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const payment = await createPayment(authToken, selectedTenantId, selectedSocietyId, payload);
      setLastPaymentResult({
        payment,
        invoices: paymentOpenInvoices
      });
      setPaymentForm({
        ...paymentFormDefaults,
        building_id: paymentForm.building_id,
        flat_id: paymentForm.flat_id,
        payment_date: todayIsoDate()
      });
      setPaymentAllocations({});
      setNotice("Payment recorded.");
      await refreshPaymentOpenInvoices(selectedTenantId, selectedSocietyId, paymentForm.flat_id, authToken);
      await refreshInvoices(selectedTenantId, selectedSocietyId, authToken, invoiceFilters);
      await refreshOutstanding(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to record payment.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleChartOfAccountSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before saving an account.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: ChartOfAccountPayload = {
      parent_account_id: chartOfAccountForm.parent_account_id || null,
      account_code: chartOfAccountForm.account_code.trim(),
      account_name: chartOfAccountForm.account_name.trim(),
      account_type: chartOfAccountForm.account_type,
      normal_balance: chartOfAccountForm.normal_balance,
      description: nullableText(chartOfAccountForm.description)
    };

    try {
      const authToken = await refreshToken();
      if (editingChartOfAccountId) {
        await updateChartOfAccount(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          editingChartOfAccountId,
          payload
        );
      } else {
        await createChartOfAccount(authToken, selectedTenantId, selectedSocietyId, payload);
      }
      setChartOfAccountForm(chartOfAccountFormDefaults);
      setEditingChartOfAccountId(null);
      setFormWorkspace(null);
      setNotice(editingChartOfAccountId ? "Account updated." : "Account created.");
      await refreshChartOfAccounts(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save account.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleJournalSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before posting a journal entry.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: JournalEntryPayload = {
      journal_date: journalForm.journal_date,
      reference_number: nullableText(journalForm.reference_number),
      description: journalForm.description.trim(),
      notes: nullableText(journalForm.notes),
      lines: journalForm.lines.map((line) => ({
        account_id: line.account_id,
        description: nullableText(line.description),
        debit_amount: line.debit_amount || "0",
        credit_amount: line.credit_amount || "0"
      }))
    };

    try {
      const authToken = await refreshToken();
      await createJournal(authToken, selectedTenantId, selectedSocietyId, payload);
      setJournalForm(journalFormDefaults());
      setFormWorkspace(null);
      setNotice("Journal entry posted.");
      await refreshJournals(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to post journal entry.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleViewOpeningBalance(entry: JournalEntry) {
    if (!selectedTenantId || !selectedSocietyId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      setSelectedOpeningBalanceDetail(
        await getJournal(authToken, selectedTenantId, selectedSocietyId, entry.id)
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load opening balance detail.");
    }
  }

  async function handleBankCashAccountSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before saving a bank or cash account.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      await createChartOfAccount(authToken, selectedTenantId, selectedSocietyId, {
        account_code: bankCashAccountForm.account_code.trim(),
        account_name: bankCashAccountForm.account_name.trim(),
        account_type: "asset",
        normal_balance: "debit",
        description: nullableText(bankCashAccountForm.description)
      });
      setBankCashAccountForm(bankCashAccountFormDefaults);
      setFormWorkspace(null);
      setNotice("Bank/cash account created.");
      await refreshChartOfAccounts(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save bank/cash account.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleOpeningBalanceSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before posting opening balances.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    const payload: OpeningBalanceJournalPayload = {
      opening_date: openingBalanceForm.opening_date,
      reference_number: nullableText(openingBalanceForm.reference_number),
      notes: nullableText(openingBalanceForm.notes),
      lines: openingBalanceForm.lines.map((line) => ({
        account_id: line.account_id,
        description: nullableText(line.description),
        debit_amount: line.debit_amount || "0",
        credit_amount: line.credit_amount || "0"
      }))
    };

    try {
      const authToken = await refreshToken();
      await createOpeningBalanceJournal(authToken, selectedTenantId, selectedSocietyId, payload);
      setOpeningBalanceForm(openingBalanceFormDefaults());
      setFormWorkspace(null);
      setNotice("Opening balance journal posted.");
      await refreshJournals(selectedTenantId, selectedSocietyId, authToken);
      await refreshTrialBalance(selectedTenantId, selectedSocietyId, authToken);
      await refreshIncomeExpenseReport(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to post opening balances.");
    } finally {
      setIsSaving(false);
    }
  }

  function updateJournalLine(
    index: number,
    field: keyof ReturnType<typeof journalLineDefaults>,
    value: string
  ) {
    setJournalForm((current) => ({
      ...current,
      lines: current.lines.map((line, lineIndex) => {
        if (lineIndex !== index) {
          return line;
        }
        if (field === "debit_amount" && value) {
          return { ...line, debit_amount: value, credit_amount: "" };
        }
        if (field === "credit_amount" && value) {
          return { ...line, credit_amount: value, debit_amount: "" };
        }
        return { ...line, [field]: value };
      })
    }));
  }

  function addJournalLine() {
    setJournalForm((current) => ({
      ...current,
      lines: [...current.lines, journalLineDefaults()]
    }));
  }

  function removeJournalLine(index: number) {
    setJournalForm((current) => ({
      ...current,
      lines:
        current.lines.length > 2
          ? current.lines.filter((_, lineIndex) => lineIndex !== index)
          : current.lines
    }));
  }

  function updateOpeningBalanceLine(
    index: number,
    field: keyof ReturnType<typeof journalLineDefaults>,
    value: string
  ) {
    setOpeningBalanceForm((current) => ({
      ...current,
      lines: current.lines.map((line, lineIndex) =>
        lineIndex === index
          ? {
              ...line,
              [field]: value,
              ...(field === "debit_amount" && value ? { credit_amount: "" } : {}),
              ...(field === "credit_amount" && value ? { debit_amount: "" } : {})
            }
          : line
      )
    }));
  }

  function addOpeningBalanceLine() {
    setOpeningBalanceForm((current) => ({
      ...current,
      lines: [...current.lines, journalLineDefaults()]
    }));
  }

  function removeOpeningBalanceLine(index: number) {
    setOpeningBalanceForm((current) => ({
      ...current,
      lines: current.lines.filter((_, lineIndex) => lineIndex !== index)
    }));
  }

  async function handleAccountTransferSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before posting a transfer.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: AccountTransferPayload = {
      from_account_id: accountTransferForm.from_account_id,
      to_account_id: accountTransferForm.to_account_id,
      transfer_date: accountTransferForm.transfer_date,
      amount: accountTransferForm.amount,
      transfer_mode: accountTransferForm.transfer_mode,
      reference_number: nullableText(accountTransferForm.reference_number),
      description: accountTransferForm.description.trim(),
      notes: nullableText(accountTransferForm.notes)
    };

    try {
      const authToken = await refreshToken();
      await createAccountTransfer(authToken, selectedTenantId, selectedSocietyId, payload);
      setAccountTransferForm({ ...accountTransferFormDefaults, transfer_date: todayIsoDate() });
      setFormWorkspace(null);
      setNotice("Account transfer posted.");
      await refreshAccountTransfers(selectedTenantId, selectedSocietyId, authToken);
      await refreshJournals(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to post account transfer.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleOtherIncomeSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before recording other income.");
      return;
    }

    const payload: OtherIncomeReceiptPayload = {
      receipt_date: otherIncomeForm.receipt_date,
      payer_name: otherIncomeForm.payer_name.trim(),
      payer_type: otherIncomeForm.payer_type,
      income_account_id: otherIncomeForm.income_account_id,
      deposit_account_id: otherIncomeForm.deposit_account_id,
      amount: otherIncomeForm.amount,
      receipt_mode: otherIncomeForm.receipt_mode,
      reference_number: nullableText(otherIncomeForm.reference_number),
      description: otherIncomeForm.description.trim(),
      notes: nullableText(otherIncomeForm.notes)
    };

    setIsSaving(true);
    setError("");
    setNotice("");

    try {
      const authToken = await refreshToken();
      const receipt = await createOtherIncomeReceipt(authToken, selectedTenantId, selectedSocietyId, payload);
      setOtherIncomeForm({ ...otherIncomeFormDefaults, receipt_date: todayIsoDate() });
      setFormWorkspace(null);
      setNotice(`Other income receipt recorded for ${receipt.amount}.`);
      await refreshOtherIncomeReceipts(selectedTenantId, selectedSocietyId, authToken);
      await refreshJournals(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to record other income receipt.");
    } finally {
      setIsSaving(false);
    }
  }

  function handleOtherIncomeReverse(receipt: OtherIncomeReceipt) {
    if (!selectedTenantId || !selectedSocietyId || receipt.status === "reversed") {
      return;
    }

    openReasonDialog({
      title: "Reverse Other Income Receipt",
      description: `Record why the receipt from ${receipt.payer_name} is being reversed.`,
      reasonLabel: "Reversal reason",
      confirmLabel: "Reverse Receipt",
      errorMessage: "Unable to reverse other income receipt.",
      onConfirm: async (reason) => {
        const authToken = await refreshToken();
        const reversed = await reverseOtherIncomeReceipt(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          receipt.id,
          reason
        );
        setNotice(`Other income receipt reversed: ${reversed.payer_name}.`);
        await refreshOtherIncomeReceipts(selectedTenantId, selectedSocietyId, authToken);
        await refreshJournals(selectedTenantId, selectedSocietyId, authToken);
      }
    });
  }

  async function handleAccountLedgerSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before loading an account ledger.");
      return;
    }
    if (!accountLedgerFilters.account_id) {
      setError("Select an account before loading the ledger.");
      return;
    }
    if (
      accountLedgerFilters.date_from &&
      accountLedgerFilters.date_to &&
      accountLedgerFilters.date_from > accountLedgerFilters.date_to
    ) {
      setError("From date cannot be after to date.");
      return;
    }

    const authToken = await refreshToken();
    await refreshAccountLedger(selectedTenantId, selectedSocietyId, authToken, accountLedgerFilters);
  }

  async function handleFlatLedgerSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before loading a flat ledger.");
      return;
    }
    if (!flatLedgerFilters.flat_id) {
      setError("Select a flat before loading the ledger.");
      return;
    }
    if (
      flatLedgerFilters.date_from &&
      flatLedgerFilters.date_to &&
      flatLedgerFilters.date_from > flatLedgerFilters.date_to
    ) {
      setError("From date cannot be after to date.");
      return;
    }

    const authToken = await refreshToken();
    await refreshFlatLedger(selectedTenantId, selectedSocietyId, authToken, flatLedgerFilters);
  }

  function handleReverseJournal(entry: JournalEntry) {
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before reversing a journal.");
      return;
    }
    openReasonDialog({
      title: "Reverse Journal",
      description: `Record why ${entry.reference_number ?? entry.description} is being reversed.`,
      reasonLabel: "Reversal reason",
      confirmLabel: "Reverse Journal",
      errorMessage: "Unable to reverse journal.",
      onConfirm: async (reason) => {
        const authToken = await refreshToken();
        await reverseJournal(authToken, selectedTenantId, selectedSocietyId, entry.id, reason);
        setNotice("Journal reversed. Post a corrected entry if needed.");
        await refreshJournals(selectedTenantId, selectedSocietyId, authToken);
        if (accountLedgerFilters.account_id) {
          await refreshAccountLedger(selectedTenantId, selectedSocietyId, authToken, accountLedgerFilters);
        }
      }
    });
  }

  async function handleTrialBalanceSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before loading a trial balance.");
      return;
    }
    if (!trialBalanceFilters.as_of_date) {
      setError("Select an as-of date before loading the trial balance.");
      return;
    }

    const authToken = await refreshToken();
    await refreshTrialBalance(selectedTenantId, selectedSocietyId, authToken, trialBalanceFilters);
  }

  async function handleIncomeExpenseSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before loading the report.");
      return;
    }
    if (!incomeExpenseFilters.period_start || !incomeExpenseFilters.period_end) {
      setError("Select report period before loading income vs expense.");
      return;
    }
    if (incomeExpenseFilters.period_start > incomeExpenseFilters.period_end) {
      setError("Period start cannot be after period end.");
      return;
    }

    const authToken = await refreshToken();
    await refreshIncomeExpenseReport(selectedTenantId, selectedSocietyId, authToken, incomeExpenseFilters);
  }

  async function handleIncomeExpenseExport(exportFormat: "xlsx" | "pdf") {
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before exporting the report.");
      return;
    }
    if (!incomeExpenseFilters.period_start || !incomeExpenseFilters.period_end) {
      setError("Select report period before exporting income vs expense.");
      return;
    }
    if (incomeExpenseFilters.period_start > incomeExpenseFilters.period_end) {
      setError("Period start cannot be after period end.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const blob = await exportIncomeExpenseReport(
        authToken,
        selectedTenantId,
        selectedSocietyId,
        incomeExpenseFilters.period_start,
        incomeExpenseFilters.period_end,
        exportFormat
      );
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `income-expense-${incomeExpenseFilters.period_start}-${incomeExpenseFilters.period_end}.${exportFormat}`;
      link.click();
      URL.revokeObjectURL(url);
      setNotice(`Income vs expense ${exportFormat.toUpperCase()} exported.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to export income vs expense report.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleBalanceSheetSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before loading the balance sheet.");
      return;
    }
    if (!balanceSheetFilters.as_of_date) {
      setError("Select an as-of date before loading the balance sheet.");
      return;
    }

    const authToken = await refreshToken();
    await refreshBalanceSheetReport(selectedTenantId, selectedSocietyId, authToken, balanceSheetFilters);
  }

  async function handleBalanceSheetExport(exportFormat: "xlsx" | "pdf") {
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before exporting the balance sheet.");
      return;
    }
    if (!balanceSheetFilters.as_of_date) {
      setError("Select an as-of date before exporting the balance sheet.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const blob = await exportBalanceSheetReport(
        authToken,
        selectedTenantId,
        selectedSocietyId,
        balanceSheetFilters.as_of_date,
        exportFormat
      );
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `balance-sheet-${balanceSheetFilters.as_of_date}.${exportFormat}`;
      link.click();
      URL.revokeObjectURL(url);
      setNotice(`Balance sheet ${exportFormat.toUpperCase()} exported.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to export balance sheet.");
    } finally {
      setIsSaving(false);
    }
  }

  function downloadBlob(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function handleOperationalReportSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before loading reports.");
      return;
    }
    const selectedType = operationalReportTypes.find((report) => report.value === operationalReportType);
    if (!selectedType) {
      setError("Select a report.");
      return;
    }
    if (
      selectedType.mode === "period" &&
      operationalReportFilters.period_start > operationalReportFilters.period_end
    ) {
      setError("Period start cannot be after period end.");
      return;
    }

    setIsLoadingOperationalReport(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      let report: OperationalReportResult;
      if (operationalReportType === "billing") {
        report = await getBillingReport(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          operationalReportFilters.period_start,
          operationalReportFilters.period_end
        );
      } else if (operationalReportType === "collection") {
        report = await getCollectionReport(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          operationalReportFilters.period_start,
          operationalReportFilters.period_end
        );
      } else if (operationalReportType === "expenses") {
        report = await getExpenseOperationalReport(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          operationalReportFilters.period_start,
          operationalReportFilters.period_end
        );
      } else if (operationalReportType === "defaulters") {
        report = await getDefaulterReport(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          operationalReportFilters.as_of_date
        );
      } else {
        report = await getOutstandingSummary(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          operationalReportFilters.as_of_date
        );
      }
      setOperationalReport(report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load operational report.");
    } finally {
      setIsLoadingOperationalReport(false);
    }
  }

  async function handleOperationalReportExport(exportFormat: "xlsx" | "pdf") {
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before exporting reports.");
      return;
    }
    const selectedType = operationalReportTypes.find((report) => report.value === operationalReportType);
    if (!selectedType) {
      setError("Select a report.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const blob =
        selectedType.mode === "period"
          ? await exportPeriodOperationalReport(
              authToken,
              selectedTenantId,
              selectedSocietyId,
              operationalReportType as "billing" | "collection" | "expenses",
              operationalReportFilters.period_start,
              operationalReportFilters.period_end,
              exportFormat
            )
          : await exportAsOfOperationalReport(
              authToken,
              selectedTenantId,
              selectedSocietyId,
              operationalReportType as "defaulters" | "outstanding",
              operationalReportFilters.as_of_date,
              exportFormat
            );
      const suffix =
        selectedType.mode === "period"
          ? `${operationalReportFilters.period_start}-${operationalReportFilters.period_end}`
          : operationalReportFilters.as_of_date;
      downloadBlob(blob, `${operationalReportType}-${suffix}.${exportFormat}`);
      setNotice(`${selectedType.label} ${exportFormat.toUpperCase()} exported.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to export operational report.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handlePaymentRegisterExport(exportFormat: "xlsx" | "pdf") {
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before exporting payments.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const blob = await exportPaymentRegister(
        authToken,
        selectedTenantId,
        selectedSocietyId,
        {
          flat_number: paymentRegisterFilters.flat_number || undefined,
          status: paymentRegisterFilters.status || undefined,
          payment_mode: paymentRegisterFilters.payment_mode || undefined,
          payment_date_from: paymentRegisterFilters.payment_date_from || undefined,
          payment_date_to: paymentRegisterFilters.payment_date_to || undefined
        },
        exportFormat
      );
      downloadBlob(blob, `payment-register.${exportFormat}`);
      setNotice(`Payment register ${exportFormat.toUpperCase()} exported.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to export payment register.");
    } finally {
      setIsSaving(false);
    }
  }

  function handlePaymentRegisterReverse(payment: PaymentRegisterRow) {
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before reversing payment.");
      return;
    }
    openReasonDialog({
      title: "Reverse Payment",
      description: `Record why payment ${payment.reference_number ?? payment.payment_date} is being reversed.`,
      reasonLabel: "Reversal reason",
      confirmLabel: "Reverse Payment",
      errorMessage: "Unable to reverse payment.",
      onConfirm: async (reason) => {
        const authToken = await refreshToken();
        await reversePayment(authToken, selectedTenantId, selectedSocietyId, payment.id, reason);
        setNotice("Payment reversed.");
        await refreshPaymentRegister(selectedTenantId, selectedSocietyId, authToken);
        await refreshInvoices(selectedTenantId, selectedSocietyId, authToken);
        await refreshOutstanding(selectedTenantId, selectedSocietyId, authToken);
      }
    });
  }

  async function handleBuildingFloorSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId || !selectedBuildingId) {
      setError("Select a tenant, society, and building before saving a floor.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: BuildingFloorPayload = {
      floor_label: buildingFloorForm.floor_label.trim(),
      floor_number: buildingFloorForm.floor_number
    };

    try {
      const authToken = await refreshToken();
      if (editingBuildingFloorId) {
        await updateBuildingFloor(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          editingBuildingFloorId,
          payload
        );
      } else {
        await createBuildingFloor(authToken, selectedTenantId, selectedSocietyId, selectedBuildingId, payload);
      }
      setBuildingFloorForm(buildingFloorFormDefaults);
      setEditingBuildingFloorId(null);
      setFormWorkspace(null);
      setNotice(editingBuildingFloorId ? "Floor updated." : "Floor created.");
      await refreshBuildingFloors(selectedTenantId, selectedSocietyId, selectedBuildingId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save floor.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleWingSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId || !selectedBuildingId) {
      setError("Select a tenant, society, and building before saving a wing.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: WingPayload = {
      name: wingForm.name.trim(),
      code: nullableText(wingForm.code)
    };

    try {
      const authToken = await refreshToken();
      if (editingWingId) {
        await updateWing(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          editingWingId,
          payload
        );
      } else {
        await createWing(authToken, selectedTenantId, selectedSocietyId, selectedBuildingId, payload);
      }
      setWingForm(wingFormDefaults);
      setEditingWingId(null);
      setFormWorkspace(null);
      setNotice(editingWingId ? "Wing updated." : "Wing created.");
      await refreshWings(selectedTenantId, selectedSocietyId, selectedBuildingId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save wing.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleFlatSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId || !selectedBuildingId) {
      setError("Select a tenant, society, and building before saving a flat.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: FlatPayload = {
      wing_id: flatForm.wing_id || null,
      floor_id: flatForm.floor_id || null,
      flat_type_id: flatForm.flat_type_id || null,
      flat_number: flatForm.flat_number.trim(),
      floor_number: null,
      carpet_area_sqft: null,
      built_up_area_sqft: null,
      parking_count: null
    };

    try {
      const authToken = await refreshToken();
      if (editingFlatId) {
        await updateFlat(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          editingFlatId,
          payload
        );
      } else {
        await createFlat(authToken, selectedTenantId, selectedSocietyId, selectedBuildingId, payload);
      }
      setFlatForm(flatFormDefaults);
      setEditingFlatId(null);
      setFormWorkspace(null);
      setNotice(editingFlatId ? "Flat updated." : "Flat created.");
      await refreshFlats(selectedTenantId, selectedSocietyId, selectedBuildingId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save flat.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleOwnerSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before saving an owner.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: OwnerPayload = {
      user_id: null,
      owner_type: ownerForm.owner_type,
      full_name: ownerForm.full_name.trim(),
      email: nullableText(ownerForm.email),
      mobile_number: nullableText(ownerForm.mobile_number),
      tax_identifier: nullableText(ownerForm.tax_identifier),
      billing_address: nullableText(ownerForm.billing_address)
    };

    try {
      const authToken = await refreshToken();
      if (editingOwnerId) {
        await updateOwner(authToken, selectedTenantId, selectedSocietyId, editingOwnerId, payload);
      } else {
        await createOwner(authToken, selectedTenantId, selectedSocietyId, payload);
      }
      setOwnerForm(ownerFormDefaults);
      setEditingOwnerId(null);
      setFormWorkspace(null);
      setNotice(editingOwnerId ? "Owner updated." : "Owner created.");
      await refreshOwners(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save owner.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleVendorSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before saving a vendor.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: VendorPayload = {
      vendor_code: vendorForm.vendor_code.trim(),
      vendor_name: vendorForm.vendor_name.trim(),
      vendor_type: vendorForm.vendor_type,
      contact_person: nullableText(vendorForm.contact_person),
      email: nullableText(vendorForm.email),
      mobile_number: nullableText(vendorForm.mobile_number),
      tax_identifier: nullableText(vendorForm.tax_identifier),
      billing_address: nullableText(vendorForm.billing_address)
    };

    try {
      const authToken = await refreshToken();
      if (editingVendorId) {
        await updateVendor(authToken, selectedTenantId, selectedSocietyId, editingVendorId, payload);
      } else {
        await createVendor(authToken, selectedTenantId, selectedSocietyId, payload);
      }
      setVendorForm(vendorFormDefaults);
      setEditingVendorId(null);
      setFormWorkspace(null);
      setNotice(editingVendorId ? "Vendor updated." : "Vendor created.");
      await refreshVendors(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save vendor.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleExpenseSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before saving an expense.");
      return;
    }

    const payload: ExpensePayload = {
      vendor_id: expenseForm.vendor_id || null,
      expense_category_id: expenseForm.expense_category_id,
      payment_account_id: expenseForm.payment_account_id || null,
      expense_type: expenseForm.expense_type,
      vendor_bill_number: nullableText(expenseForm.vendor_bill_number),
      reference_number: nullableText(expenseForm.reference_number),
      expense_date: expenseForm.expense_date,
      due_date: expenseForm.due_date,
      description: expenseForm.description.trim(),
      amount: expenseForm.amount,
      tax_amount: expenseForm.tax_amount || "0.00",
      notes: nullableText(expenseForm.notes)
    };

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (editingExpenseId) {
        await updateExpense(authToken, selectedTenantId, selectedSocietyId, editingExpenseId, payload);
      } else {
        await createExpense(authToken, selectedTenantId, selectedSocietyId, payload);
      }
      setExpenseForm({ ...expenseFormDefaults, expense_date: todayIsoDate(), due_date: todayIsoDate() });
      setEditingExpenseId(null);
      setFormWorkspace(null);
      setNotice(editingExpenseId ? "Expense updated." : "Expense recorded.");
      await refreshExpenses(selectedTenantId, selectedSocietyId, authToken);
      await refreshExpensePayments(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save expense.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleExpensePaymentSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before recording expense payment.");
      return;
    }
    const allocations = Object.entries(expensePaymentAllocations)
      .filter(([, amount]) => Number(amount) > 0)
      .map(([expenseId, amount]) => ({ expense_id: expenseId, allocated_amount: amount }));
    const payload: ExpensePaymentPayload = {
      vendor_id: expensePaymentForm.vendor_id || null,
      payment_account_id: expensePaymentForm.payment_account_id,
      payment_date: expensePaymentForm.payment_date,
      amount: expensePaymentForm.amount,
      payment_mode: expensePaymentForm.payment_mode,
      reference_number: nullableText(expensePaymentForm.reference_number),
      notes: nullableText(expensePaymentForm.notes),
      allocations
    };
    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      await createExpensePayment(authToken, selectedTenantId, selectedSocietyId, payload);
      setExpensePaymentForm({
        ...expensePaymentFormDefaults,
        vendor_id: expensePaymentForm.vendor_id,
        payment_account_id: expensePaymentForm.payment_account_id,
        payment_date: todayIsoDate()
      });
      setExpensePaymentAllocations({});
      setNotice("Expense payment recorded.");
      await refreshExpenses(selectedTenantId, selectedSocietyId, authToken);
      await refreshExpensePayments(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to record expense payment.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleOwnershipSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId || !selectedBuildingId || !selectedFlatId) {
      setError("Select a tenant, society, building, and flat before saving ownership.");
      return;
    }
    if (!ownershipForm.owner_id) {
      setError("Select an owner before saving ownership.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: FlatOwnershipPayload = {
      owner_id: ownershipForm.owner_id,
      ownership_type: ownershipForm.ownership_type,
      ownership_percentage: nullableText(ownershipForm.ownership_percentage),
      effective_from: ownershipForm.effective_from || todayIsoDate(),
      effective_to: nullableText(ownershipForm.effective_to)
    };

    try {
      const authToken = await refreshToken();
      if (editingOwnershipId) {
        await updateFlatOwnership(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          selectedFlatId,
          editingOwnershipId,
          payload
        );
      } else {
        await createFlatOwnership(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          selectedFlatId,
          payload
        );
      }
      setOwnershipForm({ ...ownershipFormDefaults, effective_from: todayIsoDate() });
      setEditingOwnershipId(null);
      setFormWorkspace(null);
      setNotice(editingOwnershipId ? "Flat ownership updated." : "Flat ownership created.");
      await refreshOwnerships(
        selectedTenantId,
        selectedSocietyId,
        selectedBuildingId,
        selectedFlatId,
        authToken
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save flat ownership.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleResidentSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId || !selectedBuildingId || !selectedFlatId) {
      setError("Select a tenant, society, building, and flat before saving resident.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: ResidentPayload = {
      owner_id: residentForm.owner_id || null,
      user_id: null,
      resident_type: residentForm.resident_type,
      full_name: residentForm.full_name.trim(),
      email: nullableText(residentForm.email),
      mobile_number: nullableText(residentForm.mobile_number),
      move_in_date: residentForm.move_in_date || todayIsoDate(),
      move_out_date: nullableText(residentForm.move_out_date)
    };

    try {
      const authToken = await refreshToken();
      if (editingResidentId) {
        await updateResident(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          selectedFlatId,
          editingResidentId,
          payload
        );
      } else {
        await createResident(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          selectedFlatId,
          payload
        );
      }
      setResidentForm({ ...residentFormDefaults, move_in_date: todayIsoDate() });
      setEditingResidentId(null);
      setFormWorkspace(null);
      setNotice(editingResidentId ? "Resident updated." : "Resident created.");
      await refreshResidents(
        selectedTenantId,
        selectedSocietyId,
        selectedBuildingId,
        selectedFlatId,
        authToken
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save resident.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleLeaseAgreementSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTenantId || !selectedSocietyId || !selectedBuildingId || !selectedFlatId) {
      setError("Select a tenant, society, building, and flat before saving a lease.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");

    const payload: LeaseAgreementPayload = {
      owner_id: leaseAgreementForm.owner_id,
      resident_id: leaseAgreementForm.resident_id || null,
      tenant_name: leaseAgreementForm.tenant_name.trim(),
      tenant_email: nullableText(leaseAgreementForm.tenant_email),
      tenant_mobile_number: nullableText(leaseAgreementForm.tenant_mobile_number),
      agreement_start_date: leaseAgreementForm.agreement_start_date,
      agreement_end_date: leaseAgreementForm.agreement_end_date,
      move_in_date: leaseAgreementForm.move_in_date,
      move_out_date: nullableText(leaseAgreementForm.move_out_date),
      monthly_rent: nullableText(leaseAgreementForm.monthly_rent),
      security_deposit: nullableText(leaseAgreementForm.security_deposit),
      police_verification_status: leaseAgreementForm.police_verification_status,
      document_reference: nullableText(leaseAgreementForm.document_reference),
      notes: nullableText(leaseAgreementForm.notes)
    };

    try {
      const authToken = await refreshToken();
      if (editingLeaseAgreementId) {
        await updateLeaseAgreement(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          selectedFlatId,
          editingLeaseAgreementId,
          payload
        );
      } else {
        await createLeaseAgreement(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          selectedFlatId,
          payload
        );
      }
      setLeaseAgreementForm(leaseAgreementFormDefaults);
      setEditingLeaseAgreementId(null);
      setFormWorkspace(null);
      setNotice(editingLeaseAgreementId ? "Lease agreement updated." : "Lease agreement created.");
      await refreshLeaseAgreements(
        selectedTenantId,
        selectedSocietyId,
        selectedBuildingId,
        selectedFlatId,
        authToken
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save lease agreement.");
    } finally {
      setIsSaving(false);
    }
  }

  function startEditTenant(tenant: Tenant) {
    setWorkspace("tenants");
    setFormWorkspace("tenants");
    setEditingTenantId(tenant.id);
    setNotice("");
    setError("");
    setTenantForm({
      name: tenant.name,
      slug: tenant.slug,
      subscription_plan: tenant.subscription_plan,
      billing_email: tenant.billing_email ?? "",
      phone: tenant.phone ?? "",
      timezone: tenant.timezone,
      locale: tenant.locale,
      currency: tenant.currency
    });
  }

  function startEditSociety(society: Society) {
    setWorkspace("societies");
    setFormWorkspace("societies");
    setEditingSocietyId(society.id);
    setNotice("");
    setError("");
    setSocietyForm({
      name: society.name,
      registration_number: society.registration_number ?? "",
      address_line1: society.address_line1 ?? "",
      address_line2: society.address_line2 ?? "",
      city: society.city ?? "",
      state: society.state ?? "",
      postal_code: society.postal_code ?? "",
      country: society.country,
      timezone: society.timezone,
      locale: society.locale,
      currency: society.currency,
      financial_year_start_month: society.financial_year_start_month,
      receivable_account_id: society.receivable_account_id ?? "",
      payable_account_id: society.payable_account_id ?? "",
      member_advance_account_id: society.member_advance_account_id ?? ""
    });
  }

  function startEditBuilding(building: Building) {
    setWorkspace("buildings");
    setFormWorkspace("buildings");
    setEditingBuildingId(building.id);
    setNotice("");
    setError("");
    setBuildingForm({
      name: building.name,
      code: building.code ?? ""
    });
  }

  function startEditFlatType(flatType: FlatType) {
    setWorkspace("flatTypes");
    setFormWorkspace("flatTypes");
    setEditingFlatTypeId(flatType.id);
    setNotice("");
    setError("");
    setFlatTypeForm({
      name: flatType.name,
      code: flatType.code ?? "",
      unit_category: flatType.unit_category,
      bedroom_count: flatType.bedroom_count === null ? "" : String(flatType.bedroom_count),
      bathroom_count: flatType.bathroom_count === null ? "" : String(flatType.bathroom_count),
      carpet_area_sqft: flatType.carpet_area_sqft ?? "",
      built_up_area_sqft: flatType.built_up_area_sqft ?? "",
      default_parking_count: flatType.default_parking_count
    });
  }

  function startEditChargeType(chargeType: ChargeType) {
    setWorkspace("chargeTypes");
    setFormWorkspace("chargeTypes");
    setEditingChargeTypeId(chargeType.id);
    setNotice("");
    setError("");
    setChargeTypeForm({
      name: chargeType.name,
      code: chargeType.code ?? "",
      description: chargeType.description ?? "",
      revenue_account_id: chargeType.revenue_account_id ?? ""
    });
  }

  function startEditExpenseCategory(category: ExpenseCategory) {
    setWorkspace("expenseCategories");
    setFormWorkspace("expenseCategories");
    setEditingExpenseCategoryId(category.id);
    setNotice("");
    setError("");
    setExpenseCategoryForm({
      name: category.name,
      code: category.code ?? "",
      description: category.description ?? "",
      expense_account_id: category.expense_account_id
    });
  }

  function startEditBillingRule(rule: BillingRule) {
    setWorkspace("billingRules");
    setFormWorkspace("billingRules");
    setEditingBillingRuleId(rule.id);
    setNotice("");
    setError("");
    setBillingRuleForm({
      charge_type_id: rule.charge_type_id,
      name: rule.name,
      calculation_method: rule.calculation_method,
      amount: rule.amount ?? "",
      area_basis: rule.area_basis ?? "",
      frequency: rule.frequency,
      generation_day: rule.generation_day,
      due_day: rule.due_day,
      billing_period_timing: rule.billing_period_timing,
      next_generation_date: rule.next_generation_date ?? "",
      scope_type: rule.scope_type,
      building_id: rule.building_id ?? "",
      wing_id: rule.wing_id ?? "",
      flat_type_id: rule.flat_type_id ?? "",
      effective_from: rule.effective_from,
      effective_to: rule.effective_to ?? "",
      description: rule.description ?? "",
      late_fee_rule_ids: rule.late_fee_rule_ids ?? []
    });
  }

  function startEditLateFeeRule(rule: LateFeeRule) {
    setWorkspace("lateFeeRules");
    setFormWorkspace("lateFeeRules");
    setEditingLateFeeRuleId(rule.id);
    setNotice("");
    setError("");
    setLateFeeRuleForm({
      charge_type_id: rule.charge_type_id,
      name: rule.name,
      calculation_method: rule.calculation_method,
      amount: rule.amount,
      grace_days: rule.grace_days,
      repeat_interval_days: rule.repeat_interval_days === null ? "" : String(rule.repeat_interval_days),
      max_applications_per_invoice:
        rule.max_applications_per_invoice === null ? "" : String(rule.max_applications_per_invoice),
      effective_from: rule.effective_from,
      effective_to: rule.effective_to ?? "",
      description: rule.description ?? ""
    });
  }

  function startEditChartOfAccount(account: ChartOfAccount) {
    setWorkspace("chartOfAccounts");
    setFormWorkspace("chartOfAccounts");
    resetChartOfAccountImport();
    setEditingChartOfAccountId(account.id);
    setNotice("");
    setError("");
    setChartOfAccountForm({
      parent_account_id: account.parent_account_id ?? "",
      account_code: account.account_code,
      account_name: account.account_name,
      account_type: account.account_type,
      normal_balance: account.normal_balance,
      description: account.description ?? ""
    });
  }

  function startEditBuildingFloor(floor: BuildingFloor) {
    setWorkspace("floors");
    setFormWorkspace("floors");
    setEditingBuildingFloorId(floor.id);
    setNotice("");
    setError("");
    setBuildingFloorForm({
      floor_label: floor.floor_label,
      floor_number: floor.floor_number
    });
  }

  function startEditWing(wing: Wing) {
    setWorkspace("wings");
    setFormWorkspace("wings");
    setEditingWingId(wing.id);
    setNotice("");
    setError("");
    setWingForm({
      name: wing.name,
      code: wing.code ?? ""
    });
  }

  function startEditFlat(flat: Flat) {
    setWorkspace("flats");
    setFormWorkspace("flats");
    setEditingFlatId(flat.id);
    setNotice("");
    setError("");
    setFlatForm({
      wing_id: flat.wing_id ?? "",
      floor_id: flat.floor_id ?? "",
      flat_type_id: flat.flat_type_id ?? "",
      flat_number: flat.flat_number,
      floor_number: flat.floor_number === null ? "" : String(flat.floor_number),
      carpet_area_sqft: flat.carpet_area_sqft ?? "",
      built_up_area_sqft: flat.built_up_area_sqft ?? "",
      parking_count: flat.parking_count === null ? "" : String(flat.parking_count)
    });
  }

  function startEditOwner(owner: Owner) {
    setWorkspace("owners");
    setFormWorkspace("owners");
    setEditingOwnerId(owner.id);
    setNotice("");
    setError("");
    setOwnerForm({
      owner_type: owner.owner_type,
      full_name: owner.full_name,
      email: owner.email ?? "",
      mobile_number: owner.mobile_number ?? "",
      tax_identifier: owner.tax_identifier ?? "",
      billing_address: owner.billing_address ?? ""
    });
  }

  function startEditVendor(vendor: Vendor) {
    setWorkspace("vendors");
    setFormWorkspace("vendors");
    setEditingVendorId(vendor.id);
    setNotice("");
    setError("");
    setVendorForm({
      vendor_code: vendor.vendor_code,
      vendor_name: vendor.vendor_name,
      vendor_type: vendor.vendor_type,
      contact_person: vendor.contact_person ?? "",
      email: vendor.email ?? "",
      mobile_number: vendor.mobile_number ?? "",
      tax_identifier: vendor.tax_identifier ?? "",
      billing_address: vendor.billing_address ?? ""
    });
  }

  function startEditExpense(expense: Expense) {
    setWorkspace("expenses");
    setFormWorkspace("expenses");
    setEditingExpenseId(expense.id);
    setNotice("");
    setError("");
    setExpenseForm({
      vendor_id: expense.vendor_id ?? "",
      expense_category_id: expense.expense_category_id,
      payment_account_id: expense.payment_account_id ?? "",
      expense_type: expense.expense_type,
      vendor_bill_number: expense.vendor_bill_number ?? "",
      reference_number: expense.reference_number ?? "",
      expense_date: expense.expense_date,
      due_date: expense.due_date,
      description: expense.description,
      amount: expense.amount,
      tax_amount: expense.tax_amount,
      notes: expense.notes ?? ""
    });
  }

  function startEditOwnership(ownership: FlatOwnership) {
    setWorkspace("ownerships");
    setFormWorkspace("ownerships");
    setEditingOwnershipId(ownership.id);
    setNotice("");
    setError("");
    setOwnershipForm({
      owner_id: ownership.owner_id,
      ownership_type: ownership.ownership_type,
      ownership_percentage: ownership.ownership_percentage ?? "",
      effective_from: ownership.effective_from,
      effective_to: ownership.effective_to ?? ""
    });
  }

  function startEditResident(resident: Resident) {
    setWorkspace("residents");
    setFormWorkspace("residents");
    setEditingResidentId(resident.id);
    setNotice("");
    setError("");
    setResidentForm({
      owner_id: resident.owner_id ?? "",
      resident_type: resident.resident_type,
      full_name: resident.full_name,
      email: resident.email ?? "",
      mobile_number: resident.mobile_number ?? "",
      move_in_date: resident.move_in_date,
      move_out_date: resident.move_out_date ?? ""
    });
  }

  function startEditLeaseAgreement(leaseAgreement: LeaseAgreement) {
    setWorkspace("leaseAgreements");
    setFormWorkspace("leaseAgreements");
    setEditingLeaseAgreementId(leaseAgreement.id);
    setNotice("");
    setError("");
    setLeaseAgreementForm({
      owner_id: leaseAgreement.owner_id,
      resident_id: leaseAgreement.resident_id ?? "",
      tenant_name: leaseAgreement.tenant_name,
      tenant_email: leaseAgreement.tenant_email ?? "",
      tenant_mobile_number: leaseAgreement.tenant_mobile_number ?? "",
      agreement_start_date: leaseAgreement.agreement_start_date,
      agreement_end_date: leaseAgreement.agreement_end_date,
      move_in_date: leaseAgreement.move_in_date,
      move_out_date: leaseAgreement.move_out_date ?? "",
      monthly_rent: leaseAgreement.monthly_rent ?? "",
      security_deposit: leaseAgreement.security_deposit ?? "",
      police_verification_status: leaseAgreement.police_verification_status,
      document_reference: leaseAgreement.document_reference ?? "",
      notes: leaseAgreement.notes ?? ""
    });
  }

  async function handleTenantStatusChange(tenant: Tenant) {
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (tenant.status === "active") {
        await suspendTenant(authToken, tenant.id);
        setNotice("Tenant suspended.");
      } else {
        await activateTenant(authToken, tenant.id);
        setNotice("Tenant activated.");
      }
      await refreshTenants(authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update tenant status.");
    }
  }

  async function handleManagedUserStatusChange(user: ManagedUser) {
    if (!selectedTenantId) {
      setError("Select a tenant before updating user access.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const hasActiveMembership =
        user.tenant_memberships.some((membership) => membership.status === "active") ||
        user.society_memberships.some((membership) => membership.status === "active");
      if (hasActiveMembership) {
        await suspendManagedUser(authToken, selectedTenantId, user.id);
      } else {
        await activateManagedUser(authToken, selectedTenantId, user.id);
      }
      setNotice(hasActiveMembership ? "User access suspended." : "User access activated.");
      await refreshManagedUsers(selectedTenantId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update user access.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSocietyStatusChange(society: Society) {
    if (!selectedTenantId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (society.status === "active") {
        await suspendSociety(authToken, selectedTenantId, society.id);
        setNotice("Society suspended.");
      } else {
        await activateSociety(authToken, selectedTenantId, society.id);
        setNotice("Society activated.");
      }
      await refreshSocieties(selectedTenantId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update society status.");
    }
  }

  async function handleBuildingStatusChange(building: Building) {
    if (!selectedTenantId || !selectedSocietyId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (building.status === "active") {
        await suspendBuilding(authToken, selectedTenantId, selectedSocietyId, building.id);
        setNotice("Building suspended.");
      } else {
        await activateBuilding(authToken, selectedTenantId, selectedSocietyId, building.id);
        setNotice("Building activated.");
      }
      await refreshBuildings(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update building status.");
    }
  }

  async function handleFlatTypeStatusChange(flatType: FlatType) {
    if (!selectedTenantId || !selectedSocietyId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (flatType.status === "active") {
        await inactivateFlatType(authToken, selectedTenantId, selectedSocietyId, flatType.id);
        setNotice("Flat type inactivated.");
      } else {
        await activateFlatType(authToken, selectedTenantId, selectedSocietyId, flatType.id);
        setNotice("Flat type activated.");
      }
      await refreshFlatTypes(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update flat type status.");
    }
  }

  async function handleChargeTypeStatusChange(chargeType: ChargeType) {
    if (!selectedTenantId || !selectedSocietyId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (chargeType.status === "active") {
        await inactivateChargeType(authToken, selectedTenantId, selectedSocietyId, chargeType.id);
        setNotice("Charge type inactivated.");
      } else {
        await activateChargeType(authToken, selectedTenantId, selectedSocietyId, chargeType.id);
        setNotice("Charge type activated.");
      }
      await refreshChargeTypes(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update charge type status.");
    }
  }

  async function handleExpenseCategoryStatusChange(category: ExpenseCategory) {
    if (!selectedTenantId || !selectedSocietyId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (category.status === "active") {
        await inactivateExpenseCategory(authToken, selectedTenantId, selectedSocietyId, category.id);
        setNotice("Expense category inactivated.");
      } else {
        await activateExpenseCategory(authToken, selectedTenantId, selectedSocietyId, category.id);
        setNotice("Expense category activated.");
      }
      await refreshExpenseCategories(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update expense category status.");
    }
  }

  async function handleBillingRuleStatusChange(rule: BillingRule) {
    if (!selectedTenantId || !selectedSocietyId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (rule.status === "active") {
        await inactivateBillingRule(authToken, selectedTenantId, selectedSocietyId, rule.id);
        setNotice("Billing rule inactivated.");
      } else {
        await activateBillingRule(authToken, selectedTenantId, selectedSocietyId, rule.id);
        setNotice("Billing rule activated.");
      }
      await refreshBillingRules(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update billing rule status.");
    }
  }

  async function handleLateFeeRuleStatusChange(rule: LateFeeRule) {
    if (!selectedTenantId || !selectedSocietyId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (rule.status === "active") {
        await inactivateLateFeeRule(authToken, selectedTenantId, selectedSocietyId, rule.id);
        setNotice("Penalty rule inactivated.");
      } else {
        await activateLateFeeRule(authToken, selectedTenantId, selectedSocietyId, rule.id);
        setNotice("Penalty rule activated.");
      }
      await refreshLateFeeRules(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update penalty rule status.");
    }
  }

  async function handleChartOfAccountStatusChange(account: ChartOfAccount) {
    if (!selectedTenantId || !selectedSocietyId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (account.status === "active") {
        await inactivateChartOfAccount(authToken, selectedTenantId, selectedSocietyId, account.id);
        setNotice("Account inactivated.");
      } else {
        await activateChartOfAccount(authToken, selectedTenantId, selectedSocietyId, account.id);
        setNotice("Account activated.");
      }
      await refreshChartOfAccounts(selectedTenantId, selectedSocietyId, authToken);
      await refreshChargeTypes(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update account status.");
    }
  }

  async function handleBuildingFloorStatusChange(floor: BuildingFloor) {
    if (!selectedTenantId || !selectedSocietyId || !selectedBuildingId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (floor.status === "active") {
        await inactivateBuildingFloor(authToken, selectedTenantId, selectedSocietyId, selectedBuildingId, floor.id);
        setNotice("Floor inactivated.");
      } else {
        await activateBuildingFloor(authToken, selectedTenantId, selectedSocietyId, selectedBuildingId, floor.id);
        setNotice("Floor activated.");
      }
      await refreshBuildingFloors(selectedTenantId, selectedSocietyId, selectedBuildingId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update floor status.");
    }
  }

  async function handleWingStatusChange(wing: Wing) {
    if (!selectedTenantId || !selectedSocietyId || !selectedBuildingId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (wing.status === "active") {
        await suspendWing(authToken, selectedTenantId, selectedSocietyId, selectedBuildingId, wing.id);
        setNotice("Wing suspended.");
      } else {
        await activateWing(authToken, selectedTenantId, selectedSocietyId, selectedBuildingId, wing.id);
        setNotice("Wing activated.");
      }
      await refreshWings(selectedTenantId, selectedSocietyId, selectedBuildingId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update wing status.");
    }
  }

  async function handleFlatStatusChange(flat: Flat) {
    if (!selectedTenantId || !selectedSocietyId || !selectedBuildingId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (flat.status === "active") {
        await inactivateFlat(authToken, selectedTenantId, selectedSocietyId, selectedBuildingId, flat.id);
        setNotice("Flat inactivated.");
      } else {
        await activateFlat(authToken, selectedTenantId, selectedSocietyId, selectedBuildingId, flat.id);
        setNotice("Flat activated.");
      }
      await refreshFlats(selectedTenantId, selectedSocietyId, selectedBuildingId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update flat status.");
    }
  }

  async function handleOwnerStatusChange(owner: Owner) {
    if (!selectedTenantId || !selectedSocietyId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (owner.status === "active") {
        await inactivateOwner(authToken, selectedTenantId, selectedSocietyId, owner.id);
        setNotice("Owner inactivated.");
      } else {
        await activateOwner(authToken, selectedTenantId, selectedSocietyId, owner.id);
        setNotice("Owner activated.");
      }
      await refreshOwners(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update owner status.");
    }
  }

  async function handleVendorStatusChange(vendor: Vendor) {
    if (!selectedTenantId || !selectedSocietyId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (vendor.status === "active") {
        await inactivateVendor(authToken, selectedTenantId, selectedSocietyId, vendor.id);
        setNotice("Vendor inactivated.");
      } else {
        await activateVendor(authToken, selectedTenantId, selectedSocietyId, vendor.id);
        setNotice("Vendor activated.");
      }
      await refreshVendors(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update vendor status.");
    }
  }

  async function handleExpenseApprove(expense: Expense) {
    if (!selectedTenantId || !selectedSocietyId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      await approveExpense(authToken, selectedTenantId, selectedSocietyId, expense.id);
      setNotice("Expense approved.");
      await refreshExpenses(selectedTenantId, selectedSocietyId, authToken);
      await refreshExpensePayments(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to approve expense.");
    }
  }

  function handleExpenseCancel(expense: Expense) {
    if (!selectedTenantId || !selectedSocietyId) {
      return;
    }
    openReasonDialog({
      title: "Cancel Expense",
      description: `Record why this expense is being cancelled: ${expense.description}`,
      reasonLabel: "Cancellation reason",
      confirmLabel: "Cancel Expense",
      errorMessage: "Unable to cancel expense.",
      onConfirm: async (reason) => {
        const authToken = await refreshToken();
        await cancelExpense(authToken, selectedTenantId, selectedSocietyId, expense.id, reason);
        setNotice("Expense cancelled.");
        await refreshExpenses(selectedTenantId, selectedSocietyId, authToken);
        await refreshExpensePayments(selectedTenantId, selectedSocietyId, authToken);
      }
    });
  }

  async function handleOwnershipStatusChange(ownership: FlatOwnership) {
    if (!selectedTenantId || !selectedSocietyId || !selectedBuildingId || !selectedFlatId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (ownership.status === "active") {
        await closeFlatOwnership(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          selectedFlatId,
          ownership.id,
          todayIsoDate()
        );
        setNotice("Flat ownership closed.");
      } else {
        await activateFlatOwnership(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          selectedFlatId,
          ownership.id
        );
        setNotice("Flat ownership activated.");
      }
      await refreshOwnerships(
        selectedTenantId,
        selectedSocietyId,
        selectedBuildingId,
        selectedFlatId,
        authToken
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update flat ownership status.");
    }
  }

  async function handleResidentStatusChange(resident: Resident) {
    if (!selectedTenantId || !selectedSocietyId || !selectedBuildingId || !selectedFlatId) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      if (resident.status === "active") {
        await moveOutResident(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          selectedFlatId,
          resident.id,
          todayIsoDate()
        );
        setNotice("Resident moved out.");
      } else {
        await activateResident(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          selectedFlatId,
          resident.id
        );
        setNotice("Resident activated.");
      }
      await refreshResidents(
        selectedTenantId,
        selectedSocietyId,
        selectedBuildingId,
        selectedFlatId,
        authToken
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update resident status.");
    }
  }

  function handleLeaseAgreementTerminate(leaseAgreement: LeaseAgreement) {
    if (!selectedTenantId || !selectedSocietyId || !selectedBuildingId || !selectedFlatId) {
      return;
    }
    openReasonDialog({
      title: "Terminate Lease",
      description: `Record why the lease for ${leaseAgreement.tenant_name} is being terminated.`,
      reasonLabel: "Termination reason",
      confirmLabel: "Terminate Lease",
      errorMessage: "Unable to terminate lease agreement.",
      onConfirm: async (reason) => {
        const authToken = await refreshToken();
        await terminateLeaseAgreement(
          authToken,
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          selectedFlatId,
          leaseAgreement.id,
          todayIsoDate(),
          reason
        );
        setNotice("Lease agreement terminated.");
        await refreshLeaseAgreements(
          selectedTenantId,
          selectedSocietyId,
          selectedBuildingId,
          selectedFlatId,
          authToken
        );
      }
    });
  }

  function resetFlatImport() {
    setIsFlatImportOpen(false);
    setFlatImportFileName("");
    setFlatImportRows([]);
    setFlatImportPreview(null);
  }

  function resetChartOfAccountImport() {
    setIsChartOfAccountImportOpen(false);
    setChartOfAccountImportFileName("");
    setChartOfAccountImportRows([]);
    setChartOfAccountImportPreview(null);
  }

  function selectTenant(tenantId: string) {
    setSelectedTenantId(tenantId);
    setSelectedSocietyId("");
    setSelectedBuildingId("");
    setSelectedFlatId("");
    setSocieties([]);
    setManagedUsers([]);
    setBuildings([]);
    setBuildingFloors([]);
    setFlatTypes([]);
    setChargeTypes([]);
    setExpenseCategories([]);
    setBillingRules([]);
    setInvoiceSequence(null);
    setInvoiceSequenceForm(invoiceSequenceFormDefaults);
    setInvoices([]);
    setPaymentOpenInvoiceRows([]);
    setLastPaymentResult(null);
    setOutstandingSummary(null);
    setSelectedInvoiceId("");
    setSelectedInvoiceDetail(null);
    setInvoiceGenerationPreview(null);
    setInvoiceGenerationForm((current) => ({ ...current, billing_rule_ids: [] }));
    setChartOfAccounts([]);
    setWings([]);
    setFlats([]);
    setSelectedOpeningBalanceDetail(null);
    setOwnerships([]);
    setResidents([]);
    setLeaseAgreements([]);
    setOwners([]);
    setVendors([]);
    setExpenses([]);
    setExpensePayments([]);
    setEditingSocietyId(null);
    setManagedUserForm(managedUserFormDefaults);
    setEditingBuildingId(null);
    setEditingBuildingFloorId(null);
    setEditingFlatTypeId(null);
    setEditingChargeTypeId(null);
    setEditingExpenseCategoryId(null);
    setEditingBillingRuleId(null);
    setEditingChartOfAccountId(null);
    setEditingWingId(null);
    setEditingFlatId(null);
    setEditingOwnerId(null);
    setEditingVendorId(null);
    setEditingExpenseId(null);
    setEditingOwnershipId(null);
    setEditingResidentId(null);
    setEditingLeaseAgreementId(null);
    setSocietyForm(societyFormDefaults);
    setBuildingForm(buildingFormDefaults);
    setBuildingFloorForm(buildingFloorFormDefaults);
    setFlatTypeForm(flatTypeFormDefaults);
    setChargeTypeForm(chargeTypeFormDefaults);
    setExpenseCategoryForm(expenseCategoryFormDefaults);
    setBillingRuleForm({ ...billingRuleFormDefaults, effective_from: todayIsoDate() });
    setChartOfAccountForm(chartOfAccountFormDefaults);
    setWingForm(wingFormDefaults);
    setFlatForm(flatFormDefaults);
    setOwnerForm(ownerFormDefaults);
    setVendorForm(vendorFormDefaults);
    setExpenseForm({ ...expenseFormDefaults, expense_date: todayIsoDate(), due_date: todayIsoDate() });
    setExpensePaymentForm({ ...expensePaymentFormDefaults, payment_date: todayIsoDate() });
    setExpensePaymentAllocations({});
    setOwnershipForm(ownershipFormDefaults);
    setResidentForm(residentFormDefaults);
    setLeaseAgreementForm(leaseAgreementFormDefaults);
    setFormWorkspace(null);
    resetFlatImport();
    resetChartOfAccountImport();
    setNotice("");
    setError("");
  }

  function selectSociety(societyId: string) {
    setSelectedSocietyId(societyId);
    setSelectedBuildingId("");
    setSelectedFlatId("");
    setWings([]);
    setBuildingFloors([]);
    setChargeTypes([]);
    setExpenseCategories([]);
    setBillingRules([]);
    setInvoiceSequence(null);
    setInvoiceSequenceForm(invoiceSequenceFormDefaults);
    setInvoices([]);
    setPaymentOpenInvoiceRows([]);
    setLastPaymentResult(null);
    setOutstandingSummary(null);
    setSelectedInvoiceId("");
    setSelectedInvoiceDetail(null);
    setInvoiceGenerationPreview(null);
    setSelectedOpeningBalanceDetail(null);
    setInvoiceGenerationForm((current) => ({ ...current, billing_rule_ids: [] }));
    setChartOfAccounts([]);
    setFlats([]);
    setOwnerships([]);
    setResidents([]);
    setLeaseAgreements([]);
    setOwners([]);
    setVendors([]);
    setExpenses([]);
    setExpensePayments([]);
    setEditingBuildingId(null);
    setEditingBuildingFloorId(null);
    setEditingFlatTypeId(null);
    setEditingChargeTypeId(null);
    setEditingExpenseCategoryId(null);
    setEditingBillingRuleId(null);
    setEditingChartOfAccountId(null);
    setEditingWingId(null);
    setEditingFlatId(null);
    setEditingOwnerId(null);
    setEditingVendorId(null);
    setEditingExpenseId(null);
    setEditingOwnershipId(null);
    setEditingResidentId(null);
    setEditingLeaseAgreementId(null);
    setBuildingForm(buildingFormDefaults);
    setBuildingFloorForm(buildingFloorFormDefaults);
    setFlatTypeForm(flatTypeFormDefaults);
    setChargeTypeForm(chargeTypeFormDefaults);
    setExpenseCategoryForm(expenseCategoryFormDefaults);
    setBillingRuleForm({ ...billingRuleFormDefaults, effective_from: todayIsoDate() });
    setChartOfAccountForm(chartOfAccountFormDefaults);
    setWingForm(wingFormDefaults);
    setFlatForm(flatFormDefaults);
    setOwnerForm(ownerFormDefaults);
    setVendorForm(vendorFormDefaults);
    setExpenseForm({ ...expenseFormDefaults, expense_date: todayIsoDate(), due_date: todayIsoDate() });
    setExpensePaymentForm({ ...expensePaymentFormDefaults, payment_date: todayIsoDate() });
    setExpensePaymentAllocations({});
    setOwnershipForm(ownershipFormDefaults);
    setResidentForm(residentFormDefaults);
    setLeaseAgreementForm(leaseAgreementFormDefaults);
    setFormWorkspace(null);
    resetFlatImport();
    resetChartOfAccountImport();
    setNotice("");
    setError("");
  }

  function selectBuilding(buildingId: string) {
    setSelectedBuildingId(buildingId);
    setSelectedFlatId("");
    setFlats([]);
    setOwnerships([]);
    setResidents([]);
    setLeaseAgreements([]);
    setBuildingFloors([]);
    setEditingWingId(null);
    setEditingFlatId(null);
    setEditingBuildingFloorId(null);
    setEditingOwnershipId(null);
    setEditingResidentId(null);
    setEditingLeaseAgreementId(null);
    setWingForm(wingFormDefaults);
    setFlatForm(flatFormDefaults);
    setBuildingFloorForm(buildingFloorFormDefaults);
    setOwnershipForm(ownershipFormDefaults);
    setResidentForm(residentFormDefaults);
    setLeaseAgreementForm(leaseAgreementFormDefaults);
    setFormWorkspace(null);
    resetFlatImport();
    setNotice("");
    setError("");
  }

  function selectFlat(flatId: string) {
    setSelectedFlatId(flatId);
    setEditingOwnershipId(null);
    setEditingResidentId(null);
    setEditingLeaseAgreementId(null);
    setOwnershipForm({ ...ownershipFormDefaults, effective_from: todayIsoDate() });
    setResidentForm({ ...residentFormDefaults, move_in_date: todayIsoDate() });
    setLeaseAgreementForm({
      ...leaseAgreementFormDefaults,
      agreement_start_date: todayIsoDate(),
      agreement_end_date: todayIsoDate(),
      move_in_date: todayIsoDate()
    });
    setFormWorkspace(null);
    resetFlatImport();
    setNotice("");
    setError("");
  }

  function openCurrentCreateForm() {
    setError("");
    setNotice("");

    if (workspace === "tenants") {
      setEditingTenantId(null);
      setTenantForm(tenantFormDefaults);
    } else if (workspace === "users") {
      setManagedUserForm({
        ...managedUserFormDefaults,
        society_id: selectedSocietyId
      });
    } else if (workspace === "societies") {
      setEditingSocietyId(null);
      setSocietyForm(societyFormDefaults);
    } else if (workspace === "buildings") {
      setEditingBuildingId(null);
      setBuildingForm(buildingFormDefaults);
    } else if (workspace === "floors") {
      setEditingBuildingFloorId(null);
      setBuildingFloorForm({
        ...buildingFloorFormDefaults,
        floor_number: nextBuildingFloorNumber(buildingFloors)
      });
    } else if (workspace === "flatTypes") {
      setEditingFlatTypeId(null);
      setFlatTypeForm(flatTypeFormDefaults);
    } else if (workspace === "chartOfAccounts") {
      setEditingChartOfAccountId(null);
      setChartOfAccountForm(chartOfAccountFormDefaults);
      resetChartOfAccountImport();
    } else if (workspace === "bankCashAccounts") {
      setBankCashAccountForm(bankCashAccountFormDefaults);
    } else if (workspace === "openingBalances") {
      setOpeningBalanceForm(openingBalanceFormDefaults());
    } else if (workspace === "journals") {
      setJournalForm(journalFormDefaults());
    } else if (workspace === "accountTransfers") {
      setAccountTransferForm({ ...accountTransferFormDefaults, transfer_date: todayIsoDate() });
    } else if (workspace === "otherIncome") {
      setOtherIncomeForm({ ...otherIncomeFormDefaults, receipt_date: todayIsoDate() });
    } else if (workspace === "chargeTypes") {
      setEditingChargeTypeId(null);
      setChargeTypeForm(chargeTypeFormDefaults);
    } else if (workspace === "expenseCategories") {
      setEditingExpenseCategoryId(null);
      setExpenseCategoryForm(expenseCategoryFormDefaults);
    } else if (workspace === "billingRules") {
      setEditingBillingRuleId(null);
      setBillingRuleForm({ ...billingRuleFormDefaults, effective_from: todayIsoDate() });
    } else if (workspace === "lateFeeRules") {
      setEditingLateFeeRuleId(null);
      setLateFeeRuleForm({ ...lateFeeRuleFormDefaults, effective_from: todayIsoDate() });
    } else if (workspace === "wings") {
      setEditingWingId(null);
      setWingForm(wingFormDefaults);
    } else if (workspace === "flats") {
      setEditingFlatId(null);
      setFlatForm(flatFormDefaults);
      resetFlatImport();
    } else if (workspace === "owners") {
      setEditingOwnerId(null);
      setOwnerForm(ownerFormDefaults);
    } else if (workspace === "vendors") {
      setEditingVendorId(null);
      setVendorForm(vendorFormDefaults);
    } else if (workspace === "expenses") {
      setEditingExpenseId(null);
      setExpenseForm({ ...expenseFormDefaults, expense_date: todayIsoDate(), due_date: todayIsoDate() });
    } else if (workspace === "ownerships") {
      setEditingOwnershipId(null);
      setOwnershipForm({ ...ownershipFormDefaults, effective_from: todayIsoDate() });
    } else if (workspace === "residents") {
      setEditingResidentId(null);
      setResidentForm({ ...residentFormDefaults, move_in_date: todayIsoDate() });
    } else if (workspace === "leaseAgreements") {
      setEditingLeaseAgreementId(null);
      setLeaseAgreementForm({
        ...leaseAgreementFormDefaults,
        agreement_start_date: todayIsoDate(),
        agreement_end_date: todayIsoDate(),
        move_in_date: todayIsoDate()
      });
    }

    setFormWorkspace(workspace);
  }

  function closeCurrentForm() {
    if (workspace === "tenants") {
      setEditingTenantId(null);
      setTenantForm(tenantFormDefaults);
    } else if (workspace === "users") {
      setManagedUserForm(managedUserFormDefaults);
    } else if (workspace === "societies") {
      setEditingSocietyId(null);
      setSocietyForm(societyFormDefaults);
    } else if (workspace === "buildings") {
      setEditingBuildingId(null);
      setBuildingForm(buildingFormDefaults);
    } else if (workspace === "floors") {
      setEditingBuildingFloorId(null);
      setBuildingFloorForm(buildingFloorFormDefaults);
    } else if (workspace === "flatTypes") {
      setEditingFlatTypeId(null);
      setFlatTypeForm(flatTypeFormDefaults);
    } else if (workspace === "chartOfAccounts") {
      setEditingChartOfAccountId(null);
      setChartOfAccountForm(chartOfAccountFormDefaults);
    } else if (workspace === "bankCashAccounts") {
      setBankCashAccountForm(bankCashAccountFormDefaults);
    } else if (workspace === "openingBalances") {
      setOpeningBalanceForm(openingBalanceFormDefaults());
    } else if (workspace === "journals") {
      setJournalForm(journalFormDefaults());
    } else if (workspace === "accountTransfers") {
      setAccountTransferForm({ ...accountTransferFormDefaults, transfer_date: todayIsoDate() });
    } else if (workspace === "otherIncome") {
      setOtherIncomeForm({ ...otherIncomeFormDefaults, receipt_date: todayIsoDate() });
    } else if (workspace === "chargeTypes") {
      setEditingChargeTypeId(null);
      setChargeTypeForm(chargeTypeFormDefaults);
    } else if (workspace === "expenseCategories") {
      setEditingExpenseCategoryId(null);
      setExpenseCategoryForm(expenseCategoryFormDefaults);
    } else if (workspace === "billingRules") {
      setEditingBillingRuleId(null);
      setBillingRuleForm({ ...billingRuleFormDefaults, effective_from: todayIsoDate() });
    } else if (workspace === "lateFeeRules") {
      setEditingLateFeeRuleId(null);
      setLateFeeRuleForm({ ...lateFeeRuleFormDefaults, effective_from: todayIsoDate() });
    } else if (workspace === "wings") {
      setEditingWingId(null);
      setWingForm(wingFormDefaults);
    } else if (workspace === "flats") {
      setEditingFlatId(null);
      setFlatForm(flatFormDefaults);
    } else if (workspace === "owners") {
      setEditingOwnerId(null);
      setOwnerForm(ownerFormDefaults);
    } else if (workspace === "vendors") {
      setEditingVendorId(null);
      setVendorForm(vendorFormDefaults);
    } else if (workspace === "expenses") {
      setEditingExpenseId(null);
      setExpenseForm({ ...expenseFormDefaults, expense_date: todayIsoDate(), due_date: todayIsoDate() });
    } else if (workspace === "ownerships") {
      setEditingOwnershipId(null);
      setOwnershipForm({ ...ownershipFormDefaults, effective_from: todayIsoDate() });
    } else if (workspace === "residents") {
      setEditingResidentId(null);
      setResidentForm({ ...residentFormDefaults, move_in_date: todayIsoDate() });
    } else if (workspace === "leaseAgreements") {
      setEditingLeaseAgreementId(null);
      setLeaseAgreementForm(leaseAgreementFormDefaults);
    }

    setFormWorkspace(null);
    setNotice("");
    setError("");
  }

  function openFlatImport() {
    setError("");
    setNotice("");
    setEditingFlatId(null);
    setFlatForm(flatFormDefaults);
    setFormWorkspace(null);
    resetFlatImport();
    setIsFlatImportOpen(true);
  }

  function openChartOfAccountImport() {
    setError("");
    setNotice("");
    setEditingChartOfAccountId(null);
    setChartOfAccountForm(chartOfAccountFormDefaults);
    setFormWorkspace(null);
    resetChartOfAccountImport();
    setIsChartOfAccountImportOpen(true);
  }

  async function handleChartOfAccountImportFileChange(file: File | null) {
    setError("");
    setNotice("");
    setChartOfAccountImportPreview(null);

    if (!file) {
      setChartOfAccountImportFileName("");
      setChartOfAccountImportRows([]);
      return;
    }

    try {
      const content = await file.text();
      const rows = parseChartOfAccountImportCsv(content);
      setChartOfAccountImportFileName(file.name);
      setChartOfAccountImportRows(rows);
      if (!rows.length) {
        setError("CSV file has no import rows.");
      }
    } catch (err) {
      setChartOfAccountImportFileName("");
      setChartOfAccountImportRows([]);
      setError(err instanceof Error ? err.message : "Unable to read CSV file.");
    }
  }

  async function handleChartOfAccountImportPreview() {
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before previewing import.");
      return;
    }
    if (!chartOfAccountImportRows.length) {
      setError("Choose a CSV file before previewing import.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const preview = await previewChartOfAccountImport(
        authToken,
        selectedTenantId,
        selectedSocietyId,
        chartOfAccountImportRows
      );
      setChartOfAccountImportPreview(preview);
      setNotice(
        preview.invalid_rows
          ? `Preview completed with ${preview.invalid_rows} invalid rows.`
          : `Preview completed. ${preview.valid_rows} accounts are ready to import.`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to preview chart of accounts import.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleChartOfAccountImportConfirm() {
    if (!selectedTenantId || !selectedSocietyId) {
      setError("Select a tenant and society before confirming import.");
      return;
    }
    if (
      !chartOfAccountImportRows.length ||
      !chartOfAccountImportPreview ||
      chartOfAccountImportPreview.invalid_rows > 0
    ) {
      setError("Preview must be valid before confirming import.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const result = await confirmChartOfAccountImport(
        authToken,
        selectedTenantId,
        selectedSocietyId,
        chartOfAccountImportRows
      );
      resetChartOfAccountImport();
      setNotice(`${result.imported_count} ledger accounts imported.`);
      await refreshChartOfAccounts(selectedTenantId, selectedSocietyId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to confirm chart of accounts import.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleFlatImportFileChange(file: File | null) {
    setError("");
    setNotice("");
    setFlatImportPreview(null);

    if (!file) {
      setFlatImportFileName("");
      setFlatImportRows([]);
      return;
    }

    try {
      const content = await file.text();
      const rows = parseFlatImportCsv(content);
      setFlatImportFileName(file.name);
      setFlatImportRows(rows);
      if (!rows.length) {
        setError("CSV file has no import rows.");
      }
    } catch (err) {
      setFlatImportFileName("");
      setFlatImportRows([]);
      setError(err instanceof Error ? err.message : "Unable to read CSV file.");
    }
  }

  async function handleFlatImportPreview() {
    if (!selectedTenantId || !selectedSocietyId || !selectedBuildingId) {
      setError("Select a tenant, society, and building before previewing import.");
      return;
    }
    if (!flatImportRows.length) {
      setError("Choose a CSV file before previewing import.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const preview = await previewFlatImport(
        authToken,
        selectedTenantId,
        selectedSocietyId,
        selectedBuildingId,
        flatImportRows
      );
      setFlatImportPreview(preview);
      setNotice(
        preview.invalid_rows
          ? `Preview completed with ${preview.invalid_rows} invalid rows.`
          : `Preview completed. ${preview.valid_rows} rows are ready to import.`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to preview flat import.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleFlatImportConfirm() {
    if (!selectedTenantId || !selectedSocietyId || !selectedBuildingId) {
      setError("Select a tenant, society, and building before confirming import.");
      return;
    }
    if (!flatImportRows.length || !flatImportPreview || flatImportPreview.invalid_rows > 0) {
      setError("Preview must be valid before confirming import.");
      return;
    }

    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const authToken = await refreshToken();
      const result = await confirmFlatImport(
        authToken,
        selectedTenantId,
        selectedSocietyId,
        selectedBuildingId,
        flatImportRows
      );
      resetFlatImport();
      setNotice(`${result.imported_count} flats imported.`);
      await refreshFlats(selectedTenantId, selectedSocietyId, selectedBuildingId, authToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to confirm flat import.");
    } finally {
      setIsSaving(false);
    }
  }

  function downloadFlatImportTemplate() {
    const csv = "flat_number,flat_type_code,floor_label,wing_code\n101,2BHK,First Floor,A\n";
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "flat-import-template.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  function downloadChartOfAccountImportTemplate() {
    const csv = [
      "account_code,parent_account_code,account_name,account_type,normal_balance,description",
      "1000,,Assets,asset,debit,Asset control account",
      "1010,1000,Bank Account,asset,debit,Society bank account",
      "1100,1000,Maintenance Receivable,asset,debit,Member outstanding dues",
      "2000,,Liabilities,liability,credit,Liability control account",
      "2010,2000,Security Deposit Liability,liability,credit,Deposits collected from members",
      "4000,,Income,income,credit,Income control account",
      "4010,4000,Sinking Fund Income,income,credit,Sinking fund billing",
      "4020,4000,Repair Fund Income,income,credit,Repair fund billing",
      "5000,,Expenses,expense,debit,Expense control account",
      "5010,5000,Housekeeping Expense,expense,debit,Housekeeping vendor expense"
    ].join("\n");
    const blob = new Blob([`${csv}\n`], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "chart-of-accounts-import-template.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  function refreshCurrentWorkspace() {
    if (workspace === "tenants") {
      void refreshTenants();
      return;
    }
    if (workspace === "users") {
      void refreshManagedUsers(selectedTenantId);
      return;
    }
    if (workspace === "societies") {
      void refreshSocieties(selectedTenantId);
      return;
    }
    if (workspace === "buildings") {
      void refreshBuildings(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "floors") {
      void refreshBuildingFloors(selectedTenantId, selectedSocietyId, selectedBuildingId);
      return;
    }
    if (workspace === "flatTypes") {
      void refreshFlatTypes(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "chargeTypes") {
      void refreshChargeTypes(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "expenseCategories") {
      void refreshExpenseCategories(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "billingRules") {
      void refreshBillingRules(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "lateFeeRules") {
      void refreshLateFeeRules(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "lateFeeApplication") {
      setLateFeePreview(null);
      return;
    }
    if (workspace === "scheduledJobs") {
      void refreshScheduledJobs(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "numberingSettings") {
      void refreshInvoiceSequence(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "invoiceGeneration") {
      setInvoiceGenerationPreview(null);
      return;
    }
    if (workspace === "manualInvoices") {
      void refreshInvoices(selectedTenantId, selectedSocietyId, token, invoiceFilters);
      return;
    }
    if (workspace === "invoices") {
      void refreshInvoices(selectedTenantId, selectedSocietyId, token, invoiceFilters);
      return;
    }
    if (workspace === "payments") {
      void refreshPaymentOpenInvoices(selectedTenantId, selectedSocietyId, paymentForm.flat_id, token);
      void refreshOutstanding(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "paymentRegister") {
      void refreshPaymentRegister(selectedTenantId, selectedSocietyId, token, paymentRegisterFilters);
      return;
    }
    if (workspace === "outstanding") {
      void refreshOutstanding(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "chartOfAccounts") {
      void refreshChartOfAccounts(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "bankCashAccounts") {
      void refreshChartOfAccounts(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "openingBalances") {
      void refreshJournals(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "journals") {
      void refreshJournals(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "accountTransfers") {
      void refreshAccountTransfers(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "otherIncome") {
      void refreshOtherIncomeReceipts(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "accountLedgers") {
      void refreshAccountLedger(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "flatLedgers") {
      void refreshFlatLedger(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "trialBalance") {
      void refreshTrialBalance(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "incomeExpense") {
      void refreshIncomeExpenseReport(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "balanceSheet") {
      void refreshBalanceSheetReport(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "wings") {
      void refreshWings(selectedTenantId, selectedSocietyId, selectedBuildingId);
      return;
    }
    if (workspace === "flats") {
      void refreshFlats(selectedTenantId, selectedSocietyId, selectedBuildingId);
      return;
    }
    if (workspace === "owners") {
      void refreshOwners(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "vendors") {
      void refreshVendors(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "expenses") {
      void refreshExpenses(selectedTenantId, selectedSocietyId);
      return;
    }
    if (workspace === "ownerships") {
      void refreshOwnerships(selectedTenantId, selectedSocietyId, selectedBuildingId, selectedFlatId);
      return;
    }
    if (workspace === "residents") {
      void refreshResidents(selectedTenantId, selectedSocietyId, selectedBuildingId, selectedFlatId);
      return;
    }
    if (workspace === "leaseAgreements") {
      void refreshLeaseAgreements(selectedTenantId, selectedSocietyId, selectedBuildingId, selectedFlatId);
      return;
    }

    void refreshSocieties(selectedTenantId);
    void refreshBuildings(selectedTenantId, selectedSocietyId);
    void refreshFlatTypes(selectedTenantId, selectedSocietyId);
    void refreshChartOfAccounts(selectedTenantId, selectedSocietyId);
    void refreshChargeTypes(selectedTenantId, selectedSocietyId);
    void refreshExpenseCategories(selectedTenantId, selectedSocietyId);
    void refreshBillingRules(selectedTenantId, selectedSocietyId);
    void refreshLateFeeRules(selectedTenantId, selectedSocietyId);
    void refreshScheduledJobs(selectedTenantId, selectedSocietyId);
    void refreshInvoices(selectedTenantId, selectedSocietyId, token, invoiceFilters);
    void refreshPaymentRegister(selectedTenantId, selectedSocietyId, token, paymentRegisterFilters);
    void refreshOutstanding(selectedTenantId, selectedSocietyId);
    void refreshOwners(selectedTenantId, selectedSocietyId);
    void refreshVendors(selectedTenantId, selectedSocietyId);
    void refreshExpenses(selectedTenantId, selectedSocietyId);
    void refreshBuildingFloors(selectedTenantId, selectedSocietyId, selectedBuildingId);
    void refreshWings(selectedTenantId, selectedSocietyId, selectedBuildingId);
    void refreshFlats(selectedTenantId, selectedSocietyId, selectedBuildingId);
    void refreshOwnerships(selectedTenantId, selectedSocietyId, selectedBuildingId, selectedFlatId);
    void refreshResidents(selectedTenantId, selectedSocietyId, selectedBuildingId, selectedFlatId);
    void refreshLeaseAgreements(selectedTenantId, selectedSocietyId, selectedBuildingId, selectedFlatId);
  }

  if (sessionState === "loading") {
    return <main className="status-screen">Loading</main>;
  }

  if (sessionState === "anonymous") {
    return (
      <main className="login-screen">
        <section className="login-panel">
          <div>
            <p className="eyebrow">Propelsync</p>
            <h1>Platform Console</h1>
          </div>
          <button type="button" onClick={() => void keycloak.login()}>
            Sign in
          </button>
          {error ? <p className="error-text">{error}</p> : null}
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-cluster">
          <button
            type="button"
            className="icon-button"
            aria-label={isSidebarCollapsed ? "Expand navigation" : "Collapse navigation"}
            onClick={() => setIsSidebarCollapsed((value) => !value)}
          >
            Menu
          </button>
          <div>
            <p className="eyebrow">Propelsync</p>
            <h1>Admin Console</h1>
          </div>
        </div>

        <div className="tenant-switcher">
          <label>
            Tenant
            <select value={selectedTenantId} onChange={(event) => selectTenant(event.target.value)}>
              {!tenants.length ? <option value="">No tenants</option> : null}
              {tenants.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Society
            <select
              value={selectedTenantSocietyId}
              disabled={!tenantSocieties.length}
              onChange={(event) => selectSociety(event.target.value)}
            >
              {!tenantSocieties.length ? <option value="">No societies</option> : null}
              {tenantSocieties.map((society) => (
                <option key={society.id} value={society.id}>
                  {society.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="session">
          <div className="session-text">
            <span>{userName}</span>
            <small>{userRoleLabel}</small>
          </div>
          <button
            type="button"
            className="secondary"
            onClick={() => {
              clearKeycloakTokens();
              void keycloak.logout();
            }}
          >
            Sign out
          </button>
        </div>
      </header>

      <div className={`shell-body ${isSidebarCollapsed ? "sidebar-collapsed" : ""}`}>
        <aside className="sidebar" aria-label="Section navigation">
          <div className="sidebar-section">
            <button
              type="button"
              className="sidebar-label-button"
              onClick={() =>
                setCollapsedSections((current) => ({ ...current, platform: !current.platform }))
              }
            >
              <span>Platform</span>
              <span className="sidebar-chevron">{collapsedSections.platform ? "+" : "-"}</span>
            </button>
            {!collapsedSections.platform ? (
              <div className="sidebar-items">
                <button
                  type="button"
                  className={`nav-item ${workspace === "tenants" ? "active" : ""}`}
                  disabled={!isPlatformUser}
                  onClick={() => setWorkspace("tenants")}
                  title="Tenants"
                >
                  <span className="nav-icon">T</span>
                  <span className="nav-text">Tenants</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "users" ? "active" : ""}`}
                  disabled={!canManageUsers || !selectedTenantId}
                  onClick={() => setWorkspace("users")}
                  title="Users"
                >
                  <span className="nav-icon">U</span>
                  <span className="nav-text">Users</span>
                </button>
              </div>
            ) : null}
          </div>

          <div className="sidebar-section">
            <button
              type="button"
              className="sidebar-label-button"
              onClick={() =>
                setCollapsedSections((current) => ({ ...current, society: !current.society }))
              }
            >
              <span>Society Setup</span>
              <span className="sidebar-chevron">{collapsedSections.society ? "+" : "-"}</span>
            </button>
            {!collapsedSections.society ? (
              <div className="sidebar-items">
                <button
                  type="button"
                  className={`nav-item ${workspace === "dashboard" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("dashboard")}
                  title="Dashboard"
                >
                  <span className="nav-icon">D</span>
                  <span className="nav-text">Dashboard</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "societies" ? "active" : ""}`}
                  disabled={!canManageTenantSocieties}
                  onClick={() => setWorkspace("societies")}
                  title="Societies"
                >
                  <span className="nav-icon">S</span>
                  <span className="nav-text">Societies</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "buildings" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("buildings")}
                  title="Buildings"
                >
                  <span className="nav-icon">B</span>
                  <span className="nav-text">Buildings</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "flatTypes" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("flatTypes")}
                  title="Flat Types"
                >
                  <span className="nav-icon">Y</span>
                  <span className="nav-text">Flat Types</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "owners" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("owners")}
                  title="Owners"
                >
                  <span className="nav-icon">O</span>
                  <span className="nav-text">Owners</span>
                </button>
              </div>
            ) : null}
          </div>

          <div className="sidebar-section">
            <button
              type="button"
              className="sidebar-label-button"
              onClick={() =>
                setCollapsedSections((current) => ({ ...current, building: !current.building }))
              }
            >
              <span>Building Setup</span>
              <span className="sidebar-chevron">{collapsedSections.building ? "+" : "-"}</span>
            </button>
            {!collapsedSections.building ? (
              <div className="sidebar-items">
                <button
                  type="button"
                  className={`nav-item ${workspace === "floors" ? "active" : ""}`}
                  disabled={!selectedBuildingId}
                  onClick={() => setWorkspace("floors")}
                  title="Floors"
                >
                  <span className="nav-icon">L</span>
                  <span className="nav-text">Floors</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "wings" ? "active" : ""}`}
                  disabled={!selectedBuildingId}
                  onClick={() => setWorkspace("wings")}
                  title="Wings"
                >
                  <span className="nav-icon">W</span>
                  <span className="nav-text">Wings</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "flats" ? "active" : ""}`}
                  disabled={!selectedBuildingId}
                  onClick={() => setWorkspace("flats")}
                  title="Flats"
                >
                  <span className="nav-icon">F</span>
                  <span className="nav-text">Flats</span>
                </button>
              </div>
            ) : null}
          </div>

          <div className="sidebar-section">
            <button
              type="button"
              className="sidebar-label-button"
              onClick={() =>
                setCollapsedSections((current) => ({ ...current, flat: !current.flat }))
              }
            >
              <span>Flat Setup</span>
              <span className="sidebar-chevron">{collapsedSections.flat ? "+" : "-"}</span>
            </button>
            {!collapsedSections.flat ? (
              <div className="sidebar-items">
                <button
                  type="button"
                  className={`nav-item ${workspace === "ownerships" ? "active" : ""}`}
                  disabled={!selectedFlatId}
                  onClick={() => setWorkspace("ownerships")}
                  title="Ownerships"
                >
                  <span className="nav-icon">A</span>
                  <span className="nav-text">Ownerships</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "flatLedgers" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("flatLedgers")}
                  title="Flat Ledger"
                >
                  <span className="nav-icon">G</span>
                  <span className="nav-text">Flat Ledger</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "residents" ? "active" : ""}`}
                  disabled={!selectedFlatId}
                  onClick={() => setWorkspace("residents")}
                  title="Residents"
                >
                  <span className="nav-icon">R</span>
                  <span className="nav-text">Residents</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "leaseAgreements" ? "active" : ""}`}
                  disabled={!selectedFlatId}
                  onClick={() => setWorkspace("leaseAgreements")}
                  title="Lease Agreements"
                >
                  <span className="nav-icon">L</span>
                  <span className="nav-text">Leases</span>
                </button>
              </div>
            ) : null}
          </div>

          <div className="sidebar-section">
            <button
              type="button"
              className="sidebar-label-button"
              onClick={() =>
                setCollapsedSections((current) => ({ ...current, billing: !current.billing }))
              }
            >
              <span>Billing Setup</span>
              <span className="sidebar-chevron">{collapsedSections.billing ? "+" : "-"}</span>
            </button>
            {!collapsedSections.billing ? (
              <div className="sidebar-items">
                <button
                  type="button"
                  className={`nav-item ${workspace === "chartOfAccounts" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("chartOfAccounts")}
                  title="Chart of Accounts"
                >
                  <span className="nav-icon">A</span>
                  <span className="nav-text">Chart Accounts</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "bankCashAccounts" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("bankCashAccounts")}
                  title="Bank & Cash"
                >
                  <span className="nav-icon">K</span>
                  <span className="nav-text">Bank & Cash</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "accountLedgers" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("accountLedgers")}
                  title="Account Ledger"
                >
                  <span className="nav-icon">L</span>
                  <span className="nav-text">Account Ledger</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "openingBalances" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("openingBalances")}
                  title="Opening Balances"
                >
                  <span className="nav-icon">O</span>
                  <span className="nav-text">Opening Balances</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "trialBalance" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("trialBalance")}
                  title="Trial Balance"
                >
                  <span className="nav-icon">B</span>
                  <span className="nav-text">Trial Balance</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "journals" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("journals")}
                  title="Journal Entries"
                >
                  <span className="nav-icon">J</span>
                  <span className="nav-text">Journals</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "accountTransfers" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("accountTransfers")}
                  title="Account Transfers"
                >
                  <span className="nav-icon">T</span>
                  <span className="nav-text">Transfers</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "otherIncome" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("otherIncome")}
                  title="Other Income"
                >
                  <span className="nav-icon">R</span>
                  <span className="nav-text">Other Income</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "chargeTypes" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("chargeTypes")}
                  title="Charge Types"
                >
                  <span className="nav-icon">C</span>
                  <span className="nav-text">Charge Types</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "expenseCategories" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("expenseCategories")}
                  title="Expense Categories"
                >
                  <span className="nav-icon">E</span>
                  <span className="nav-text">Expense Categories</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "numberingSettings" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("numberingSettings")}
                  title="Numbering"
                >
                  <span className="nav-icon">N</span>
                  <span className="nav-text">Numbering</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "billingRules" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("billingRules")}
                  title="Billing Rules"
                >
                  <span className="nav-icon">B</span>
                  <span className="nav-text">Billing Rules</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "lateFeeRules" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("lateFeeRules")}
                  title="Penalty Rules"
                >
                  <span className="nav-icon">F</span>
                  <span className="nav-text">Penalty Rules</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "invoiceGeneration" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("invoiceGeneration")}
                  title="Generate Invoices"
                >
                  <span className="nav-icon">G</span>
                  <span className="nav-text">Generate</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "lateFeeApplication" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("lateFeeApplication")}
                  title="Apply Penalties"
                >
                  <span className="nav-icon">Y</span>
                  <span className="nav-text">Apply Penalties</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "scheduledJobs" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("scheduledJobs")}
                  title="Scheduled Jobs"
                >
                  <span className="nav-icon">Q</span>
                  <span className="nav-text">Scheduled Jobs</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "manualInvoices" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("manualInvoices")}
                  title="Manual Invoice"
                >
                  <span className="nav-icon">M</span>
                  <span className="nav-text">Manual Invoice</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "invoices" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("invoices")}
                  title="Invoices"
                >
                  <span className="nav-icon">I</span>
                  <span className="nav-text">Invoices</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "payments" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("payments")}
                  title="Payments"
                >
                  <span className="nav-icon">P</span>
                  <span className="nav-text">Payments</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "outstanding" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("outstanding")}
                  title="Outstanding"
                >
                  <span className="nav-icon">O</span>
                  <span className="nav-text">Outstanding</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "vendors" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("vendors")}
                  title="Vendors"
                >
                  <span className="nav-icon">V</span>
                  <span className="nav-text">Vendors</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "expenses" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("expenses")}
                  title="Expenses"
                >
                  <span className="nav-icon">X</span>
                  <span className="nav-text">Expenses</span>
                </button>
              </div>
            ) : null}
          </div>

          <div className="sidebar-section">
            <button
              type="button"
              className="sidebar-label-button"
              onClick={() =>
                setCollapsedSections((current) => ({ ...current, reports: !current.reports }))
              }
            >
              <span>Reports</span>
              <span className="sidebar-chevron">{collapsedSections.reports ? "+" : "-"}</span>
            </button>
            {!collapsedSections.reports ? (
              <div className="sidebar-items">
                <button
                  type="button"
                  className={`nav-item ${workspace === "operationalReports" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("operationalReports")}
                  title="Operational Reports"
                >
                  <span className="nav-icon">R</span>
                  <span className="nav-text">Operational Reports</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "paymentRegister" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("paymentRegister")}
                  title="Payment Register"
                >
                  <span className="nav-icon">P</span>
                  <span className="nav-text">Payment Register</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "incomeExpense" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("incomeExpense")}
                  title="Income vs Expense"
                >
                  <span className="nav-icon">I</span>
                  <span className="nav-text">Income vs Expense</span>
                </button>
                <button
                  type="button"
                  className={`nav-item ${workspace === "balanceSheet" ? "active" : ""}`}
                  disabled={!selectedSocietyId}
                  onClick={() => setWorkspace("balanceSheet")}
                  title="Balance Sheet"
                >
                  <span className="nav-icon">S</span>
                  <span className="nav-text">Balance Sheet</span>
                </button>
              </div>
            ) : null}
          </div>
        </aside>

        <section className="content-area">
          <div className="page-heading">
            <div>
              <p className="eyebrow">
                {breadcrumbLabel}
              </p>
              <h2>
                {workspace === "tenants"
                  ? "Tenant Management"
                  : workspace === "users"
                    ? "User Management"
                  : workspace === "dashboard"
                    ? "Dashboard"
                  : workspace === "societies"
                    ? "Society Management"
                  : workspace === "buildings"
                    ? "Building Management"
                    : workspace === "floors"
                      ? "Floor Management"
                    : workspace === "flatTypes"
                      ? "Flat Type Management"
                      : workspace === "chartOfAccounts"
                        ? "Chart of Accounts"
                        : workspace === "bankCashAccounts"
                          ? "Bank & Cash Accounts"
                        : workspace === "accountLedgers"
                          ? "Account Ledger"
                        : workspace === "flatLedgers"
                          ? "Flat Ledger"
                          : workspace === "openingBalances"
                          ? "Opening Balances"
                        : workspace === "trialBalance"
                          ? "Trial Balance"
                        : workspace === "operationalReports"
                          ? "Operational Reports"
                        : workspace === "paymentRegister"
                          ? "Payment Register"
                            : workspace === "incomeExpense"
                              ? "Income vs Expense"
                            : workspace === "balanceSheet"
                              ? "Balance Sheet"
                        : workspace === "journals"
                          ? "Journal Entries"
                          : workspace === "accountTransfers"
                            ? "Account Transfers"
                            : workspace === "otherIncome"
                              ? "Other Income Receipts"
                            : workspace === "chargeTypes"
                              ? "Charge Type Management"
                      : workspace === "expenseCategories"
                        ? "Expense Category Management"
                      : workspace === "numberingSettings"
                        ? "Numbering Settings"
                        : workspace === "billingRules"
                          ? "Billing Rule Management"
                        : workspace === "lateFeeRules"
                          ? "Penalty Rule Management"
                        : workspace === "lateFeeApplication"
                          ? "Apply Penalties"
                        : workspace === "scheduledJobs"
                          ? "Scheduled Jobs"
                        : workspace === "invoiceGeneration"
                          ? "Invoice Generation"
                        : workspace === "manualInvoices"
                          ? "Manual Invoice"
                        : workspace === "invoices"
                          ? "Invoices"
                        : workspace === "payments"
                          ? "Payments"
                        : workspace === "outstanding"
                          ? "Outstanding"
                        : workspace === "vendors"
                          ? "Vendor Management"
                        : workspace === "expenses"
                          ? "Expenses"
                        : workspace === "wings"
                          ? "Wing Management"
                          : workspace === "flats"
                            ? "Flat Management"
                            : workspace === "owners"
                              ? "Owner Management"
                              : workspace === "ownerships"
                                ? "Flat Ownerships"
                              : workspace === "leaseAgreements"
                                ? "Lease Agreements"
                                : "Resident Management"}
              </h2>
            </div>
            <div className="page-actions">
              {workspace === "flats" ? (
                <button
                  type="button"
                  className="secondary"
                  onClick={isFlatImportOpen ? resetFlatImport : openFlatImport}
                  disabled={!selectedBuildingId}
                >
                  {isFlatImportOpen ? "Close Import" : "Bulk Import"}
                </button>
              ) : null}
              {workspace === "chartOfAccounts" ? (
                <button
                  type="button"
                  className="secondary"
                  onClick={isChartOfAccountImportOpen ? resetChartOfAccountImport : openChartOfAccountImport}
                  disabled={!selectedSocietyId}
                >
                  {isChartOfAccountImportOpen ? "Close Import" : "Bulk Import"}
                </button>
              ) : null}
              {createActionLabel ? (
                <button
                  type="button"
                  onClick={isCurrentFormOpen ? closeCurrentForm : openCurrentCreateForm}
                  disabled={!isCurrentFormOpen && !canOpenCurrentForm}
                >
                  {isCurrentFormOpen ? "Close Form" : createActionLabel}
                </button>
              ) : null}
              <button
                type="button"
                className="secondary"
                onClick={refreshCurrentWorkspace}
              >
                Refresh
              </button>
            </div>
          </div>

          {workspace === "dashboard" ? (
            <section className="metrics-grid">
              <article className="metric-tile">
                <span>Total Tenants</span>
                <strong>{tenants.length}</strong>
              </article>
              <article className="metric-tile">
                <span>Active Tenants</span>
                <strong>{activeTenantCount}</strong>
              </article>
              <article className="metric-tile">
                <span>Societies</span>
                <strong>{societies.length}</strong>
              </article>
              <article className="metric-tile">
                <span>Active Societies</span>
                <strong>{activeSocietyCount}</strong>
              </article>
              <article className="metric-tile">
                <span>Buildings</span>
                <strong>{buildings.length}</strong>
              </article>
              <article className="metric-tile">
                <span>Active Buildings</span>
                <strong>{activeBuildingCount}</strong>
              </article>
              <article className="metric-tile">
                <span>Floors</span>
                <strong>{buildingFloors.length}</strong>
              </article>
              <article className="metric-tile">
                <span>Active Floors</span>
                <strong>{activeBuildingFloorCount}</strong>
              </article>
              <article className="metric-tile">
                <span>Flat Types</span>
                <strong>{flatTypes.length}</strong>
              </article>
              <article className="metric-tile">
                <span>Active Types</span>
                <strong>{activeFlatTypeCount}</strong>
              </article>
              <article className="metric-tile">
                <span>Charge Types</span>
                <strong>{chargeTypes.length}</strong>
              </article>
              <article className="metric-tile">
                <span>Active Charges</span>
                <strong>{activeChargeTypeCount}</strong>
              </article>
              <article className="metric-tile">
                <span>Billing Rules</span>
                <strong>{billingRules.length}</strong>
              </article>
              <article className="metric-tile">
                <span>Active Rules</span>
                <strong>{activeBillingRuleCount}</strong>
              </article>
              <article className="metric-tile">
                <span>Invoices</span>
                <strong>{invoices.length}</strong>
              </article>
              <article className="metric-tile">
                <span>Open Invoices</span>
                <strong>{openInvoiceCount}</strong>
              </article>
              <article className="metric-tile">
                <span>Ledger Accounts</span>
                <strong>{chartOfAccounts.length}</strong>
              </article>
              <article className="metric-tile">
                <span>Active Accounts</span>
                <strong>{activeChartOfAccountCount}</strong>
              </article>
              <article className="metric-tile">
                <span>Wings</span>
                <strong>{wings.length}</strong>
              </article>
              <article className="metric-tile">
                <span>Active Wings</span>
                <strong>{activeWingCount}</strong>
              </article>
              <article className="metric-tile">
                <span>Flats</span>
                <strong>{flats.length}</strong>
              </article>
              <article className="metric-tile">
                <span>Active Flats</span>
                <strong>{activeFlatCount}</strong>
              </article>
              <article className="metric-tile">
                <span>Owners</span>
                <strong>{owners.length}</strong>
              </article>
              <article className="metric-tile">
                <span>Active Owners</span>
                <strong>{activeOwnerCount}</strong>
              </article>
              <article className="metric-tile">
                <span>Ownerships</span>
                <strong>{ownerships.length}</strong>
              </article>
              <article className="metric-tile">
                <span>Current Owners</span>
                <strong>{activeOwnershipCount}</strong>
              </article>
              <article className="metric-tile">
                <span>Residents</span>
                <strong>{residents.length}</strong>
              </article>
              <article className="metric-tile">
                <span>Active Residents</span>
                <strong>{activeResidentCount}</strong>
              </article>
            </section>
          ) : null}

          {showBuildingContext ? (
            <section className="context-strip">
              <label>
                Building
                <select
                  value={selectedBuildingId}
                  disabled={!buildings.length}
                  onChange={(event) => selectBuilding(event.target.value)}
                >
                  {!buildings.length ? <option value="">No buildings</option> : null}
                  {buildings.map((building) => (
                    <option key={building.id} value={building.id}>
                      {building.name}
                    </option>
                  ))}
                </select>
              </label>
              {showFlatContext ? (
                <label>
                  Flat
                  <select
                    value={selectedFlatId}
                    disabled={!flats.length}
                    onChange={(event) => selectFlat(event.target.value)}
                  >
                    {!flats.length ? <option value="">No flats</option> : null}
                    {flats.map((flat) => (
                      <option key={flat.id} value={flat.id}>
                        {flat.flat_number}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
            </section>
          ) : null}

          {notice || error ? (
            <div className={`message-bar ${error ? "error" : "notice"}`}>
              {error || notice}
            </div>
          ) : null}

          {workspace === "dashboard" ? null : workspace === "tenants" ? (
            !isPlatformUser ? (
              <section className="empty-state-panel">
                <h2>Tenant administration is restricted</h2>
                <p>Select an available society setup area from the sidebar.</p>
              </section>
            ) : (
            <section className={`workspace ${isTenantFormOpen ? "" : "registry-only"}`}>
              {isTenantFormOpen ? (
              <form className="panel-form" onSubmit={handleTenantSubmit}>
                <div className="form-title-row">
                  <h2>{editingTenantId ? "Edit Tenant" : "Create Tenant"}</h2>
                  {editingTenantId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingTenantId(null);
                        setTenantForm(tenantFormDefaults);
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <label>
                  Name
                  <input
                    required
                    maxLength={255}
                    value={tenantForm.name}
                    onChange={(event) => setTenantForm({ ...tenantForm, name: event.target.value })}
                  />
                </label>
                <label>
                  Slug
                  <input
                    required
                    maxLength={100}
                    pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$"
                    disabled={Boolean(editingTenantId)}
                    value={tenantForm.slug}
                    onChange={(event) => setTenantForm({ ...tenantForm, slug: event.target.value })}
                  />
                </label>
                <div className="form-grid">
                  <label>
                    Plan
                    <select
                      required
                      value={tenantForm.subscription_plan}
                      onChange={(event) =>
                        setTenantForm({ ...tenantForm, subscription_plan: event.target.value })
                      }
                    >
                      {tenantPlans.map((plan) => (
                        <option key={plan} value={plan}>
                          {plan}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Currency
                    <select
                      required
                      value={tenantForm.currency}
                      onChange={(event) =>
                        setTenantForm({ ...tenantForm, currency: event.target.value })
                      }
                    >
                      {currencies.map((currency) => (
                        <option key={currency} value={currency}>
                          {currency}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <label>
                  Billing Email
                  <input
                    type="email"
                    value={tenantForm.billing_email}
                    onChange={(event) =>
                      setTenantForm({ ...tenantForm, billing_email: event.target.value })
                    }
                  />
                </label>
                <label>
                  Phone
                  <input
                    maxLength={30}
                    value={tenantForm.phone}
                    onChange={(event) => setTenantForm({ ...tenantForm, phone: event.target.value })}
                  />
                </label>
                <div className="form-grid">
                  <label>
                    Timezone
                    <select
                      required
                      value={tenantForm.timezone}
                      onChange={(event) =>
                        setTenantForm({ ...tenantForm, timezone: event.target.value })
                      }
                    >
                      {timezones.map((timezone) => (
                        <option key={timezone} value={timezone}>
                          {timezone}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Locale
                    <select
                      required
                      value={tenantForm.locale}
                      onChange={(event) => setTenantForm({ ...tenantForm, locale: event.target.value })}
                    >
                      {locales.map((locale) => (
                        <option key={locale} value={locale}>
                          {locale}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <button type="submit" disabled={isSaving}>
                  {isSaving ? "Saving" : editingTenantId ? "Save Tenant" : "Create Tenant"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Tenant Registry</h2>
                  <span className="record-count">{isLoadingTenants ? "Loading" : `${tenants.length} records`}</span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Slug</th>
                        <th>Status</th>
                        <th>Plan</th>
                        <th>Currency</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tenants.map((tenant) => (
                        <tr key={tenant.id}>
                          <td>{tenant.name}</td>
                          <td>{tenant.slug}</td>
                          <td><StatusPill status={tenant.status} /></td>
                          <td>{tenant.subscription_plan}</td>
                          <td>{tenant.currency}</td>
                          <td>
                            <div className="row-actions">
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => {
                                  selectTenant(tenant.id);
                                  setWorkspace("societies");
                                }}
                              >
                                Open
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => startEditTenant(tenant)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => void handleTenantStatusChange(tenant)}
                              >
                                {tenant.status === "active" ? "Suspend" : "Activate"}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                      {!tenants.length && !isLoadingTenants ? (
                        <tr>
                          <td colSpan={6} className="empty-cell">
                            No tenants yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
            )
          ) : workspace === "users" ? (
            !canManageUsers ? (
              <section className="empty-state-panel">
                <h2>User management is restricted</h2>
                <p>Select a tenant or society where you have administration access.</p>
              </section>
            ) : (
            <section className={`workspace ${isManagedUserFormOpen ? "" : "registry-only"}`}>
              {isManagedUserFormOpen ? (
              <form className="panel-form" onSubmit={handleManagedUserSubmit}>
                <h2>Create User</h2>
                <div className="context-card">
                  <span>Selected Tenant</span>
                  <strong>{selectedTenant?.name ?? "Select a tenant"}</strong>
                </div>
                <label>
                  Full Name
                  <input
                    required
                    maxLength={255}
                    value={managedUserForm.full_name}
                    onChange={(event) =>
                      setManagedUserForm({ ...managedUserForm, full_name: event.target.value })
                    }
                  />
                </label>
                <div className="form-grid">
                  <label>
                    Email
                    <input
                      type="email"
                      value={managedUserForm.email}
                      onChange={(event) =>
                        setManagedUserForm({ ...managedUserForm, email: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Mobile
                    <input
                      maxLength={20}
                      value={managedUserForm.mobile_number}
                      onChange={(event) =>
                        setManagedUserForm({ ...managedUserForm, mobile_number: event.target.value })
                      }
                    />
                  </label>
                </div>
                <label>
                  Temporary Password
                  <input
                    required
                    type="password"
                    minLength={8}
                    maxLength={128}
                    value={managedUserForm.temporary_password}
                    onChange={(event) =>
                      setManagedUserForm({ ...managedUserForm, temporary_password: event.target.value })
                    }
                  />
                </label>
                {canManageTenantSocieties ? (
                  <label className="checkbox-field">
                    <input
                      type="checkbox"
                      checked={managedUserForm.tenant_admin}
                      onChange={(event) =>
                        setManagedUserForm({ ...managedUserForm, tenant_admin: event.target.checked })
                      }
                    />
                    Tenant admin
                  </label>
                ) : null}
                <div className="form-grid">
                  <label>
                    Society
                    <select
                      value={managedUserForm.society_id}
                      onChange={(event) =>
                        setManagedUserForm({ ...managedUserForm, society_id: event.target.value })
                      }
                    >
                      <option value="">No society role</option>
                      {tenantSocieties.map((society) => (
                        <option key={society.id} value={society.id}>
                          {society.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Society Role
                    <select
                      value={managedUserForm.society_role}
                      disabled={!managedUserForm.society_id}
                      onChange={(event) =>
                        setManagedUserForm({ ...managedUserForm, society_role: event.target.value })
                      }
                    >
                      <option value="">Select role</option>
                      {societyRoles.map((role) => (
                        <option key={role} value={role}>
                          {role}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <button
                  type="submit"
                  disabled={
                    isSaving ||
                    !selectedTenantId ||
                    (!managedUserForm.email.trim() && !managedUserForm.mobile_number.trim()) ||
                    Boolean(managedUserForm.society_id && !managedUserForm.society_role)
                  }
                >
                  {isSaving ? "Saving" : "Create User"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>User Registry</h2>
                  <span className="record-count">
                    {isLoadingManagedUsers ? "Loading" : `${managedUsers.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Identity</th>
                        <th>Tenant Roles</th>
                        <th>Society Roles</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {managedUsers.map((user) => {
                        const tenantRoles = user.tenant_memberships
                          .map((membership) => `${membership.role} (${membership.status})`)
                          .join(", ");
                        const societyRoleText = user.society_memberships
                          .map(
                            (membership) =>
                              `${membership.society_name}: ${membership.role} (${membership.status})`
                          )
                          .join(", ");
                        const hasActiveMembership =
                          user.tenant_memberships.some((membership) => membership.status === "active") ||
                          user.society_memberships.some((membership) => membership.status === "active");
                        return (
                          <tr key={user.id}>
                            <td>{user.full_name}</td>
                            <td>{[user.email, user.mobile_number].filter(Boolean).join(" / ")}</td>
                            <td>{tenantRoles || "None"}</td>
                            <td>{societyRoleText || "None"}</td>
                            <td><StatusPill status={hasActiveMembership ? "active" : "suspended"} /></td>
                            <td>
                              <div className="row-actions">
                                <button
                                  type="button"
                                  className="secondary compact"
                                  disabled={user.is_platform_superuser}
                                  onClick={() => void handleManagedUserStatusChange(user)}
                                >
                                  {hasActiveMembership ? "Suspend" : "Activate"}
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                      {!managedUsers.length && !isLoadingManagedUsers ? (
                        <tr>
                          <td colSpan={6} className="empty-cell">
                            No users assigned in this tenant yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
            )
          ) : workspace === "societies" ? (
            !canManageTenantSocieties ? (
              <section className="empty-state-panel">
                <h2>Society administration is restricted</h2>
                <p>Select a society and continue with the setup sections available to your role.</p>
              </section>
            ) : (
            <section className={`workspace ${isSocietyFormOpen ? "" : "registry-only"}`}>
              {isSocietyFormOpen ? (
              <form className="panel-form" onSubmit={handleSocietySubmit}>
                <div className="form-title-row">
                  <h2>{editingSocietyId ? "Edit Society" : "Create Society"}</h2>
                  {editingSocietyId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingSocietyId(null);
                        setSocietyForm(societyFormDefaults);
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <label>
                  Name
                  <input
                    required
                    maxLength={255}
                    value={societyForm.name}
                    onChange={(event) => setSocietyForm({ ...societyForm, name: event.target.value })}
                  />
                </label>
                <label>
                  Registration Number
                  <input
                    maxLength={100}
                    value={societyForm.registration_number}
                    onChange={(event) =>
                      setSocietyForm({ ...societyForm, registration_number: event.target.value })
                    }
                  />
                </label>
                <label>
                  Address Line 1
                  <input
                    maxLength={255}
                    value={societyForm.address_line1}
                    onChange={(event) =>
                      setSocietyForm({ ...societyForm, address_line1: event.target.value })
                    }
                  />
                </label>
                <label>
                  Address Line 2
                  <input
                    maxLength={255}
                    value={societyForm.address_line2}
                    onChange={(event) =>
                      setSocietyForm({ ...societyForm, address_line2: event.target.value })
                    }
                  />
                </label>
                <div className="form-grid">
                  <label>
                    City
                    <input
                      maxLength={100}
                      value={societyForm.city}
                      onChange={(event) =>
                        setSocietyForm({ ...societyForm, city: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    State
                    <input
                      maxLength={100}
                      value={societyForm.state}
                      onChange={(event) =>
                        setSocietyForm({ ...societyForm, state: event.target.value })
                      }
                    />
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Currency
                    <select
                      required
                      value={societyForm.currency}
                      onChange={(event) =>
                        setSocietyForm({ ...societyForm, currency: event.target.value })
                      }
                    >
                      {currencies.map((currency) => (
                        <option key={currency} value={currency}>
                          {currency}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Financial Year
                    <select
                      required
                      value={societyForm.financial_year_start_month}
                      onChange={(event) =>
                        setSocietyForm({
                          ...societyForm,
                          financial_year_start_month: Number(event.target.value)
                        })
                      }
                    >
                      {financialYearMonths.map((month) => (
                        <option key={month.value} value={month.value}>
                          {month.label}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Timezone
                    <select
                      required
                      value={societyForm.timezone}
                      onChange={(event) =>
                        setSocietyForm({ ...societyForm, timezone: event.target.value })
                      }
                    >
                      {timezones.map((timezone) => (
                        <option key={timezone} value={timezone}>
                          {timezone}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Locale
                    <select
                      required
                      value={societyForm.locale}
                      onChange={(event) =>
                        setSocietyForm({ ...societyForm, locale: event.target.value })
                      }
                    >
                      {locales.map((locale) => (
                        <option key={locale} value={locale}>
                          {locale}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <label>
                  Receivable Account
                  <select
                    value={societyForm.receivable_account_id}
                    onChange={(event) =>
                      setSocietyForm({ ...societyForm, receivable_account_id: event.target.value })
                    }
                  >
                    <option value="">Configure after chart of accounts</option>
                    {activeAssetAccounts.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.account_code} - {account.account_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Payable Account
                  <select
                    value={societyForm.payable_account_id}
                    onChange={(event) =>
                      setSocietyForm({ ...societyForm, payable_account_id: event.target.value })
                    }
                  >
                    <option value="">Configure after chart of accounts</option>
                    {activeLiabilityAccounts.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.account_code} - {account.account_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Member Advance Account
                  <select
                    value={societyForm.member_advance_account_id}
                    onChange={(event) =>
                      setSocietyForm({ ...societyForm, member_advance_account_id: event.target.value })
                    }
                  >
                    <option value="">Configure after chart of accounts</option>
                    {activeLiabilityAccounts.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.account_code} - {account.account_name}
                      </option>
                    ))}
                  </select>
                </label>
                <button type="submit" disabled={isSaving || !selectedTenantId}>
                  {isSaving ? "Saving" : editingSocietyId ? "Save Society" : "Create Society"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Society Registry</h2>
                  <span className="record-count">
                    {isLoadingSocieties ? "Loading" : `${societies.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Registration</th>
                        <th>Status</th>
                        <th>Location</th>
                        <th>Currency</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {societies.map((society) => (
                        <tr key={society.id}>
                          <td>{society.name}</td>
                          <td>{society.registration_number ?? ""}</td>
                          <td><StatusPill status={society.status} /></td>
                          <td>{[society.city, society.state].filter(Boolean).join(", ")}</td>
                          <td>{society.currency}</td>
                          <td>
                            <div className="row-actions">
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => {
                                  selectSociety(society.id);
                                  setWorkspace("buildings");
                                }}
                              >
                                Setup
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => startEditSociety(society)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => void handleSocietyStatusChange(society)}
                              >
                                {society.status === "active" ? "Suspend" : "Activate"}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                      {!societies.length && !isLoadingSocieties ? (
                        <tr>
                          <td colSpan={6} className="empty-cell">
                            No societies for this tenant yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
            )
          ) : workspace === "buildings" ? (
            <section className={`workspace ${isBuildingFormOpen ? "" : "registry-only"}`}>
              {isBuildingFormOpen ? (
              <form className="panel-form" onSubmit={handleBuildingSubmit}>
                <div className="form-title-row">
                  <h2>{editingBuildingId ? "Edit Building" : "Create Building"}</h2>
                  {editingBuildingId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingBuildingId(null);
                        setBuildingForm(buildingFormDefaults);
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Society</span>
                  <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                </div>

                <label>
                  Building Name
                  <input
                    required
                    maxLength={255}
                    value={buildingForm.name}
                    onChange={(event) =>
                      setBuildingForm({ ...buildingForm, name: event.target.value })
                    }
                  />
                </label>
                <label>
                  Building Code
                  <input
                    maxLength={50}
                    value={buildingForm.code}
                    onChange={(event) =>
                      setBuildingForm({ ...buildingForm, code: event.target.value })
                    }
                  />
                </label>
                <button type="submit" disabled={isSaving || !selectedTenantId || !selectedSocietyId}>
                  {isSaving ? "Saving" : editingBuildingId ? "Save Building" : "Create Building"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Building Registry</h2>
                  <span className="record-count">
                    {isLoadingBuildings ? "Loading" : `${buildings.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Code</th>
                        <th>Status</th>
                        <th>Society</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {buildings.map((building) => (
                        <tr key={building.id}>
                          <td>{building.name}</td>
                          <td>{building.code ?? ""}</td>
                          <td><StatusPill status={building.status} /></td>
                          <td>{selectedSociety?.name ?? ""}</td>
                          <td>
                            <div className="row-actions">
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => {
                                  selectBuilding(building.id);
                                  setWorkspace("floors");
                                }}
                              >
                                Floors
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => {
                                  selectBuilding(building.id);
                                  setWorkspace("wings");
                                }}
                              >
                                Wings
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => {
                                  selectBuilding(building.id);
                                  setWorkspace("flats");
                                }}
                              >
                                Flats
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => startEditBuilding(building)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => void handleBuildingStatusChange(building)}
                              >
                                {building.status === "active" ? "Suspend" : "Activate"}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                      {!buildings.length && !isLoadingBuildings ? (
                        <tr>
                          <td colSpan={5} className="empty-cell">
                            No buildings for this society yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : workspace === "floors" ? (
            <section className={`workspace ${isBuildingFloorFormOpen ? "" : "registry-only"}`}>
              {isBuildingFloorFormOpen ? (
              <form className="panel-form" onSubmit={handleBuildingFloorSubmit}>
                <div className="form-title-row">
                  <h2>{editingBuildingFloorId ? "Edit Floor" : "Create Floor"}</h2>
                  {editingBuildingFloorId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingBuildingFloorId(null);
                        setBuildingFloorForm(buildingFloorFormDefaults);
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Building</span>
                  <strong>{selectedBuilding?.name ?? "Select a building"}</strong>
                </div>

                <label>
                  Floor Label
                  <input
                    required
                    maxLength={100}
                    value={buildingFloorForm.floor_label}
                    onChange={(event) =>
                      setBuildingFloorForm({ ...buildingFloorForm, floor_label: event.target.value })
                    }
                  />
                </label>
                <label>
                  Display Order
                  <input
                    required
                    type="number"
                    value={buildingFloorForm.floor_number}
                    onChange={(event) =>
                      setBuildingFloorForm({
                        ...buildingFloorForm,
                        floor_number: Number(event.target.value)
                      })
                    }
                  />
                </label>
                <button
                  type="submit"
                  disabled={
                    isSaving ||
                    !selectedTenantId ||
                    !selectedSocietyId ||
                    !selectedBuildingId ||
                    !buildingFloorForm.floor_label.trim() ||
                    Number.isNaN(Number(buildingFloorForm.floor_number))
                  }
                >
                  {isSaving ? "Saving" : editingBuildingFloorId ? "Save Floor" : "Create Floor"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Floor Registry</h2>
                  <span className="record-count">
                    {isLoadingBuildingFloors ? "Loading" : `${buildingFloors.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Label</th>
                        <th>Display Order</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {buildingFloors.map((floor) => (
                        <tr key={floor.id}>
                          <td>{floor.floor_label}</td>
                          <td>{floor.floor_number}</td>
                          <td><StatusPill status={floor.status} /></td>
                          <td>
                            <div className="row-actions">
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => startEditBuildingFloor(floor)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => void handleBuildingFloorStatusChange(floor)}
                              >
                                {floor.status === "active" ? "Inactivate" : "Activate"}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                      {!buildingFloors.length && !isLoadingBuildingFloors ? (
                        <tr>
                          <td colSpan={4} className="empty-cell">
                            No floors for this building yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : workspace === "flatTypes" ? (
            <section className={`workspace ${isFlatTypeFormOpen ? "" : "registry-only"}`}>
              {isFlatTypeFormOpen ? (
              <form className="panel-form" onSubmit={handleFlatTypeSubmit}>
                <div className="form-title-row">
                  <h2>{editingFlatTypeId ? "Edit Flat Type" : "Create Flat Type"}</h2>
                  {editingFlatTypeId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingFlatTypeId(null);
                        setFlatTypeForm(flatTypeFormDefaults);
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Society</span>
                  <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                </div>

                <label>
                  Name
                  <input
                    required
                    maxLength={255}
                    value={flatTypeForm.name}
                    onChange={(event) => setFlatTypeForm({ ...flatTypeForm, name: event.target.value })}
                  />
                </label>
                <label>
                  Code
                  <input
                    maxLength={50}
                    value={flatTypeForm.code}
                    onChange={(event) => setFlatTypeForm({ ...flatTypeForm, code: event.target.value })}
                  />
                </label>
                <label>
                  Category
                  <select
                    required
                    value={flatTypeForm.unit_category}
                    onChange={(event) =>
                      setFlatTypeForm({ ...flatTypeForm, unit_category: event.target.value })
                    }
                  >
                    {unitCategories.map((category) => (
                      <option key={category} value={category}>
                        {category}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="form-grid">
                  <label>
                    Bedrooms
                    <input
                      type="number"
                      min="0"
                      value={flatTypeForm.bedroom_count}
                      onChange={(event) =>
                        setFlatTypeForm({ ...flatTypeForm, bedroom_count: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Bathrooms
                    <input
                      type="number"
                      min="0"
                      value={flatTypeForm.bathroom_count}
                      onChange={(event) =>
                        setFlatTypeForm({ ...flatTypeForm, bathroom_count: event.target.value })
                      }
                    />
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Carpet Area
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={flatTypeForm.carpet_area_sqft}
                      onChange={(event) =>
                        setFlatTypeForm({ ...flatTypeForm, carpet_area_sqft: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Built-up Area
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={flatTypeForm.built_up_area_sqft}
                      onChange={(event) =>
                        setFlatTypeForm({ ...flatTypeForm, built_up_area_sqft: event.target.value })
                      }
                    />
                  </label>
                </div>
                <label>
                  Default Parking
                  <input
                    type="number"
                    min="0"
                    value={flatTypeForm.default_parking_count}
                    onChange={(event) =>
                      setFlatTypeForm({
                        ...flatTypeForm,
                        default_parking_count: Number(event.target.value)
                      })
                    }
                  />
                </label>
                <button type="submit" disabled={isSaving || !selectedTenantId || !selectedSocietyId}>
                  {isSaving ? "Saving" : editingFlatTypeId ? "Save Flat Type" : "Create Flat Type"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Flat Type Registry</h2>
                  <span className="record-count">
                    {isLoadingFlatTypes ? "Loading" : `${flatTypes.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Code</th>
                        <th>Category</th>
                        <th>Area</th>
                        <th>Parking</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {flatTypes.map((flatType) => (
                        <tr key={flatType.id}>
                          <td>{flatType.name}</td>
                          <td>{flatType.code ?? ""}</td>
                          <td>{flatType.unit_category}</td>
                          <td>{[flatType.carpet_area_sqft, flatType.built_up_area_sqft].filter(Boolean).join(" / ")}</td>
                          <td>{flatType.default_parking_count}</td>
                          <td><StatusPill status={flatType.status} /></td>
                          <td>
                            <div className="row-actions">
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => startEditFlatType(flatType)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => void handleFlatTypeStatusChange(flatType)}
                              >
                                {flatType.status === "active" ? "Inactivate" : "Activate"}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                      {!flatTypes.length && !isLoadingFlatTypes ? (
                        <tr>
                          <td colSpan={7} className="empty-cell">
                            No flat types for this society yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : workspace === "chartOfAccounts" ? (
            <section
              className={`workspace ${
                isChartOfAccountFormOpen || isChartOfAccountImportOpen ? "task-only" : "registry-only"
              }`}
            >
              {isChartOfAccountFormOpen ? (
              <form className="panel-form" onSubmit={handleChartOfAccountSubmit}>
                <div className="form-title-row">
                  <h2>{editingChartOfAccountId ? "Edit Account" : "Create Account"}</h2>
                  {editingChartOfAccountId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingChartOfAccountId(null);
                        setChartOfAccountForm(chartOfAccountFormDefaults);
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Society</span>
                  <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                </div>

                <label>
                  Parent Account
                  <select
                    value={chartOfAccountForm.parent_account_id}
                    onChange={(event) =>
                      setChartOfAccountForm({
                        ...chartOfAccountForm,
                        parent_account_id: event.target.value
                      })
                    }
                  >
                    <option value="">No parent</option>
                    {parentAccountOptions.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.account_code} - {account.account_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Account Code
                  <input
                    required
                    maxLength={50}
                    value={chartOfAccountForm.account_code}
                    onChange={(event) =>
                      setChartOfAccountForm({
                        ...chartOfAccountForm,
                        account_code: event.target.value
                      })
                    }
                  />
                </label>
                <label>
                  Account Name
                  <input
                    required
                    maxLength={255}
                    value={chartOfAccountForm.account_name}
                    onChange={(event) =>
                      setChartOfAccountForm({
                        ...chartOfAccountForm,
                        account_name: event.target.value
                      })
                    }
                  />
                </label>
                <div className="form-grid">
                  <label>
                    Account Type
                    <select
                      required
                      value={chartOfAccountForm.account_type}
                      onChange={(event) => {
                        const accountType = event.target.value;
                        setChartOfAccountForm({
                          ...chartOfAccountForm,
                          account_type: accountType,
                          normal_balance:
                            accountType === "asset" || accountType === "expense" ? "debit" : "credit"
                        });
                      }}
                    >
                      {accountTypes.map((accountType) => (
                        <option key={accountType} value={accountType}>
                          {accountType}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Normal Balance
                    <select
                      required
                      value={chartOfAccountForm.normal_balance}
                      onChange={(event) =>
                        setChartOfAccountForm({
                          ...chartOfAccountForm,
                          normal_balance: event.target.value
                        })
                      }
                    >
                      {normalBalances.map((balance) => (
                        <option key={balance} value={balance}>
                          {balance}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <label>
                  Description
                  <textarea
                    value={chartOfAccountForm.description}
                    onChange={(event) =>
                      setChartOfAccountForm({
                        ...chartOfAccountForm,
                        description: event.target.value
                      })
                    }
                  />
                </label>
                <button
                  type="submit"
                  disabled={
                    isSaving ||
                    !selectedTenantId ||
                    !selectedSocietyId ||
                    !chartOfAccountForm.account_code.trim() ||
                    !chartOfAccountForm.account_name.trim()
                  }
                >
                  {isSaving ? "Saving" : editingChartOfAccountId ? "Save Account" : "Create Account"}
                </button>
              </form>
              ) : null}

              {isChartOfAccountImportOpen ? (
                <section className="data-panel">
                  <div className="section-heading">
                    <h2>Bulk Account Import</h2>
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={downloadChartOfAccountImportTemplate}
                    >
                      Download Template
                    </button>
                  </div>
                  <div className="import-controls">
                    <label>
                      CSV File
                      <input
                        type="file"
                        accept=".csv,text/csv"
                        onChange={(event) =>
                          void handleChartOfAccountImportFileChange(event.target.files?.[0] ?? null)
                        }
                      />
                    </label>
                    <div className="import-summary">
                      <span>{chartOfAccountImportFileName || "No file selected"}</span>
                      <span>{chartOfAccountImportRows.length} rows loaded</span>
                    </div>
                    <div className="row-actions">
                      <button
                        type="button"
                        className="secondary"
                        onClick={() => void handleChartOfAccountImportPreview()}
                        disabled={isSaving || !chartOfAccountImportRows.length}
                      >
                        Preview
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleChartOfAccountImportConfirm()}
                        disabled={
                          isSaving ||
                          !chartOfAccountImportPreview ||
                          chartOfAccountImportPreview.invalid_rows > 0
                        }
                      >
                        Confirm Import
                      </button>
                    </div>
                  </div>

                  {chartOfAccountImportPreview ? (
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Row</th>
                            <th>Code</th>
                            <th>Parent</th>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Normal Balance</th>
                            <th>Status</th>
                            <th>Errors</th>
                          </tr>
                        </thead>
                        <tbody>
                          {chartOfAccountImportPreview.rows.map((row) => (
                            <tr key={row.row_number}>
                              <td>{row.row_number}</td>
                              <td>{row.input.account_code ?? ""}</td>
                              <td>{row.input.parent_account_code ?? ""}</td>
                              <td>{row.input.account_name ?? ""}</td>
                              <td>{row.input.account_type ?? ""}</td>
                              <td>{row.input.normal_balance ?? ""}</td>
                              <td><StatusPill status={row.status} /></td>
                              <td>{row.errors.join(" ")}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : null}
                </section>
              ) : null}

              {!isChartOfAccountFormOpen && !isChartOfAccountImportOpen ? (
              <section className="data-panel">
                <div className="section-heading">
                  <h2>Chart of Accounts</h2>
                  <span className="record-count">
                    {isLoadingChartOfAccounts ? "Loading" : `${chartOfAccounts.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Parent</th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Normal Balance</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {chartOfAccounts.map((account) => (
                        <tr key={account.id}>
                          <td>{account.account_code}</td>
                          <td>
                            {chartOfAccounts.find((parent) => parent.id === account.parent_account_id)
                              ?.account_code ?? ""}
                          </td>
                          <td>{account.account_name}</td>
                          <td>{account.account_type}</td>
                          <td>{account.normal_balance}</td>
                          <td><StatusPill status={account.status} /></td>
                          <td>
                            <div className="row-actions">
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => startEditChartOfAccount(account)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => void handleChartOfAccountStatusChange(account)}
                              >
                                {account.status === "active" ? "Inactivate" : "Activate"}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                      {!chartOfAccounts.length && !isLoadingChartOfAccounts ? (
                        <tr>
                          <td colSpan={7} className="empty-cell">
                            No ledger accounts for this society yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
              ) : null}
            </section>
          ) : workspace === "bankCashAccounts" ? (
            <section className={`workspace ${isBankCashAccountFormOpen ? "" : "registry-only"}`}>
              {isBankCashAccountFormOpen ? (
                <form className="panel-form" onSubmit={handleBankCashAccountSubmit}>
                  <div className="form-title-row">
                    <h2>Create Bank/Cash Account</h2>
                  </div>
                  <div className="context-card">
                    <span>Selected Society</span>
                    <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                  </div>
                  <label>
                    Account Code
                    <input
                      required
                      maxLength={50}
                      value={bankCashAccountForm.account_code}
                      onChange={(event) =>
                        setBankCashAccountForm({
                          ...bankCashAccountForm,
                          account_code: event.target.value
                        })
                      }
                    />
                  </label>
                  <label>
                    Account Name
                    <input
                      required
                      maxLength={255}
                      value={bankCashAccountForm.account_name}
                      onChange={(event) =>
                        setBankCashAccountForm({
                          ...bankCashAccountForm,
                          account_name: event.target.value
                        })
                      }
                    />
                  </label>
                  <div className="context-card">
                    <span>Account Classification</span>
                    <strong>Asset / Debit</strong>
                  </div>
                  <label>
                    Description
                    <textarea
                      value={bankCashAccountForm.description}
                      onChange={(event) =>
                        setBankCashAccountForm({
                          ...bankCashAccountForm,
                          description: event.target.value
                        })
                      }
                    />
                  </label>
                  <button
                    type="submit"
                    disabled={
                      isSaving ||
                      !selectedTenantId ||
                      !selectedSocietyId ||
                      !bankCashAccountForm.account_code.trim() ||
                      !bankCashAccountForm.account_name.trim()
                    }
                  >
                    {isSaving ? "Saving" : "Create Account"}
                  </button>
                </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Bank & Cash Accounts</h2>
                  <span className="record-count">
                    {isLoadingChartOfAccounts ? "Loading" : `${bankCashAccounts.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Name</th>
                        <th>Description</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bankCashAccounts.map((account) => (
                        <tr key={account.id}>
                          <td>{account.account_code}</td>
                          <td>{account.account_name}</td>
                          <td>{account.description ?? ""}</td>
                          <td><StatusPill status={account.status} /></td>
                        </tr>
                      ))}
                      {!bankCashAccounts.length && !isLoadingChartOfAccounts ? (
                        <tr>
                          <td colSpan={4} className="empty-cell">
                            No bank or cash asset accounts for this society yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : workspace === "openingBalances" ? (
            <section className={`workspace ${isOpeningBalanceFormOpen ? "task-only" : "registry-only"}`}>
              {isOpeningBalanceFormOpen ? (
                <form className="data-panel full-width-panel" onSubmit={handleOpeningBalanceSubmit}>
                  <div className="section-heading">
                    <h2>Post Opening Balances</h2>
                    <span className="record-count">
                      {isOpeningBalanceBalanced ? "Balanced" : "Unbalanced"}
                    </span>
                  </div>
                  <div className="context-card wide-field">
                    <span>Selected Society</span>
                    <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                  </div>
                  <div className="form-grid wide-field">
                    <label>
                      Opening Date
                      <input
                        required
                        type="date"
                        value={openingBalanceForm.opening_date}
                        onChange={(event) =>
                          setOpeningBalanceForm({
                            ...openingBalanceForm,
                            opening_date: event.target.value
                          })
                        }
                      />
                    </label>
                    <label>
                      Reference Number
                      <input
                        maxLength={100}
                        value={openingBalanceForm.reference_number}
                        onChange={(event) =>
                          setOpeningBalanceForm({
                            ...openingBalanceForm,
                            reference_number: event.target.value
                          })
                        }
                      />
                    </label>
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>Account</th>
                          <th>Description</th>
                          <th>Debit</th>
                          <th>Credit</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {openingBalanceForm.lines.map((line, index) => (
                          <tr key={`opening-balance-line-${index + 1}`}>
                            <td>{index + 1}</td>
                            <td>
                              <select
                                required
                                value={line.account_id}
                                onChange={(event) =>
                                  updateOpeningBalanceLine(index, "account_id", event.target.value)
                                }
                              >
                                <option value="">Select account</option>
                                {activeJournalAccounts.map((account) => (
                                  <option key={account.id} value={account.id}>
                                    {account.account_code} - {account.account_name}
                                  </option>
                                ))}
                              </select>
                            </td>
                            <td>
                              <input
                                value={line.description}
                                onChange={(event) =>
                                  updateOpeningBalanceLine(index, "description", event.target.value)
                                }
                              />
                            </td>
                            <td>
                              <input
                                min="0"
                                step="0.01"
                                type="number"
                                value={line.debit_amount}
                                onChange={(event) =>
                                  updateOpeningBalanceLine(index, "debit_amount", event.target.value)
                                }
                              />
                            </td>
                            <td>
                              <input
                                min="0"
                                step="0.01"
                                type="number"
                                value={line.credit_amount}
                                onChange={(event) =>
                                  updateOpeningBalanceLine(index, "credit_amount", event.target.value)
                                }
                              />
                            </td>
                            <td>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => removeOpeningBalanceLine(index)}
                                disabled={openingBalanceForm.lines.length <= 2}
                              >
                                Remove
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot>
                        <tr>
                          <td colSpan={3}>Totals</td>
                          <td>{openingBalanceDebitTotal.toFixed(2)}</td>
                          <td>{openingBalanceCreditTotal.toFixed(2)}</td>
                          <td><StatusPill status={isOpeningBalanceBalanced ? "balanced" : "unbalanced"} /></td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                  <div className="form-actions">
                    <button type="button" className="secondary" onClick={addOpeningBalanceLine}>
                      Add Line
                    </button>
                  </div>
                  <label className="wide-field">
                    Notes
                    <textarea
                      value={openingBalanceForm.notes}
                      onChange={(event) =>
                        setOpeningBalanceForm({ ...openingBalanceForm, notes: event.target.value })
                      }
                    />
                  </label>
                  <div className="form-actions">
                    <button
                      type="submit"
                      disabled={
                        isSaving ||
                        !selectedTenantId ||
                        !selectedSocietyId ||
                        !openingBalanceForm.opening_date ||
                        !isOpeningBalanceBalanced ||
                        openingBalanceForm.lines.some(
                          (line) =>
                            !line.account_id ||
                            (!Number(line.debit_amount) && !Number(line.credit_amount))
                        )
                      }
                    >
                      {isSaving ? "Posting" : "Post Opening Balances"}
                    </button>
                  </div>
                </form>
              ) : (
                <section className="data-panel">
                  <div className="section-heading">
                    <h2>Opening Balance Journals</h2>
                    <span className="record-count">
                      {journals.filter((entry) => entry.source_type === "opening_balance").length} records
                    </span>
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Reference</th>
                          <th>Description</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {journals
                          .filter((entry) => entry.source_type === "opening_balance")
                          .map((entry) => (
                            <tr key={entry.id}>
                              <td>{entry.journal_date}</td>
                              <td>{entry.reference_number ?? ""}</td>
                              <td>{entry.description}</td>
                              <td><StatusPill status={entry.status} /></td>
                              <td>
                                <div className="row-actions">
                                  <button
                                    type="button"
                                    className="secondary compact"
                                    onClick={() => void handleViewOpeningBalance(entry)}
                                  >
                                    View
                                  </button>
                                  <button
                                    type="button"
                                    className="secondary compact"
                                    disabled={entry.status === "reversed" || isSaving}
                                    onClick={() => void handleReverseJournal(entry)}
                                  >
                                    Reverse
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        {!journals.some((entry) => entry.source_type === "opening_balance") ? (
                          <tr>
                            <td colSpan={5} className="empty-cell">
                              No opening balance journals posted for this society yet.
                            </td>
                          </tr>
                        ) : null}
                      </tbody>
                    </table>
                  </div>
                  {selectedOpeningBalanceDetail ? (
                    <div className="detail-section">
                      <div className="section-heading nested-heading">
                        <div>
                          <h2>{selectedOpeningBalanceDetail.reference_number ?? "Opening Balance Detail"}</h2>
                          <span className="record-count">
                            {selectedOpeningBalanceDetail.journal_date} · {selectedOpeningBalanceDetail.status}
                          </span>
                        </div>
                        <button
                          type="button"
                          className="secondary compact"
                          onClick={() => setSelectedOpeningBalanceDetail(null)}
                        >
                          Close
                        </button>
                      </div>
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>#</th>
                              <th>Account</th>
                              <th>Description</th>
                              <th>Debit</th>
                              <th>Credit</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedOpeningBalanceDetail.lines.map((line) => {
                              const account = chartOfAccounts.find((item) => item.id === line.account_id);
                              return (
                                <tr key={line.id}>
                                  <td>{line.line_number}</td>
                                  <td>
                                    {account
                                      ? `${account.account_code} - ${account.account_name}`
                                      : line.account_id}
                                  </td>
                                  <td>{line.description ?? ""}</td>
                                  <td>{line.debit_amount}</td>
                                  <td>{line.credit_amount}</td>
                                </tr>
                              );
                            })}
                          </tbody>
                          <tfoot>
                            <tr>
                              <td colSpan={3}>Totals</td>
                              <td>
                                {selectedOpeningBalanceDetail.lines
                                  .reduce((total, line) => total + Number(line.debit_amount), 0)
                                  .toFixed(2)}
                              </td>
                              <td>
                                {selectedOpeningBalanceDetail.lines
                                  .reduce((total, line) => total + Number(line.credit_amount), 0)
                                  .toFixed(2)}
                              </td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                      {selectedOpeningBalanceDetail.notes ? (
                        <div className="context-card wide-field">
                          <span>Notes</span>
                          <strong>{selectedOpeningBalanceDetail.notes}</strong>
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </section>
              )}
            </section>
          ) : workspace === "accountLedgers" ? (
            <section className="workspace registry-only">
              <section className="data-panel">
                <form className="filter-bar" onSubmit={handleAccountLedgerSubmit}>
                  <label>
                    Account
                    <select
                      required
                      value={accountLedgerFilters.account_id}
                      onChange={(event) => {
                        setAccountLedger(null);
                        setAccountLedgerFilters({
                          ...accountLedgerFilters,
                          account_id: event.target.value
                        });
                      }}
                    >
                      <option value="">Select account</option>
                      {chartOfAccounts.map((account) => (
                        <option key={account.id} value={account.id}>
                          {account.account_code} - {account.account_name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    From
                    <input
                      type="date"
                      value={accountLedgerFilters.date_from}
                      onChange={(event) =>
                        setAccountLedgerFilters({
                          ...accountLedgerFilters,
                          date_from: event.target.value
                        })
                      }
                    />
                  </label>
                  <label>
                    To
                    <input
                      type="date"
                      value={accountLedgerFilters.date_to}
                      onChange={(event) =>
                        setAccountLedgerFilters({
                          ...accountLedgerFilters,
                          date_to: event.target.value
                        })
                      }
                    />
                  </label>
                  <button type="submit" disabled={isLoadingAccountLedger || !accountLedgerFilters.account_id}>
                    {isLoadingAccountLedger ? "Loading" : "Apply"}
                  </button>
                </form>
              </section>

              <section className="data-panel">
                <div className="section-heading">
                  <h2>
                    {accountLedger
                      ? `${accountLedger.account_code} - ${accountLedger.account_name}`
                      : "Account Ledger"}
                  </h2>
                  <span className="record-count">
                    {isLoadingAccountLedger
                      ? "Loading"
                      : accountLedger
                        ? `${accountLedger.lines.length} records`
                        : "No account selected"}
                  </span>
                </div>

                {accountLedger ? (
                  <>
                    <div className="metrics-grid compact-metrics">
                      <article className="metric-tile">
                        <span>Opening</span>
                        <strong>{accountLedger.opening_balance}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Debits</span>
                        <strong>{accountLedger.total_debits}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Credits</span>
                        <strong>{accountLedger.total_credits}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Closing</span>
                        <strong>{accountLedger.closing_balance}</strong>
                      </article>
                    </div>
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Date</th>
                            <th>Source</th>
                            <th>Reference</th>
                            <th>Description</th>
                            <th>Debit</th>
                            <th>Credit</th>
                            <th>Balance</th>
                          </tr>
                        </thead>
                        <tbody>
                          {accountLedger.lines.map((line) => (
                            <tr key={line.journal_line_id}>
                              <td>{line.journal_date}</td>
                              <td>{line.source_type}</td>
                              <td>{line.reference_number ?? ""}</td>
                              <td>{line.line_description ?? line.description}</td>
                              <td>{line.debit_amount}</td>
                              <td>{line.credit_amount}</td>
                              <td>{line.running_balance}</td>
                            </tr>
                          ))}
                          {!accountLedger.lines.length ? (
                            <tr>
                              <td colSpan={7} className="empty-cell">
                                No posted ledger movement for this account and date range.
                              </td>
                            </tr>
                          ) : null}
                        </tbody>
                      </table>
                    </div>
                  </>
                ) : (
                  <div className="empty-state-panel">
                    <h2>Select an account</h2>
                    <p>Choose a society ledger account and apply filters to view posted movements.</p>
                  </div>
                )}
              </section>
            </section>
          ) : workspace === "flatLedgers" ? (
            <section className="workspace registry-only">
              <section className="data-panel">
                <form className="filter-bar" onSubmit={handleFlatLedgerSubmit}>
                  <label>
                    Building
                    <select
                      required
                      value={flatLedgerFilters.building_id}
                      onChange={(event) => {
                        const buildingId = event.target.value;
                        setFlatLedger(null);
                        setFlatLedgerFilters({
                          ...flatLedgerFilters,
                          building_id: buildingId,
                          flat_id: ""
                        });
                        if (selectedTenantId && selectedSocietyId && buildingId) {
                          void refreshFlats(selectedTenantId, selectedSocietyId, buildingId);
                        }
                      }}
                    >
                      <option value="">Select building</option>
                      {activeBuildings.map((building) => (
                        <option key={building.id} value={building.id}>
                          {building.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Flat
                    <select
                      required
                      disabled={!flatLedgerFilters.building_id}
                      value={flatLedgerFilters.flat_id}
                      onChange={(event) => {
                        setFlatLedger(null);
                        setFlatLedgerFilters({
                          ...flatLedgerFilters,
                          flat_id: event.target.value
                        });
                      }}
                    >
                      <option value="">Select flat</option>
                      {flats
                        .filter((flat) => flat.building_id === flatLedgerFilters.building_id)
                        .map((flat) => (
                          <option key={flat.id} value={flat.id}>
                            {flat.flat_number}
                          </option>
                        ))}
                    </select>
                  </label>
                  <label>
                    From
                    <input
                      type="date"
                      value={flatLedgerFilters.date_from}
                      onChange={(event) =>
                        setFlatLedgerFilters({
                          ...flatLedgerFilters,
                          date_from: event.target.value
                        })
                      }
                    />
                  </label>
                  <label>
                    To
                    <input
                      type="date"
                      value={flatLedgerFilters.date_to}
                      onChange={(event) =>
                        setFlatLedgerFilters({
                          ...flatLedgerFilters,
                          date_to: event.target.value
                        })
                      }
                    />
                  </label>
                  <button type="submit" disabled={isLoadingFlatLedger || !flatLedgerFilters.flat_id}>
                    {isLoadingFlatLedger ? "Loading" : "Apply"}
                  </button>
                </form>
              </section>

              <section className="data-panel">
                <div className="section-heading">
                  <h2>{flatLedger ? `Flat ${flatLedger.flat_number} Ledger` : "Flat Ledger"}</h2>
                  <span className="record-count">
                    {isLoadingFlatLedger
                      ? "Loading"
                      : flatLedger
                        ? `${flatLedger.lines.length} records`
                        : "No flat selected"}
                  </span>
                </div>

                {flatLedger ? (
                  <>
                    <div className="metrics-grid compact-metrics">
                      <article className="metric-tile">
                        <span>Opening</span>
                        <strong>{flatLedger.opening_balance}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Charges</span>
                        <strong>{flatLedger.total_debits}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Payments</span>
                        <strong>{flatLedger.total_credits}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Closing Due</span>
                        <strong>{flatLedger.closing_balance}</strong>
                      </article>
                    </div>
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Date</th>
                            <th>Type</th>
                            <th>Reference</th>
                            <th>Description</th>
                            <th>Debit</th>
                            <th>Credit</th>
                            <th>Balance</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {flatLedger.lines.map((line) => (
                            <tr key={`${line.source_type}-${line.source_id}`}>
                              <td>{line.line_date}</td>
                              <td>{line.source_type}</td>
                              <td>{line.reference_number ?? ""}</td>
                              <td>{line.description}</td>
                              <td>{line.debit_amount}</td>
                              <td>{line.credit_amount}</td>
                              <td>{line.running_balance}</td>
                              <td><StatusPill status={line.status} /></td>
                            </tr>
                          ))}
                          {!flatLedger.lines.length ? (
                            <tr>
                              <td colSpan={8} className="empty-cell">
                                No invoice or payment movement for this flat and date range.
                              </td>
                            </tr>
                          ) : null}
                        </tbody>
                      </table>
                    </div>
                  </>
                ) : (
                  <div className="empty-state-panel">
                    <h2>Select a flat</h2>
                    <p>Choose a building and flat to view invoice, penalty, and payment history.</p>
                  </div>
                )}
              </section>
            </section>
          ) : workspace === "trialBalance" ? (
            <section className="workspace registry-only">
              <section className="data-panel">
                <form className="filter-bar narrow-filter-bar" onSubmit={handleTrialBalanceSubmit}>
                  <label>
                    As Of Date
                    <input
                      required
                      type="date"
                      value={trialBalanceFilters.as_of_date}
                      onChange={(event) => {
                        setTrialBalance(null);
                        setTrialBalanceFilters({ ...trialBalanceFilters, as_of_date: event.target.value });
                      }}
                    />
                  </label>
                  <button type="submit" disabled={isLoadingTrialBalance || !trialBalanceFilters.as_of_date}>
                    {isLoadingTrialBalance ? "Loading" : "Apply"}
                  </button>
                </form>
              </section>

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Trial Balance</h2>
                  <span className="record-count">
                    {isLoadingTrialBalance
                      ? "Loading"
                      : trialBalance
                        ? `${trialBalance.rows.length} accounts`
                        : "No report loaded"}
                  </span>
                </div>

                {trialBalance ? (
                  <>
                    <div className="metrics-grid compact-metrics">
                      <article className="metric-tile">
                        <span>As Of</span>
                        <strong>{trialBalance.as_of_date}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Total Debits</span>
                        <strong>{trialBalance.total_debits}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Total Credits</span>
                        <strong>{trialBalance.total_credits}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Status</span>
                        <strong>{trialBalance.is_balanced ? "Balanced" : "Review"}</strong>
                      </article>
                    </div>
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Code</th>
                            <th>Account</th>
                            <th>Type</th>
                            <th>Normal</th>
                            <th>Status</th>
                            <th>Debit Balance</th>
                            <th>Credit Balance</th>
                          </tr>
                        </thead>
                        <tbody>
                          {trialBalance.rows.map((row) => (
                            <tr key={row.account_id}>
                              <td>{row.account_code}</td>
                              <td>{row.account_name}</td>
                              <td>{row.account_type}</td>
                              <td>{row.normal_balance}</td>
                              <td><StatusPill status={row.status} /></td>
                              <td>{row.debit_balance}</td>
                              <td>{row.credit_balance}</td>
                            </tr>
                          ))}
                          {!trialBalance.rows.length ? (
                            <tr>
                              <td colSpan={7} className="empty-cell">
                                No chart of accounts configured for this society yet.
                              </td>
                            </tr>
                          ) : null}
                        </tbody>
                        <tfoot>
                          <tr>
                            <td colSpan={5}>Totals</td>
                            <td>{trialBalance.total_debits}</td>
                            <td>{trialBalance.total_credits}</td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  </>
                ) : (
                  <div className="empty-state-panel">
                    <h2>Load trial balance</h2>
                    <p>Select an as-of date to summarize all posted account balances for the society.</p>
                  </div>
                )}
              </section>
            </section>
          ) : workspace === "incomeExpense" ? (
            <section className="workspace registry-only">
              <section className="data-panel">
                <form className="filter-bar report-filter-bar" onSubmit={handleIncomeExpenseSubmit}>
                  <label>
                    Period Start
                    <input
                      required
                      type="date"
                      value={incomeExpenseFilters.period_start}
                      onChange={(event) => {
                        setIncomeExpenseReport(null);
                        setIncomeExpenseFilters({
                          ...incomeExpenseFilters,
                          period_start: event.target.value
                        });
                      }}
                    />
                  </label>
                  <label>
                    Period End
                    <input
                      required
                      type="date"
                      value={incomeExpenseFilters.period_end}
                      onChange={(event) => {
                        setIncomeExpenseReport(null);
                        setIncomeExpenseFilters({
                          ...incomeExpenseFilters,
                          period_end: event.target.value
                        });
                      }}
                    />
                  </label>
                  <button
                    type="submit"
                    disabled={
                      isLoadingIncomeExpense ||
                      !incomeExpenseFilters.period_start ||
                      !incomeExpenseFilters.period_end
                    }
                  >
                    {isLoadingIncomeExpense ? "Loading" : "Apply"}
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={isSaving || !incomeExpenseReport}
                    onClick={() => void handleIncomeExpenseExport("xlsx")}
                  >
                    Excel
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={isSaving || !incomeExpenseReport}
                    onClick={() => void handleIncomeExpenseExport("pdf")}
                  >
                    PDF
                  </button>
                </form>
              </section>

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Income vs Expense</h2>
                  <span className="record-count">
                    {isLoadingIncomeExpense
                      ? "Loading"
                      : incomeExpenseReport
                        ? `${incomeExpenseReport.period_start} to ${incomeExpenseReport.period_end}`
                        : "No report loaded"}
                  </span>
                </div>

                {incomeExpenseReport ? (
                  <>
                    <div className="metrics-grid compact-metrics">
                      <article className="metric-tile">
                        <span>Total Income</span>
                        <strong>{incomeExpenseReport.total_income}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Total Expense</span>
                        <strong>{incomeExpenseReport.total_expense}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Net Surplus</span>
                        <strong>{incomeExpenseReport.net_surplus}</strong>
                      </article>
                    </div>
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Section</th>
                            <th>Code</th>
                            <th>Account</th>
                            <th>Amount</th>
                          </tr>
                        </thead>
                        <tbody>
                          {incomeExpenseReport.income_rows.map((row) => (
                            <tr key={row.account_id}>
                              <td>Income</td>
                              <td>{row.account_code}</td>
                              <td>{row.account_name}</td>
                              <td>{row.amount}</td>
                            </tr>
                          ))}
                          {incomeExpenseReport.expense_rows.map((row) => (
                            <tr key={row.account_id}>
                              <td>Expense</td>
                              <td>{row.account_code}</td>
                              <td>{row.account_name}</td>
                              <td>{row.amount}</td>
                            </tr>
                          ))}
                          {!incomeExpenseReport.income_rows.length &&
                          !incomeExpenseReport.expense_rows.length ? (
                            <tr>
                              <td colSpan={4} className="empty-cell">
                                No income or expense accounts configured for this society yet.
                              </td>
                            </tr>
                          ) : null}
                        </tbody>
                        <tfoot>
                          <tr>
                            <td colSpan={3}>Total Income</td>
                            <td>{incomeExpenseReport.total_income}</td>
                          </tr>
                          <tr>
                            <td colSpan={3}>Total Expense</td>
                            <td>{incomeExpenseReport.total_expense}</td>
                          </tr>
                          <tr>
                            <td colSpan={3}>Net Surplus / Deficit</td>
                            <td>{incomeExpenseReport.net_surplus}</td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  </>
                ) : (
                  <div className="empty-state-panel">
                    <h2>Load income vs expense</h2>
                    <p>Select a report period to summarize posted income and expense ledger movement.</p>
                  </div>
                )}
              </section>
            </section>
          ) : workspace === "balanceSheet" ? (
            <section className="workspace registry-only">
              <section className="data-panel">
                <form className="filter-bar report-filter-bar" onSubmit={handleBalanceSheetSubmit}>
                  <label>
                    As Of Date
                    <input
                      required
                      type="date"
                      value={balanceSheetFilters.as_of_date}
                      onChange={(event) => {
                        setBalanceSheetReport(null);
                        setBalanceSheetFilters({
                          ...balanceSheetFilters,
                          as_of_date: event.target.value
                        });
                      }}
                    />
                  </label>
                  <button type="submit" disabled={isLoadingBalanceSheet || !balanceSheetFilters.as_of_date}>
                    {isLoadingBalanceSheet ? "Loading" : "Apply"}
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={isSaving || !balanceSheetReport}
                    onClick={() => void handleBalanceSheetExport("xlsx")}
                  >
                    Excel
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={isSaving || !balanceSheetReport}
                    onClick={() => void handleBalanceSheetExport("pdf")}
                  >
                    PDF
                  </button>
                </form>
              </section>

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Balance Sheet</h2>
                  <span className="record-count">
                    {isLoadingBalanceSheet
                      ? "Loading"
                      : balanceSheetReport
                        ? balanceSheetReport.is_balanced
                          ? "Balanced"
                          : "Review"
                        : "No report loaded"}
                  </span>
                </div>

                {balanceSheetReport ? (
                  <>
                    <div className="metrics-grid compact-metrics">
                      <article className="metric-tile">
                        <span>Total Assets</span>
                        <strong>{balanceSheetReport.total_assets}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Total Liabilities</span>
                        <strong>{balanceSheetReport.total_liabilities}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Total Equity</span>
                        <strong>{balanceSheetReport.total_equity}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Liabilities + Equity</span>
                        <strong>{balanceSheetReport.total_liabilities_and_equity}</strong>
                      </article>
                    </div>
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Section</th>
                            <th>Code</th>
                            <th>Account</th>
                            <th>Amount</th>
                          </tr>
                        </thead>
                        <tbody>
                          {balanceSheetReport.asset_rows.map((row) => (
                            <tr key={row.account_id ?? row.account_code}>
                              <td>Assets</td>
                              <td>{row.account_code}</td>
                              <td>{row.account_name}</td>
                              <td>{row.amount}</td>
                            </tr>
                          ))}
                          {balanceSheetReport.liability_rows.map((row) => (
                            <tr key={row.account_id ?? row.account_code}>
                              <td>Liabilities</td>
                              <td>{row.account_code}</td>
                              <td>{row.account_name}</td>
                              <td>{row.amount}</td>
                            </tr>
                          ))}
                          {balanceSheetReport.equity_rows.map((row) => (
                            <tr key={row.account_id ?? row.account_code}>
                              <td>Equity</td>
                              <td>{row.account_code}</td>
                              <td>{row.account_name}</td>
                              <td>{row.amount}</td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot>
                          <tr>
                            <td colSpan={3}>Total Assets</td>
                            <td>{balanceSheetReport.total_assets}</td>
                          </tr>
                          <tr>
                            <td colSpan={3}>Total Liabilities</td>
                            <td>{balanceSheetReport.total_liabilities}</td>
                          </tr>
                          <tr>
                            <td colSpan={3}>Total Equity</td>
                            <td>{balanceSheetReport.total_equity}</td>
                          </tr>
                          <tr>
                            <td colSpan={3}>Total Liabilities & Equity</td>
                            <td>{balanceSheetReport.total_liabilities_and_equity}</td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  </>
                ) : (
                  <div className="empty-state-panel">
                    <h2>Load balance sheet</h2>
                    <p>Select an as-of date to summarize assets, liabilities, equity, and current surplus.</p>
                  </div>
                )}
              </section>
            </section>
          ) : workspace === "journals" ? (
            <section className={`workspace ${isJournalFormOpen ? "task-only" : "registry-only"}`}>
              {isJournalFormOpen ? (
                <form className="panel-form" onSubmit={handleJournalSubmit}>
                  <div className="form-title-row">
                    <h2>Post Journal Entry</h2>
                  </div>

                  <div className="context-card">
                    <span>Selected Society</span>
                    <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                  </div>

                  <div className="form-grid">
                    <label>
                      Journal Date
                      <input
                        required
                        type="date"
                        value={journalForm.journal_date}
                        onChange={(event) =>
                          setJournalForm({ ...journalForm, journal_date: event.target.value })
                        }
                      />
                    </label>
                    <label>
                      Reference Number
                      <input
                        maxLength={100}
                        value={journalForm.reference_number}
                        onChange={(event) =>
                          setJournalForm({ ...journalForm, reference_number: event.target.value })
                        }
                      />
                    </label>
                  </div>

                  <label>
                    Description
                    <input
                      required
                      maxLength={255}
                      value={journalForm.description}
                      onChange={(event) =>
                        setJournalForm({ ...journalForm, description: event.target.value })
                      }
                    />
                  </label>

                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>Account</th>
                          <th>Description</th>
                          <th>Debit</th>
                          <th>Credit</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {journalForm.lines.map((line, index) => (
                          <tr key={`journal-line-${index + 1}`}>
                            <td>{index + 1}</td>
                            <td>
                              <select
                                required
                                value={line.account_id}
                                onChange={(event) =>
                                  updateJournalLine(index, "account_id", event.target.value)
                                }
                              >
                                <option value="">Select account</option>
                                {activeJournalAccounts.map((account) => (
                                  <option key={account.id} value={account.id}>
                                    {account.account_code} - {account.account_name}
                                  </option>
                                ))}
                              </select>
                            </td>
                            <td>
                              <input
                                value={line.description}
                                onChange={(event) =>
                                  updateJournalLine(index, "description", event.target.value)
                                }
                              />
                            </td>
                            <td>
                              <input
                                min="0"
                                step="0.01"
                                type="number"
                                value={line.debit_amount}
                                onChange={(event) =>
                                  updateJournalLine(index, "debit_amount", event.target.value)
                                }
                              />
                            </td>
                            <td>
                              <input
                                min="0"
                                step="0.01"
                                type="number"
                                value={line.credit_amount}
                                onChange={(event) =>
                                  updateJournalLine(index, "credit_amount", event.target.value)
                                }
                              />
                            </td>
                            <td>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => removeJournalLine(index)}
                                disabled={journalForm.lines.length <= 2}
                              >
                                Remove
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot>
                        <tr>
                          <td colSpan={3}>Totals</td>
                          <td>{journalDebitTotal.toFixed(2)}</td>
                          <td>{journalCreditTotal.toFixed(2)}</td>
                          <td>
                            <StatusPill status={isJournalBalanced ? "balanced" : "unbalanced"} />
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>

                  <div className="row-actions">
                    <button type="button" className="secondary" onClick={addJournalLine}>
                      Add Line
                    </button>
                  </div>

                  <label>
                    Notes
                    <textarea
                      value={journalForm.notes}
                      onChange={(event) =>
                        setJournalForm({ ...journalForm, notes: event.target.value })
                      }
                    />
                  </label>

                  <button
                    type="submit"
                    disabled={
                      isSaving ||
                      !selectedTenantId ||
                      !selectedSocietyId ||
                      !journalForm.journal_date ||
                      !journalForm.description.trim() ||
                      !isJournalBalanced ||
                      journalForm.lines.some(
                        (line) =>
                          !line.account_id ||
                          (!Number(line.debit_amount) && !Number(line.credit_amount))
                      )
                    }
                  >
                    {isSaving ? "Posting" : "Post Journal"}
                  </button>
                </form>
              ) : null}

              {!isJournalFormOpen ? (
                <section className="data-panel">
                  <div className="section-heading">
                    <h2>Journal Registry</h2>
                    <span className="record-count">
                      {isLoadingJournals ? "Loading" : `${journals.length} records`}
                    </span>
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Reference</th>
                          <th>Source</th>
                          <th>Description</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {journals.map((entry) => (
                          <tr key={entry.id}>
                            <td>{entry.journal_date}</td>
                            <td>{entry.reference_number ?? ""}</td>
                            <td>{entry.source_type}</td>
                            <td>{entry.description}</td>
                            <td><StatusPill status={entry.status} /></td>
                          </tr>
                        ))}
                        {!journals.length && !isLoadingJournals ? (
                          <tr>
                            <td colSpan={5} className="empty-cell">
                              No journal entries for this society yet.
                            </td>
                          </tr>
                        ) : null}
                      </tbody>
                    </table>
                  </div>
                </section>
              ) : null}
            </section>
          ) : workspace === "accountTransfers" ? (
            <section className={`workspace ${isAccountTransferFormOpen ? "task-only" : "registry-only"}`}>
              {isAccountTransferFormOpen ? (
                <form className="panel-form" onSubmit={handleAccountTransferSubmit}>
                  <div className="form-title-row">
                    <h2>Post Account Transfer</h2>
                  </div>

                  <div className="context-card">
                    <span>Selected Society</span>
                    <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                  </div>

                  <div className="form-grid">
                    <label>
                      From Account
                      <select
                        required
                        value={accountTransferForm.from_account_id}
                        onChange={(event) =>
                          setAccountTransferForm({
                            ...accountTransferForm,
                            from_account_id: event.target.value,
                            to_account_id:
                              event.target.value === accountTransferForm.to_account_id
                                ? ""
                                : accountTransferForm.to_account_id
                          })
                        }
                      >
                        <option value="">Select source account</option>
                        {activeAssetAccounts.map((account) => (
                          <option key={account.id} value={account.id}>
                            {account.account_code} - {account.account_name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      To Account
                      <select
                        required
                        value={accountTransferForm.to_account_id}
                        onChange={(event) =>
                          setAccountTransferForm({
                            ...accountTransferForm,
                            to_account_id: event.target.value
                          })
                        }
                      >
                        <option value="">Select destination account</option>
                        {activeAssetAccounts
                          .filter((account) => account.id !== accountTransferForm.from_account_id)
                          .map((account) => (
                            <option key={account.id} value={account.id}>
                              {account.account_code} - {account.account_name}
                            </option>
                          ))}
                      </select>
                    </label>
                  </div>

                  <div className="form-grid">
                    <label>
                      Transfer Date
                      <input
                        required
                        type="date"
                        value={accountTransferForm.transfer_date}
                        onChange={(event) =>
                          setAccountTransferForm({
                            ...accountTransferForm,
                            transfer_date: event.target.value
                          })
                        }
                      />
                    </label>
                    <label>
                      Amount
                      <input
                        required
                        min="0.01"
                        step="0.01"
                        type="number"
                        value={accountTransferForm.amount}
                        onChange={(event) =>
                          setAccountTransferForm({ ...accountTransferForm, amount: event.target.value })
                        }
                      />
                    </label>
                  </div>

                  <div className="form-grid">
                    <label>
                      Transfer Mode
                      <select
                        required
                        value={accountTransferForm.transfer_mode}
                        onChange={(event) =>
                          setAccountTransferForm({
                            ...accountTransferForm,
                            transfer_mode: event.target.value
                          })
                        }
                      >
                        {paymentModes.map((mode) => (
                          <option key={mode} value={mode}>
                            {mode}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Reference Number
                      <input
                        maxLength={100}
                        value={accountTransferForm.reference_number}
                        onChange={(event) =>
                          setAccountTransferForm({
                            ...accountTransferForm,
                            reference_number: event.target.value
                          })
                        }
                      />
                    </label>
                  </div>

                  <label>
                    Description
                    <input
                      required
                      maxLength={255}
                      value={accountTransferForm.description}
                      onChange={(event) =>
                        setAccountTransferForm({
                          ...accountTransferForm,
                          description: event.target.value
                        })
                      }
                    />
                  </label>

                  <div className="context-card">
                    <span>Posting</span>
                    <strong>
                      Debit {selectedTransferToAccount?.account_name ?? "destination account"} / Credit{" "}
                      {selectedTransferFromAccount?.account_name ?? "source account"}
                    </strong>
                  </div>

                  <label>
                    Notes
                    <textarea
                      value={accountTransferForm.notes}
                      onChange={(event) =>
                        setAccountTransferForm({ ...accountTransferForm, notes: event.target.value })
                      }
                    />
                  </label>

                  <button
                    type="submit"
                    disabled={
                      isSaving ||
                      !selectedTenantId ||
                      !selectedSocietyId ||
                      !accountTransferForm.from_account_id ||
                      !accountTransferForm.to_account_id ||
                      accountTransferForm.from_account_id === accountTransferForm.to_account_id ||
                      !accountTransferForm.transfer_date ||
                      !accountTransferForm.description.trim() ||
                      !Number(accountTransferForm.amount)
                    }
                  >
                    {isSaving ? "Posting" : "Post Transfer"}
                  </button>
                </form>
              ) : null}

              {!isAccountTransferFormOpen ? (
                <section className="data-panel">
                  <div className="section-heading">
                    <h2>Transfer Registry</h2>
                    <span className="record-count">
                      {isLoadingAccountTransfers ? "Loading" : `${accountTransfers.length} records`}
                    </span>
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>From</th>
                          <th>To</th>
                          <th>Amount</th>
                          <th>Mode</th>
                          <th>Reference</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {accountTransfers.map((transfer) => {
                          const fromAccount = chartOfAccounts.find(
                            (account) => account.id === transfer.from_account_id
                          );
                          const toAccount = chartOfAccounts.find(
                            (account) => account.id === transfer.to_account_id
                          );
                          return (
                            <tr key={transfer.id}>
                              <td>{transfer.transfer_date}</td>
                              <td>
                                {fromAccount
                                  ? `${fromAccount.account_code} - ${fromAccount.account_name}`
                                  : ""}
                              </td>
                              <td>
                                {toAccount ? `${toAccount.account_code} - ${toAccount.account_name}` : ""}
                              </td>
                              <td>{transfer.amount}</td>
                              <td>{transfer.transfer_mode}</td>
                              <td>{transfer.reference_number ?? ""}</td>
                              <td><StatusPill status={transfer.status} /></td>
                            </tr>
                          );
                        })}
                        {!accountTransfers.length && !isLoadingAccountTransfers ? (
                          <tr>
                            <td colSpan={7} className="empty-cell">
                              No account transfers for this society yet.
                            </td>
                          </tr>
                        ) : null}
                      </tbody>
                    </table>
                  </div>
                </section>
              ) : null}
            </section>
          ) : workspace === "otherIncome" ? (
            <section className={`workspace ${isOtherIncomeFormOpen ? "task-only" : "registry-only"}`}>
              {isOtherIncomeFormOpen ? (
                <form className="panel-form" onSubmit={handleOtherIncomeSubmit}>
                  <div className="form-title-row">
                    <h2>Record Other Income</h2>
                  </div>

                  <div className="context-card">
                    <span>Selected Society</span>
                    <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                  </div>

                  <div className="form-grid">
                    <label>
                      Receipt Date
                      <input
                        required
                        type="date"
                        value={otherIncomeForm.receipt_date}
                        onChange={(event) =>
                          setOtherIncomeForm({ ...otherIncomeForm, receipt_date: event.target.value })
                        }
                      />
                    </label>
                    <label>
                      Payer Type
                      <select
                        required
                        value={otherIncomeForm.payer_type}
                        onChange={(event) =>
                          setOtherIncomeForm({ ...otherIncomeForm, payer_type: event.target.value })
                        }
                      >
                        {otherIncomePayerTypes.map((payerType) => (
                          <option key={payerType} value={payerType}>
                            {payerType.replace("_", " ")}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>

                  <label>
                    Payer Name
                    <input
                      required
                      maxLength={255}
                      value={otherIncomeForm.payer_name}
                      onChange={(event) =>
                        setOtherIncomeForm({ ...otherIncomeForm, payer_name: event.target.value })
                      }
                    />
                  </label>

                  <div className="form-grid">
                    <label>
                      Income Account
                      <select
                        required
                        value={otherIncomeForm.income_account_id}
                        onChange={(event) =>
                          setOtherIncomeForm({ ...otherIncomeForm, income_account_id: event.target.value })
                        }
                      >
                        <option value="">Select income account</option>
                        {activeIncomeAccounts.map((account) => (
                          <option key={account.id} value={account.id}>
                            {account.account_code} - {account.account_name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Deposit Account
                      <select
                        required
                        value={otherIncomeForm.deposit_account_id}
                        onChange={(event) =>
                          setOtherIncomeForm({ ...otherIncomeForm, deposit_account_id: event.target.value })
                        }
                      >
                        <option value="">Select bank/cash account</option>
                        {activeAssetAccounts.map((account) => (
                          <option key={account.id} value={account.id}>
                            {account.account_code} - {account.account_name}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>

                  <div className="form-grid">
                    <label>
                      Amount
                      <input
                        required
                        min="0.01"
                        step="0.01"
                        type="number"
                        value={otherIncomeForm.amount}
                        onChange={(event) =>
                          setOtherIncomeForm({ ...otherIncomeForm, amount: event.target.value })
                        }
                      />
                    </label>
                    <label>
                      Receipt Mode
                      <select
                        required
                        value={otherIncomeForm.receipt_mode}
                        onChange={(event) =>
                          setOtherIncomeForm({ ...otherIncomeForm, receipt_mode: event.target.value })
                        }
                      >
                        {paymentModes.map((mode) => (
                          <option key={mode} value={mode}>
                            {mode}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>

                  <label>
                    Reference Number
                    <input
                      maxLength={100}
                      value={otherIncomeForm.reference_number}
                      onChange={(event) =>
                        setOtherIncomeForm({ ...otherIncomeForm, reference_number: event.target.value })
                      }
                    />
                  </label>

                  <label>
                    Description
                    <input
                      required
                      maxLength={255}
                      value={otherIncomeForm.description}
                      onChange={(event) =>
                        setOtherIncomeForm({ ...otherIncomeForm, description: event.target.value })
                      }
                    />
                  </label>

                  <div className="context-card">
                    <span>Posting</span>
                    <strong>
                      Debit {selectedOtherIncomeDepositAccount?.account_name ?? "deposit account"} / Credit{" "}
                      {selectedOtherIncomeAccount?.account_name ?? "income account"}
                    </strong>
                  </div>

                  <label>
                    Notes
                    <textarea
                      value={otherIncomeForm.notes}
                      onChange={(event) =>
                        setOtherIncomeForm({ ...otherIncomeForm, notes: event.target.value })
                      }
                    />
                  </label>

                  <button
                    type="submit"
                    disabled={
                      isSaving ||
                      !selectedTenantId ||
                      !selectedSocietyId ||
                      !otherIncomeForm.receipt_date ||
                      !otherIncomeForm.payer_name.trim() ||
                      !otherIncomeForm.income_account_id ||
                      !otherIncomeForm.deposit_account_id ||
                      !otherIncomeForm.description.trim() ||
                      !Number(otherIncomeForm.amount)
                    }
                  >
                    {isSaving ? "Recording" : "Record Receipt"}
                  </button>
                </form>
              ) : null}

              {!isOtherIncomeFormOpen ? (
                <section className="data-panel">
                  <div className="section-heading">
                    <h2>Other Income Registry</h2>
                    <span className="record-count">
                      {isLoadingOtherIncomeReceipts ? "Loading" : `${otherIncomeReceipts.length} records`}
                    </span>
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Payer</th>
                          <th>Income Account</th>
                          <th>Deposit Account</th>
                          <th>Amount</th>
                          <th>Mode</th>
                          <th>Reference</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {otherIncomeReceipts.map((receipt) => {
                          const incomeAccount = chartOfAccounts.find(
                            (account) => account.id === receipt.income_account_id
                          );
                          const depositAccount = chartOfAccounts.find(
                            (account) => account.id === receipt.deposit_account_id
                          );
                          return (
                            <tr key={receipt.id}>
                              <td>{receipt.receipt_date}</td>
                              <td>
                                <strong>{receipt.payer_name}</strong>
                                <span className="table-subtext">{receipt.payer_type.replace("_", " ")}</span>
                              </td>
                              <td>
                                {incomeAccount
                                  ? `${incomeAccount.account_code} - ${incomeAccount.account_name}`
                                  : ""}
                              </td>
                              <td>
                                {depositAccount
                                  ? `${depositAccount.account_code} - ${depositAccount.account_name}`
                                  : ""}
                              </td>
                              <td>{receipt.amount}</td>
                              <td>{receipt.receipt_mode}</td>
                              <td>{receipt.reference_number ?? ""}</td>
                              <td><StatusPill status={receipt.status} /></td>
                              <td>
                                <button
                                  type="button"
                                  className="secondary compact"
                                  disabled={receipt.status === "reversed"}
                                  onClick={() => handleOtherIncomeReverse(receipt)}
                                >
                                  Reverse
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                        {!otherIncomeReceipts.length && !isLoadingOtherIncomeReceipts ? (
                          <tr>
                            <td colSpan={9} className="empty-cell">
                              No other income receipts for this society yet.
                            </td>
                          </tr>
                        ) : null}
                      </tbody>
                    </table>
                  </div>
                </section>
              ) : null}
            </section>
          ) : workspace === "chargeTypes" ? (
            <section className={`workspace ${isChargeTypeFormOpen ? "" : "registry-only"}`}>
              {isChargeTypeFormOpen ? (
              <form className="panel-form" onSubmit={handleChargeTypeSubmit}>
                <div className="form-title-row">
                  <h2>{editingChargeTypeId ? "Edit Charge Type" : "Create Charge Type"}</h2>
                  {editingChargeTypeId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingChargeTypeId(null);
                        setChargeTypeForm(chargeTypeFormDefaults);
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Society</span>
                  <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                </div>

                <label>
                  Name
                  <input
                    required
                    maxLength={255}
                    value={chargeTypeForm.name}
                    onChange={(event) =>
                      setChargeTypeForm({ ...chargeTypeForm, name: event.target.value })
                    }
                  />
                </label>
                <label>
                  Code
                  <input
                    maxLength={50}
                    value={chargeTypeForm.code}
                    onChange={(event) =>
                      setChargeTypeForm({ ...chargeTypeForm, code: event.target.value })
                    }
                  />
                </label>
                <label>
                  Revenue Account
                  <select
                    required
                    value={chargeTypeForm.revenue_account_id}
                    onChange={(event) =>
                      setChargeTypeForm({
                        ...chargeTypeForm,
                        revenue_account_id: event.target.value
                      })
                    }
                  >
                    <option value="">Select income account</option>
                    {incomeAccounts.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.account_code} - {account.account_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Description
                  <textarea
                    value={chargeTypeForm.description}
                    onChange={(event) =>
                      setChargeTypeForm({ ...chargeTypeForm, description: event.target.value })
                    }
                  />
                </label>
                <button
                  type="submit"
                  disabled={
                    isSaving ||
                    !selectedTenantId ||
                    !selectedSocietyId ||
                    !chargeTypeForm.name.trim() ||
                    !chargeTypeForm.revenue_account_id
                  }
                >
                  {isSaving ? "Saving" : editingChargeTypeId ? "Save Charge Type" : "Create Charge Type"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Charge Type Registry</h2>
                  <span className="record-count">
                    {isLoadingChargeTypes ? "Loading" : `${chargeTypes.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Code</th>
                        <th>Revenue Account</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {chargeTypes.map((chargeType) => {
                        const revenueAccount = chartOfAccounts.find(
                          (account) => account.id === chargeType.revenue_account_id
                        );
                        return (
                        <tr key={chargeType.id}>
                          <td>{chargeType.name}</td>
                          <td>{chargeType.code ?? ""}</td>
                          <td>
                            {revenueAccount
                              ? `${revenueAccount.account_code} - ${revenueAccount.account_name}`
                              : "Unassigned"}
                          </td>
                          <td><StatusPill status={chargeType.status} /></td>
                          <td>
                            <div className="row-actions">
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => startEditChargeType(chargeType)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => void handleChargeTypeStatusChange(chargeType)}
                              >
                                {chargeType.status === "active" ? "Inactivate" : "Activate"}
                              </button>
                            </div>
                          </td>
                        </tr>
                        );
                      })}
                      {!chargeTypes.length && !isLoadingChargeTypes ? (
                        <tr>
                          <td colSpan={5} className="empty-cell">
                            No charge types for this society yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : workspace === "expenseCategories" ? (
            <section className={`workspace ${isExpenseCategoryFormOpen ? "" : "registry-only"}`}>
              {isExpenseCategoryFormOpen ? (
              <form className="panel-form" onSubmit={handleExpenseCategorySubmit}>
                <div className="form-title-row">
                  <h2>{editingExpenseCategoryId ? "Edit Expense Category" : "Create Expense Category"}</h2>
                  {editingExpenseCategoryId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingExpenseCategoryId(null);
                        setExpenseCategoryForm(expenseCategoryFormDefaults);
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Society</span>
                  <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                </div>

                <label>
                  Name
                  <input
                    required
                    maxLength={255}
                    value={expenseCategoryForm.name}
                    onChange={(event) =>
                      setExpenseCategoryForm({ ...expenseCategoryForm, name: event.target.value })
                    }
                  />
                </label>
                <label>
                  Code
                  <input
                    maxLength={50}
                    value={expenseCategoryForm.code}
                    onChange={(event) =>
                      setExpenseCategoryForm({ ...expenseCategoryForm, code: event.target.value })
                    }
                  />
                </label>
                <label>
                  Expense Account
                  <select
                    required
                    value={expenseCategoryForm.expense_account_id}
                    onChange={(event) =>
                      setExpenseCategoryForm({
                        ...expenseCategoryForm,
                        expense_account_id: event.target.value
                      })
                    }
                  >
                    <option value="">Select expense account</option>
                    {activeExpenseAccounts.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.account_code} - {account.account_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Description
                  <textarea
                    value={expenseCategoryForm.description}
                    onChange={(event) =>
                      setExpenseCategoryForm({
                        ...expenseCategoryForm,
                        description: event.target.value
                      })
                    }
                  />
                </label>
                <button
                  type="submit"
                  disabled={
                    isSaving ||
                    !selectedTenantId ||
                    !selectedSocietyId ||
                    !expenseCategoryForm.name.trim() ||
                    !expenseCategoryForm.expense_account_id
                  }
                >
                  {isSaving
                    ? "Saving"
                    : editingExpenseCategoryId
                      ? "Save Expense Category"
                      : "Create Expense Category"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Expense Category Registry</h2>
                  <span className="record-count">
                    {isLoadingExpenseCategories ? "Loading" : `${expenseCategories.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Code</th>
                        <th>Expense Account</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {expenseCategories.map((category) => {
                        const expenseAccount = chartOfAccounts.find(
                          (account) => account.id === category.expense_account_id
                        );
                        return (
                        <tr key={category.id}>
                          <td>{category.name}</td>
                          <td>{category.code ?? ""}</td>
                          <td>
                            {expenseAccount
                              ? `${expenseAccount.account_code} - ${expenseAccount.account_name}`
                              : "Unassigned"}
                          </td>
                          <td><StatusPill status={category.status} /></td>
                          <td>
                            <div className="row-actions">
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => startEditExpenseCategory(category)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => void handleExpenseCategoryStatusChange(category)}
                              >
                                {category.status === "active" ? "Inactivate" : "Activate"}
                              </button>
                            </div>
                          </td>
                        </tr>
                        );
                      })}
                      {!expenseCategories.length && !isLoadingExpenseCategories ? (
                        <tr>
                          <td colSpan={5} className="empty-cell">
                            No expense categories for this society yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : workspace === "numberingSettings" ? (
            <section className="workspace task-only">
              <form className="data-panel full-width-panel" onSubmit={handleInvoiceSequenceSubmit}>
                <div className="section-heading">
                  <h2>Invoice Numbering</h2>
                  <span className="record-count">
                    {isLoadingInvoiceSequence
                      ? "Loading"
                      : invoiceSequence
                        ? `Next ${invoiceSequence.next_sequence}`
                        : "Default settings"}
                  </span>
                </div>
                <div className="context-card">
                  <span>Selected Society</span>
                  <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                </div>
                <div className="form-grid two-column">
                  <label>
                    Prefix
                    <input
                      value={invoiceSequenceForm.prefix}
                      onChange={(event) =>
                        setInvoiceSequenceForm((current) => ({
                          ...current,
                          prefix: event.target.value.toUpperCase()
                        }))
                      }
                      placeholder="INV"
                      required
                    />
                  </label>
                  <label>
                    Separator
                    <select
                      value={invoiceSequenceForm.separator}
                      onChange={(event) =>
                        setInvoiceSequenceForm((current) => ({
                          ...current,
                          separator: event.target.value
                        }))
                      }
                    >
                      <option value="-">-</option>
                      <option value="/">/</option>
                      <option value="_">_</option>
                      <option value=".">.</option>
                      <option value="">None</option>
                    </select>
                  </label>
                  <label>
                    Next Sequence
                    <input
                      type="number"
                      min="1"
                      value={invoiceSequenceForm.next_sequence}
                      onChange={(event) =>
                        setInvoiceSequenceForm((current) => ({
                          ...current,
                          next_sequence: Number(event.target.value)
                        }))
                      }
                      required
                    />
                  </label>
                  <label>
                    Padding
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={invoiceSequenceForm.padding}
                      onChange={(event) =>
                        setInvoiceSequenceForm((current) => ({
                          ...current,
                          padding: Number(event.target.value)
                        }))
                      }
                      required
                    />
                  </label>
                  <label>
                    Reset Policy
                    <select
                      value={invoiceSequenceForm.reset_policy}
                      onChange={(event) =>
                        setInvoiceSequenceForm((current) => ({
                          ...current,
                          reset_policy: event.target.value
                        }))
                      }
                    >
                      {documentResetPolicies.map((policy) => (
                        <option key={policy} value={policy}>
                          {policy}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="rule-picker">
                  <div className="rule-grid">
                    <label className="rule-option">
                      <input
                        type="checkbox"
                        checked={invoiceSequenceForm.include_period}
                        onChange={(event) =>
                          setInvoiceSequenceForm((current) => ({
                            ...current,
                            include_period: event.target.checked
                          }))
                        }
                      />
                      <span>
                        <strong>Include Billing Period</strong>
                        <small>Example token: 202604</small>
                      </span>
                    </label>
                    <label className="rule-option">
                      <input
                        type="checkbox"
                        checked={invoiceSequenceForm.include_financial_year}
                        onChange={(event) =>
                          setInvoiceSequenceForm((current) => ({
                            ...current,
                            include_financial_year: event.target.checked
                          }))
                        }
                      />
                      <span>
                        <strong>Include Financial Year</strong>
                        <small>Example token: FY2627</small>
                      </span>
                    </label>
                  </div>
                </div>
                <div className="detail-grid">
                  <div>
                    <span>Preview</span>
                    <strong>
                      {[
                        invoiceSequenceForm.prefix || "INV",
                        invoiceSequenceForm.include_financial_year ? "FY2627" : "",
                        invoiceSequenceForm.include_period ? "202604" : "",
                        String(invoiceSequenceForm.next_sequence || 1).padStart(
                          Number(invoiceSequenceForm.padding || 5),
                          "0"
                        )
                      ].filter(Boolean).join(invoiceSequenceForm.separator)}
                    </strong>
                  </div>
                  <div>
                    <span>Current Reset Key</span>
                    <strong>{invoiceSequence?.current_reset_key ?? "GLOBAL"}</strong>
                  </div>
                </div>
                <div className="form-actions">
                  <button type="submit" disabled={isSaving || !selectedSocietyId}>
                    Save Numbering
                  </button>
                </div>
              </form>
            </section>
          ) : workspace === "billingRules" ? (
            <section className={`workspace ${isBillingRuleFormOpen ? "task-only" : "registry-only"}`}>
              {isBillingRuleFormOpen ? (
              <form className="panel-form" onSubmit={handleBillingRuleSubmit}>
                <div className="form-title-row">
                  <h2>{editingBillingRuleId ? "Edit Billing Rule" : "Create Billing Rule"}</h2>
                  {editingBillingRuleId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingBillingRuleId(null);
                        setBillingRuleForm({ ...billingRuleFormDefaults, effective_from: todayIsoDate() });
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Society</span>
                  <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                </div>

                <label>
                  Rule Name
                  <input
                    required
                    maxLength={255}
                    value={billingRuleForm.name}
                    onChange={(event) =>
                      setBillingRuleForm({ ...billingRuleForm, name: event.target.value })
                    }
                  />
                </label>
                <label>
                  Charge Type
                  <select
                    required
                    value={billingRuleForm.charge_type_id}
                    onChange={(event) =>
                      setBillingRuleForm({ ...billingRuleForm, charge_type_id: event.target.value })
                    }
                  >
                    <option value="">Select charge type</option>
                    {activeChargeTypes.map((chargeType) => (
                      <option key={chargeType.id} value={chargeType.id}>
                        {chargeType.name}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="form-grid">
                  <label>
                    Calculation
                    <select
                      required
                      value={billingRuleForm.calculation_method}
                      onChange={(event) => {
                        const calculationMethod = event.target.value;
                        setBillingRuleForm({
                          ...billingRuleForm,
                          calculation_method: calculationMethod,
                          area_basis: calculationMethod === "area_based" ? "carpet_area" : "",
                          scope_type:
                            calculationMethod === "flat_type_fixed"
                              ? "flat_type"
                              : billingRuleForm.scope_type === "flat_type" && calculationMethod !== "flat_type_fixed"
                                ? "all_flats"
                                : billingRuleForm.scope_type,
                          building_id: calculationMethod === "flat_type_fixed" ? "" : billingRuleForm.building_id,
                          wing_id: calculationMethod === "flat_type_fixed" ? "" : billingRuleForm.wing_id,
                          flat_type_id: calculationMethod === "flat_type_fixed" ? billingRuleForm.flat_type_id : ""
                        });
                      }}
                    >
                      {billingCalculationMethods.map((method) => (
                        <option key={method} value={method}>
                          {method}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Frequency
                    <select
                      required
                      value={billingRuleForm.frequency}
                      onChange={(event) =>
                        setBillingRuleForm({ ...billingRuleForm, frequency: event.target.value })
                      }
                    >
                      {billingFrequencies.map((frequency) => (
                        <option key={frequency} value={frequency}>
                          {frequency}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Amount / Rate
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      required={billingRuleForm.calculation_method !== "manual"}
                      value={billingRuleForm.amount}
                      onChange={(event) =>
                        setBillingRuleForm({ ...billingRuleForm, amount: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Area Basis
                    <select
                      value={billingRuleForm.area_basis}
                      disabled={billingRuleForm.calculation_method !== "area_based"}
                      required={billingRuleForm.calculation_method === "area_based"}
                      onChange={(event) =>
                        setBillingRuleForm({ ...billingRuleForm, area_basis: event.target.value })
                      }
                    >
                      <option value="">Not applicable</option>
                      {billingAreaBases.map((areaBasis) => (
                        <option key={areaBasis} value={areaBasis}>
                          {areaBasis}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Generation Day
                    <input
                      type="number"
                      min="1"
                      max="31"
                      required
                      value={billingRuleForm.generation_day}
                      onChange={(event) =>
                        setBillingRuleForm({
                          ...billingRuleForm,
                          generation_day: Number(event.target.value)
                        })
                      }
                    />
                  </label>
                  <label>
                    Due Day
                    <input
                      type="number"
                      min="1"
                      max="31"
                      required
                      value={billingRuleForm.due_day}
                      onChange={(event) =>
                        setBillingRuleForm({
                          ...billingRuleForm,
                          due_day: Number(event.target.value)
                        })
                      }
                    />
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Billing Period
                    <select
                      required
                      value={billingRuleForm.billing_period_timing}
                      onChange={(event) =>
                        setBillingRuleForm({
                          ...billingRuleForm,
                          billing_period_timing: event.target.value
                        })
                      }
                    >
                      {billingPeriodTimings.map((periodTiming) => (
                        <option key={periodTiming} value={periodTiming}>
                          {periodTiming}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Next Generation Date
                    <input
                      type="date"
                      value={billingRuleForm.next_generation_date}
                      onChange={(event) =>
                        setBillingRuleForm({
                          ...billingRuleForm,
                          next_generation_date: event.target.value
                        })
                      }
                    />
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Scope
                    <select
                      required
                      value={billingRuleForm.scope_type}
                      disabled={billingRuleForm.calculation_method === "flat_type_fixed"}
                      onChange={(event) => {
                        const scopeType = event.target.value;
                        setBillingRuleForm({
                          ...billingRuleForm,
                          scope_type: scopeType,
                          building_id: "",
                          wing_id: "",
                          flat_type_id: ""
                        });
                      }}
                    >
                      {billingScopeTypes.map((scopeType) => (
                        <option key={scopeType} value={scopeType}>
                          {scopeType}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Building
                    <select
                      value={billingRuleForm.building_id}
                      disabled={!["building", "wing"].includes(billingRuleForm.scope_type)}
                      required={["building", "wing"].includes(billingRuleForm.scope_type)}
                      onChange={(event) =>
                        setBillingRuleForm({
                          ...billingRuleForm,
                          building_id: event.target.value,
                          wing_id: ""
                        })
                      }
                    >
                      <option value="">Select building</option>
                      {activeBuildings.map((building) => (
                        <option key={building.id} value={building.id}>
                          {building.name}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Wing
                    <select
                      value={billingRuleForm.wing_id}
                      disabled={billingRuleForm.scope_type !== "wing" || !billingRuleForm.building_id}
                      required={billingRuleForm.scope_type === "wing"}
                      onChange={(event) =>
                        setBillingRuleForm({ ...billingRuleForm, wing_id: event.target.value })
                      }
                    >
                      <option value="">Select wing</option>
                      {activeWings
                        .filter((wing) => wing.building_id === billingRuleForm.building_id)
                        .map((wing) => (
                          <option key={wing.id} value={wing.id}>
                            {wing.name}
                          </option>
                        ))}
                    </select>
                  </label>
                  <label>
                    Flat Type
                    <select
                      value={billingRuleForm.flat_type_id}
                      disabled={billingRuleForm.scope_type !== "flat_type"}
                      required={billingRuleForm.scope_type === "flat_type"}
                      onChange={(event) =>
                        setBillingRuleForm({ ...billingRuleForm, flat_type_id: event.target.value })
                      }
                    >
                      <option value="">Select flat type</option>
                      {activeFlatTypes.map((flatType) => (
                        <option key={flatType.id} value={flatType.id}>
                          {flatType.name}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Effective From
                    <input
                      type="date"
                      required
                      value={billingRuleForm.effective_from}
                      onChange={(event) =>
                        setBillingRuleForm({ ...billingRuleForm, effective_from: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Effective To
                    <input
                      type="date"
                      value={billingRuleForm.effective_to}
                      onChange={(event) =>
                        setBillingRuleForm({ ...billingRuleForm, effective_to: event.target.value })
                      }
                    />
                  </label>
                </div>
                <label>
                  Description
                  <textarea
                    value={billingRuleForm.description}
                    onChange={(event) =>
                      setBillingRuleForm({ ...billingRuleForm, description: event.target.value })
                    }
                  />
                </label>
                <label>
                  Applicable Penalty Rules
                  <select
                    multiple
                    value={billingRuleForm.late_fee_rule_ids}
                    onChange={(event) =>
                      setBillingRuleForm({
                        ...billingRuleForm,
                        late_fee_rule_ids: Array.from(event.target.selectedOptions, (option) => option.value)
                      })
                    }
                  >
                    {activeLateFeeRules.map((rule) => (
                      <option key={rule.id} value={rule.id}>
                        {rule.name}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  type="submit"
                  disabled={
                    isSaving ||
                    !selectedTenantId ||
                    !selectedSocietyId ||
                    !billingRuleForm.name.trim() ||
                    !billingRuleForm.charge_type_id ||
                    !billingRuleForm.effective_from ||
                    billingRuleForm.generation_day < 1 ||
                    billingRuleForm.generation_day > 31 ||
                    billingRuleForm.due_day < 1 ||
                    billingRuleForm.due_day > 31 ||
                    (billingRuleForm.calculation_method !== "manual" && !billingRuleForm.amount.trim())
                  }
                >
                  {isSaving ? "Saving" : editingBillingRuleId ? "Save Billing Rule" : "Create Billing Rule"}
                </button>
              </form>
              ) : null}

              {!isBillingRuleFormOpen ? (
              <section className="data-panel">
                <div className="section-heading">
                  <h2>Billing Rule Registry</h2>
                  <span className="record-count">
                    {isLoadingBillingRules ? "Loading" : `${billingRules.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Charge Type</th>
                        <th>Method</th>
                        <th>Amount</th>
                        <th>Schedule</th>
                        <th>Scope</th>
                        <th>Frequency</th>
                        <th>Penalties</th>
                        <th>Effective</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {billingRules.map((rule) => {
                        const chargeType = chargeTypes.find((item) => item.id === rule.charge_type_id);
                        const building = buildings.find((item) => item.id === rule.building_id);
                        const wing = wings.find((item) => item.id === rule.wing_id);
                        const flatType = flatTypes.find((item) => item.id === rule.flat_type_id);
                        const scopeLabel =
                          rule.scope_type === "building"
                            ? `building: ${building?.name ?? ""}`
                            : rule.scope_type === "wing"
                              ? `wing: ${building?.name ?? ""} / ${wing?.name ?? ""}`
                              : rule.scope_type === "flat_type"
                                ? `flat type: ${flatType?.name ?? ""}`
                                : "all flats";
                        return (
                        <tr key={rule.id}>
                          <td>{rule.name}</td>
                          <td>{chargeType?.name ?? "Unknown"}</td>
                          <td>{rule.calculation_method}</td>
                          <td>{rule.amount ?? ""}</td>
                          <td>
                            Day {rule.generation_day}, due {rule.due_day}
                            {rule.next_generation_date ? `, next ${rule.next_generation_date}` : ""}
                          </td>
                          <td>{scopeLabel}</td>
                          <td>{rule.frequency}</td>
                          <td>{rule.late_fee_rule_ids?.length ?? 0}</td>
                          <td>{[rule.effective_from, rule.effective_to].filter(Boolean).join(" to ")}</td>
                          <td><StatusPill status={rule.status} /></td>
                          <td>
                            <div className="row-actions">
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => startEditBillingRule(rule)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => void handleBillingRuleStatusChange(rule)}
                              >
                                {rule.status === "active" ? "Inactivate" : "Activate"}
                              </button>
                            </div>
                          </td>
                        </tr>
                        );
                      })}
                      {!billingRules.length && !isLoadingBillingRules ? (
                        <tr>
                          <td colSpan={11} className="empty-cell">
                            No billing rules for this society yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
              ) : null}
            </section>
          ) : workspace === "lateFeeRules" ? (
            <section className={`workspace ${isLateFeeRuleFormOpen ? "task-only" : "registry-only"}`}>
              {isLateFeeRuleFormOpen ? (
                <form className="panel-form" onSubmit={handleLateFeeRuleSubmit}>
                  <div className="form-title-row">
                    <h2>{editingLateFeeRuleId ? "Edit Penalty Rule" : "Create Penalty Rule"}</h2>
                    {editingLateFeeRuleId ? (
                      <button
                        type="button"
                        className="secondary compact"
                        onClick={() => {
                          setEditingLateFeeRuleId(null);
                          setLateFeeRuleForm({
                            ...lateFeeRuleFormDefaults,
                            effective_from: todayIsoDate()
                          });
                          setFormWorkspace(null);
                        }}
                      >
                        Cancel
                      </button>
                    ) : null}
                  </div>
                  <div className="context-card">
                    <span>Selected Society</span>
                    <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                  </div>
                  <label>
                    Rule Name
                    <input
                      required
                      maxLength={255}
                      value={lateFeeRuleForm.name}
                      onChange={(event) =>
                        setLateFeeRuleForm({ ...lateFeeRuleForm, name: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Charge Type
                    <select
                      required
                      value={lateFeeRuleForm.charge_type_id}
                      onChange={(event) =>
                        setLateFeeRuleForm({ ...lateFeeRuleForm, charge_type_id: event.target.value })
                      }
                    >
                      <option value="">Select penalty charge type</option>
                      {activeChargeTypes.map((chargeType) => (
                        <option key={chargeType.id} value={chargeType.id}>
                          {chargeType.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="form-grid">
                    <label>
                      Calculation
                      <select
                        required
                        value={lateFeeRuleForm.calculation_method}
                        onChange={(event) =>
                          setLateFeeRuleForm({
                            ...lateFeeRuleForm,
                            calculation_method: event.target.value
                          })
                        }
                      >
                        {lateFeeCalculationMethods.map((method) => (
                          <option key={method} value={method}>
                            {method}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      {lateFeeRuleForm.calculation_method === "fixed" ? "Amount" : "Percent of Due"}
                      <input
                        type="number"
                        min="0.01"
                        step="0.01"
                        required
                        value={lateFeeRuleForm.amount}
                        onChange={(event) =>
                          setLateFeeRuleForm({ ...lateFeeRuleForm, amount: event.target.value })
                        }
                      />
                    </label>
                  </div>
                  <div className="form-grid">
                    <label>
                      Grace Days
                      <input
                        type="number"
                        min="0"
                        required
                        value={lateFeeRuleForm.grace_days}
                        onChange={(event) =>
                          setLateFeeRuleForm({
                            ...lateFeeRuleForm,
                            grace_days: Number(event.target.value)
                          })
                        }
                      />
                    </label>
                    <label>
                      Repeat Interval Days
                      <input
                        type="number"
                        min="1"
                        value={lateFeeRuleForm.repeat_interval_days}
                        onChange={(event) =>
                          setLateFeeRuleForm({
                            ...lateFeeRuleForm,
                            repeat_interval_days: event.target.value
                          })
                        }
                      />
                    </label>
                  </div>
                  <div className="form-grid">
                    <label>
                      Max Applications per Invoice
                      <input
                        type="number"
                        min="1"
                        value={lateFeeRuleForm.max_applications_per_invoice}
                        onChange={(event) =>
                          setLateFeeRuleForm({
                            ...lateFeeRuleForm,
                            max_applications_per_invoice: event.target.value
                          })
                        }
                      />
                    </label>
                    <label>
                      Effective From
                      <input
                        type="date"
                        required
                        value={lateFeeRuleForm.effective_from}
                        onChange={(event) =>
                          setLateFeeRuleForm({ ...lateFeeRuleForm, effective_from: event.target.value })
                        }
                      />
                    </label>
                  </div>
                  <label>
                    Effective To
                    <input
                      type="date"
                      value={lateFeeRuleForm.effective_to}
                      onChange={(event) =>
                        setLateFeeRuleForm({ ...lateFeeRuleForm, effective_to: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Description
                    <textarea
                      value={lateFeeRuleForm.description}
                      onChange={(event) =>
                        setLateFeeRuleForm({ ...lateFeeRuleForm, description: event.target.value })
                      }
                    />
                  </label>
                  <button
                    type="submit"
                    disabled={
                      isSaving ||
                      !selectedTenantId ||
                      !selectedSocietyId ||
                      !lateFeeRuleForm.name.trim() ||
                      !lateFeeRuleForm.charge_type_id ||
                      !lateFeeRuleForm.amount.trim() ||
                      !lateFeeRuleForm.effective_from
                    }
                  >
                    {isSaving ? "Saving" : editingLateFeeRuleId ? "Save Penalty Rule" : "Create Penalty Rule"}
                  </button>
                </form>
              ) : null}

              {!isLateFeeRuleFormOpen ? (
                <section className="data-panel">
                  <div className="section-heading">
                    <h2>Penalty Rule Registry</h2>
                    <span className="record-count">
                      {isLoadingLateFeeRules ? "Loading" : `${lateFeeRules.length} records`}
                    </span>
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Charge Type</th>
                          <th>Calculation</th>
                          <th>Grace</th>
                          <th>Repeat</th>
                          <th>Max</th>
                          <th>Effective</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lateFeeRules.map((rule) => {
                          const chargeType = chargeTypes.find((item) => item.id === rule.charge_type_id);
                          return (
                            <tr key={rule.id}>
                              <td>{rule.name}</td>
                              <td>{chargeType?.name ?? "Unknown"}</td>
                              <td>
                                {rule.calculation_method} / {rule.amount}
                              </td>
                              <td>{rule.grace_days} days</td>
                              <td>{rule.repeat_interval_days ? `${rule.repeat_interval_days} days` : "Once"}</td>
                              <td>{rule.max_applications_per_invoice ?? "No limit"}</td>
                              <td>{[rule.effective_from, rule.effective_to].filter(Boolean).join(" to ")}</td>
                              <td><StatusPill status={rule.status} /></td>
                              <td>
                                <div className="row-actions">
                                  <button
                                    type="button"
                                    className="secondary compact"
                                    onClick={() => startEditLateFeeRule(rule)}
                                  >
                                    Edit
                                  </button>
                                  <button
                                    type="button"
                                    className="secondary compact"
                                    onClick={() => void handleLateFeeRuleStatusChange(rule)}
                                  >
                                    {rule.status === "active" ? "Inactivate" : "Activate"}
                                  </button>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                        {!lateFeeRules.length && !isLoadingLateFeeRules ? (
                          <tr>
                            <td colSpan={9} className="empty-cell">
                              No penalty rules for this society yet.
                            </td>
                          </tr>
                        ) : null}
                      </tbody>
                    </table>
                  </div>
                </section>
              ) : null}
            </section>
          ) : workspace === "lateFeeApplication" ? (
            <section className="workspace task-only">
              <form className="data-panel full-width-panel" onSubmit={handleLateFeePreview}>
                <div className="section-heading">
                  <h2>Apply Penalties</h2>
                  <span className="record-count">
                    {lateFeePreview ? `${lateFeePreview.valid_rows} ready` : "Preview required"}
                  </span>
                </div>
                <div className="context-card">
                  <span>Selected Society</span>
                  <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                </div>
                <label>
                  As of Date
                  <input
                    type="date"
                    required
                    value={lateFeeApplicationForm.as_of_date}
                    onChange={(event) => {
                      setLateFeePreview(null);
                      setLateFeeApplicationForm((current) => ({
                        ...current,
                        as_of_date: event.target.value
                      }));
                    }}
                  />
                </label>
                <div className="rule-picker">
                  {activeLateFeeRules.map((rule) => (
                    <label key={rule.id} className="rule-option">
                      <input
                        type="checkbox"
                        checked={lateFeeApplicationForm.late_fee_rule_ids.includes(rule.id)}
                        onChange={(event) => {
                          setLateFeePreview(null);
                          setLateFeeApplicationForm((current) => ({
                            ...current,
                            late_fee_rule_ids: event.target.checked
                              ? [...current.late_fee_rule_ids, rule.id]
                              : current.late_fee_rule_ids.filter((ruleId) => ruleId !== rule.id)
                          }));
                        }}
                      />
                      <span>
                        <strong>{rule.name}</strong>
                        <small>
                          {rule.calculation_method} / {rule.amount}, grace {rule.grace_days} days
                        </small>
                      </span>
                    </label>
                  ))}
                  {!activeLateFeeRules.length ? (
                    <p className="muted">Create an active penalty rule before applying penalties.</p>
                  ) : null}
                </div>
                <div className="form-actions">
                  <button
                    type="submit"
                    disabled={
                      isSaving ||
                      !selectedTenantId ||
                      !selectedSocietyId ||
                      !lateFeeApplicationForm.as_of_date ||
                      !lateFeeApplicationForm.late_fee_rule_ids.length
                    }
                  >
                    Preview
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={isSaving || !lateFeePreview || lateFeePreview.valid_rows === 0}
                    onClick={() => void handleLateFeeApply()}
                  >
                    Confirm Apply
                  </button>
                </div>
              </form>

              <section className="data-panel full-width-panel">
                <div className="section-heading">
                  <h2>{lateFeePreview ? "Penalty Preview" : "No preview yet"}</h2>
                  <span className="record-count">
                    {lateFeePreview ? `${lateFeePreview.total_penalty_amount} total` : ""}
                  </span>
                </div>
                {lateFeePreview ? (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Invoice</th>
                          <th>Flat</th>
                          <th>Due Date</th>
                          <th>Apply Date</th>
                          <th>Overdue</th>
                          <th>Amount Due</th>
                          <th>Rule</th>
                          <th>Penalty</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lateFeePreview.rows.map((row) => (
                          <tr key={`${row.original_invoice_id}-${row.late_fee_rule_id}-${row.applied_as_of_date}`}>
                            <td>{row.original_invoice_number}</td>
                            <td>{row.flat_number}</td>
                            <td>{row.due_date}</td>
                            <td>{row.applied_as_of_date}</td>
                            <td>{row.days_overdue} days</td>
                            <td>{row.amount_due}</td>
                            <td>{row.late_fee_rule_name}</td>
                            <td>{row.penalty_amount}</td>
                            <td>
                              <StatusPill status={row.status} />
                              {row.errors.length ? <small>{row.errors.join(" ")}</small> : null}
                            </td>
                          </tr>
                        ))}
                        {!lateFeePreview.rows.length ? (
                          <tr>
                            <td colSpan={9} className="empty-cell">
                              No overdue invoices are eligible for the selected rules.
                            </td>
                          </tr>
                        ) : null}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="muted">Select an as-of date and active penalty rules, then preview.</p>
                )}
              </section>
            </section>
          ) : workspace === "scheduledJobs" ? (
            <section className="workspace task-only">
              <section className="data-panel full-width-panel">
                <div className="section-heading">
                  <h2>Due Work</h2>
                  <span className="record-count">
                    {isLoadingScheduledJobs
                      ? "Loading"
                      : scheduledDueWork
                        ? `${scheduledDueWork.billing_due_count + scheduledDueWork.late_fee_due_count} due`
                        : "Not loaded"}
                  </span>
                </div>
                <div className="context-card">
                  <span>Selected Society</span>
                  <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                </div>
                <div className="form-grid two-column">
                  <label>
                    As of Date
                    <input
                      type="date"
                      value={scheduledJobFilters.as_of_date}
                      onChange={(event) =>
                        setScheduledJobFilters({ as_of_date: event.target.value })
                      }
                    />
                  </label>
                  <div className="form-actions align-end">
                    <button
                      type="button"
                      onClick={() => void refreshScheduledJobs(selectedTenantId, selectedSocietyId)}
                      disabled={!selectedTenantId || !selectedSocietyId || isLoadingScheduledJobs}
                    >
                      Check Due Work
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => void handleRunScheduledDueJobs()}
                      disabled={
                        isSaving ||
                        !selectedTenantId ||
                        !selectedSocietyId ||
                        !scheduledDueWork ||
                        scheduledDueWork.billing_due_count + scheduledDueWork.late_fee_due_count === 0
                      }
                    >
                      Run Due Jobs
                    </button>
                  </div>
                </div>
                {scheduledDueWork ? (
                  <div className="metrics-grid compact-metrics">
                    <div className="metric-card">
                      <span>Billing Rules Due</span>
                      <strong>{scheduledDueWork.billing_due_count}</strong>
                    </div>
                    <div className="metric-card">
                      <span>Penalty Rules Due</span>
                      <strong>{scheduledDueWork.late_fee_due_count}</strong>
                    </div>
                  </div>
                ) : null}
              </section>

              <section className="data-panel full-width-panel">
                <div className="section-heading">
                  <h2>Billing Due</h2>
                  <span className="record-count">
                    {scheduledDueWork ? `${scheduledDueWork.billing_rules.length} records` : ""}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Rule</th>
                        <th>Next Date</th>
                        <th>Frequency</th>
                        <th>Schedule</th>
                        <th>Status</th>
                        <th>Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scheduledDueWork?.billing_rules.map((rule) => (
                        <tr key={rule.billing_rule_id}>
                          <td>{rule.billing_rule_name}</td>
                          <td>{rule.next_generation_date ?? ""}</td>
                          <td>{rule.frequency}</td>
                          <td>
                            Day {rule.generation_day}, due {rule.due_day}
                          </td>
                          <td><StatusPill status={rule.status} /></td>
                          <td>{rule.reason}</td>
                        </tr>
                      ))}
                      {scheduledDueWork && !scheduledDueWork.billing_rules.length ? (
                        <tr>
                          <td colSpan={6} className="empty-cell">
                            No billing rules are due for this date.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="data-panel full-width-panel">
                <div className="section-heading">
                  <h2>Penalty Due</h2>
                  <span className="record-count">
                    {scheduledDueWork ? `${scheduledDueWork.late_fee_rules.length} records` : ""}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Rule</th>
                        <th>Grace</th>
                        <th>Eligible Invoices</th>
                        <th>Total Penalty</th>
                        <th>Status</th>
                        <th>Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scheduledDueWork?.late_fee_rules.map((rule) => (
                        <tr key={rule.late_fee_rule_id}>
                          <td>{rule.late_fee_rule_name}</td>
                          <td>{rule.grace_days} days</td>
                          <td>{rule.eligible_invoice_count}</td>
                          <td>{rule.total_penalty_amount}</td>
                          <td><StatusPill status={rule.status} /></td>
                          <td>{rule.reason}</td>
                        </tr>
                      ))}
                      {scheduledDueWork && !scheduledDueWork.late_fee_rules.length ? (
                        <tr>
                          <td colSpan={6} className="empty-cell">
                            No penalty rules are due for this date.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="data-panel full-width-panel">
                <div className="section-heading">
                  <h2>Job Run History</h2>
                  <span className="record-count">{scheduledJobRuns.length} records</span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Mode</th>
                        <th>Status</th>
                        <th>As Of</th>
                        <th>Started</th>
                        <th>Finished</th>
                        <th>Summary</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scheduledJobRuns.map((run) => (
                        <tr key={run.id}>
                          <td>{run.job_type}</td>
                          <td>{run.run_mode}</td>
                          <td><StatusPill status={run.status} /></td>
                          <td>{run.as_of_date}</td>
                          <td>{run.started_at ?? ""}</td>
                          <td>{run.finished_at ?? ""}</td>
                          <td>{run.summary ?? run.error_message ?? ""}</td>
                        </tr>
                      ))}
                      {!scheduledJobRuns.length ? (
                        <tr>
                          <td colSpan={7} className="empty-cell">
                            No scheduled job runs yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : workspace === "invoiceGeneration" ? (
            <section className="workspace task-only">
              <form className="data-panel full-width-panel" onSubmit={handleInvoiceGenerationPreview}>
                <div className="section-heading">
                  <h2>Generate Invoices</h2>
                  <span className="record-count">
                    {invoiceGenerationPreview
                      ? `${invoiceGenerationPreview.valid_rows} ready`
                      : "Preview required"}
                  </span>
                </div>
                <div className="context-card">
                  <span>Selected Society</span>
                  <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                </div>
                <div className="form-grid two-column">
                  <label>
                    Billing Period Start
                    <input
                      type="date"
                      value={invoiceGenerationForm.billing_period_start}
                      onChange={(event) => {
                        setInvoiceGenerationPreview(null);
                        setInvoiceGenerationForm((current) => ({
                          ...current,
                          billing_period_start: event.target.value
                        }));
                      }}
                      required
                    />
                  </label>
                  <label>
                    Billing Period End
                    <input
                      type="date"
                      value={invoiceGenerationForm.billing_period_end}
                      onChange={(event) => {
                        setInvoiceGenerationPreview(null);
                        setInvoiceGenerationForm((current) => ({
                          ...current,
                          billing_period_end: event.target.value
                        }));
                      }}
                      required
                    />
                  </label>
                  <label>
                    Invoice Date
                    <input
                      type="date"
                      value={invoiceGenerationForm.invoice_date}
                      onChange={(event) => {
                        setInvoiceGenerationPreview(null);
                        setInvoiceGenerationForm((current) => ({
                          ...current,
                          invoice_date: event.target.value
                        }));
                      }}
                      required
                    />
                  </label>
                  <label>
                    Due Date
                    <input
                      type="date"
                      value={invoiceGenerationForm.due_date}
                      onChange={(event) => {
                        setInvoiceGenerationPreview(null);
                        setInvoiceGenerationForm((current) => ({
                          ...current,
                          due_date: event.target.value
                        }));
                      }}
                      required
                    />
                  </label>
                </div>
                <div className="rule-picker">
                  <div className="rule-picker-heading">
                    <div>
                      <h3>Billing Rules</h3>
                      <span>
                        {invoiceGenerationForm.billing_rule_ids.length} of{" "}
                        {selectableBillingRules.length} selected
                      </span>
                    </div>
                    <div className="form-actions compact-actions">
                      <button
                        type="button"
                        className="secondary compact"
                        disabled={!selectableBillingRules.length}
                        onClick={selectAllInvoiceGenerationRules}
                      >
                        Select All
                      </button>
                      <button
                        type="button"
                        className="secondary compact"
                        disabled={!invoiceGenerationForm.billing_rule_ids.length}
                        onClick={clearInvoiceGenerationRules}
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                  <div className="rule-grid">
                    {selectableBillingRules.map((rule) => {
                      const chargeType = chargeTypes.find((item) => item.id === rule.charge_type_id);
                      return (
                        <label key={rule.id} className="rule-option">
                          <input
                            type="checkbox"
                            checked={invoiceGenerationForm.billing_rule_ids.includes(rule.id)}
                            onChange={() => toggleInvoiceGenerationRule(rule.id)}
                          />
                          <span>
                            <strong>{rule.name}</strong>
                            <small>
                              {chargeType?.name ?? "Charge"} / {rule.calculation_method} / {rule.frequency}
                            </small>
                          </span>
                        </label>
                      );
                    })}
                    {!selectableBillingRules.length ? (
                      <div className="empty-inline">
                        No active non-manual billing rules are available for generation.
                      </div>
                    ) : null}
                  </div>
                </div>
                <div className="rule-picker">
                  <div className="rule-picker-heading">
                    <div>
                      <h3>Flats</h3>
                      <span>
                        {(invoiceGenerationForm.flat_ids ?? []).length
                          ? `${(invoiceGenerationForm.flat_ids ?? []).length} of ${flats.length} selected`
                          : "All active flats"}
                      </span>
                    </div>
                    <div className="form-actions compact-actions">
                      <button
                        type="button"
                        className="secondary compact"
                        disabled={!flats.length}
                        onClick={selectAllInvoiceGenerationFlats}
                      >
                        Select All
                      </button>
                      <button
                        type="button"
                        className="secondary compact"
                        disabled={!(invoiceGenerationForm.flat_ids ?? []).length}
                        onClick={clearInvoiceGenerationFlats}
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                  <div className="rule-grid">
                    {flats.map((flat) => (
                      <label key={flat.id} className="rule-option">
                        <input
                          type="checkbox"
                          checked={(invoiceGenerationForm.flat_ids ?? []).includes(flat.id)}
                          onChange={() => toggleInvoiceGenerationFlat(flat.id)}
                        />
                        <span>
                          <strong>{flat.flat_number}</strong>
                          <small>{buildings.find((building) => building.id === flat.building_id)?.name ?? "Building"}</small>
                        </span>
                      </label>
                    ))}
                    {!flats.length ? (
                      <div className="empty-inline">
                        No active flats are loaded for this society.
                      </div>
                    ) : null}
                  </div>
                </div>
                <div className="form-actions">
                  <button
                    type="submit"
                    disabled={
                      isSaving ||
                      !selectedSocietyId ||
                      !invoiceGenerationForm.billing_rule_ids.length
                    }
                  >
                    Preview
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={
                      isSaving ||
                      !invoiceGenerationPreview ||
                      invoiceGenerationPreview.invalid_rows > 0 ||
                      invoiceGenerationPreview.invoice_count === 0
                    }
                    onClick={() => void handleInvoiceGenerationConfirm()}
                  >
                    Confirm Generate
                  </button>
                </div>
              </form>

              {invoiceGenerationPreview ? (
                <section className="data-panel full-width-panel">
                  <div className="section-heading">
                    <h2>Generation Preview</h2>
                    <span className="record-count">
                      Total {invoiceGenerationPreview.total_amount}
                    </span>
                  </div>
                  <div className="detail-grid">
                    <div>
                      <span>Total Flats</span>
                      <strong>{invoiceGenerationPreview.total_flats}</strong>
                    </div>
                    <div>
                      <span>Invoices Ready</span>
                      <strong>{invoiceGenerationPreview.invoice_count}</strong>
                    </div>
                    <div>
                      <span>Invalid Rows</span>
                      <strong>{invoiceGenerationPreview.invalid_rows}</strong>
                    </div>
                    <div>
                      <span>Skipped</span>
                      <strong>{invoiceGenerationPreview.skipped_rows}</strong>
                    </div>
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Flat</th>
                          <th>Status</th>
                          <th>Lines</th>
                          <th>Total</th>
                          <th>Errors</th>
                        </tr>
                      </thead>
                      <tbody>
                        {invoiceGenerationPreview.rows.map((row) => (
                          <tr key={row.flat_id}>
                            <td>{row.flat_number}</td>
                            <td><StatusPill status={row.status} /></td>
                            <td>{row.lines.length}</td>
                            <td>{row.total_amount}</td>
                            <td>{row.errors.join(", ")}</td>
                          </tr>
                        ))}
                        {!invoiceGenerationPreview.rows.length ? (
                          <tr>
                            <td colSpan={5} className="empty-cell">
                              No flats found for this society.
                            </td>
                          </tr>
                        ) : null}
                      </tbody>
                    </table>
                  </div>
                </section>
              ) : (
                <div className="empty-state-panel">
                  <h2>No preview yet</h2>
                  <p>Select the billing period, invoice date, and due date, then preview before generating.</p>
                </div>
              )}
            </section>
          ) : workspace === "manualInvoices" ? (
            <section className="workspace task-only">
              <form className="data-panel full-width-panel" onSubmit={handleManualInvoiceSubmit}>
                <div className="section-heading">
                  <h2>Create Manual Invoice</h2>
                  <span className="record-count">Ad hoc charge</span>
                </div>
                <div className="context-card">
                  <span>Selected Society</span>
                  <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                </div>
                <div className="form-grid two-column">
                  <label>
                    Building
                    <select
                      value={manualInvoiceForm.building_id}
                      onChange={(event) => void handleManualInvoiceBuildingChange(event.target.value)}
                      required
                    >
                      <option value="">Select building</option>
                      {activeBuildings.map((building) => (
                        <option key={building.id} value={building.id}>
                          {building.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Flat
                    <select
                      value={manualInvoiceForm.flat_id}
                      disabled={!manualInvoiceForm.building_id}
                      onChange={(event) =>
                        setManualInvoiceForm((current) => ({ ...current, flat_id: event.target.value }))
                      }
                      required
                    >
                      <option value="">Select flat</option>
                      {flats
                        .filter((flat) => flat.building_id === manualInvoiceForm.building_id)
                        .map((flat) => (
                          <option key={flat.id} value={flat.id}>
                            {flat.flat_number}
                          </option>
                        ))}
                    </select>
                  </label>
                  <label>
                    Invoice Date
                    <input
                      type="date"
                      value={manualInvoiceForm.invoice_date}
                      onChange={(event) =>
                        setManualInvoiceForm((current) => ({ ...current, invoice_date: event.target.value }))
                      }
                      required
                    />
                  </label>
                  <label>
                    Due Date
                    <input
                      type="date"
                      value={manualInvoiceForm.due_date}
                      onChange={(event) =>
                        setManualInvoiceForm((current) => ({ ...current, due_date: event.target.value }))
                      }
                      required
                    />
                  </label>
                  <label>
                    Billing Period Start
                    <input
                      type="date"
                      value={manualInvoiceForm.billing_period_start}
                      onChange={(event) =>
                        setManualInvoiceForm((current) => ({
                          ...current,
                          billing_period_start: event.target.value
                        }))
                      }
                      required
                    />
                  </label>
                  <label>
                    Billing Period End
                    <input
                      type="date"
                      value={manualInvoiceForm.billing_period_end}
                      onChange={(event) =>
                        setManualInvoiceForm((current) => ({
                          ...current,
                          billing_period_end: event.target.value
                        }))
                      }
                      required
                    />
                  </label>
                  <label>
                    Charge Type
                    <select
                      value={manualInvoiceForm.charge_type_id}
                      onChange={(event) =>
                        setManualInvoiceForm((current) => ({ ...current, charge_type_id: event.target.value }))
                      }
                      required
                    >
                      <option value="">Select charge type</option>
                      {activeChargeTypes.map((chargeType) => (
                        <option key={chargeType.id} value={chargeType.id}>
                          {chargeType.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Amount
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={manualInvoiceForm.unit_amount}
                      onChange={(event) =>
                        setManualInvoiceForm((current) => ({ ...current, unit_amount: event.target.value }))
                      }
                      required
                    />
                  </label>
                </div>
                <label className="wide-field">
                  Description
                  <input
                    value={manualInvoiceForm.description}
                    onChange={(event) =>
                      setManualInvoiceForm((current) => ({ ...current, description: event.target.value }))
                    }
                    placeholder="Clubhouse booking"
                    required
                  />
                </label>
                <label className="wide-field">
                  Notes
                  <textarea
                    value={manualInvoiceForm.notes}
                    onChange={(event) =>
                      setManualInvoiceForm((current) => ({ ...current, notes: event.target.value }))
                    }
                  />
                </label>
                <label className="wide-field">
                  Applicable Penalty Rules
                  <select
                    multiple
                    value={manualInvoiceForm.late_fee_rule_ids}
                    onChange={(event) =>
                      setManualInvoiceForm((current) => ({
                        ...current,
                        late_fee_rule_ids: Array.from(event.target.selectedOptions, (option) => option.value)
                      }))
                    }
                  >
                    {activeLateFeeRules.map((rule) => (
                      <option key={rule.id} value={rule.id}>
                        {rule.name}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="detail-grid">
                  <div>
                    <span>Total</span>
                    <strong>{manualInvoiceForm.unit_amount || "0.00"}</strong>
                  </div>
                  <div>
                    <span>Quantity</span>
                    <strong>{manualInvoiceForm.quantity}</strong>
                  </div>
                </div>
                <div className="form-actions">
                  <button
                    type="submit"
                    disabled={
                      isSaving ||
                      !selectedSocietyId ||
                      !manualInvoiceForm.flat_id ||
                      !manualInvoiceForm.charge_type_id ||
                      !manualInvoiceForm.description.trim() ||
                      !manualInvoiceForm.unit_amount
                    }
                  >
                    {isSaving ? "Saving" : "Create Invoice"}
                  </button>
                </div>
              </form>
            </section>
          ) : workspace === "invoices" ? (
            <section className="workspace registry-only">
              {selectedInvoiceId ? (
                <section className="data-panel">
                  <div className="section-heading">
                    <div>
                      <h2>Invoice Detail</h2>
                      <span className="record-count">
                        {selectedInvoiceDetail ? selectedInvoiceDetail.invoice_number : "Loading"}
                      </span>
                    </div>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => {
                        setSelectedInvoiceId("");
                        setSelectedInvoiceDetail(null);
                      }}
                    >
                      Back
                    </button>
                  </div>
                  {selectedInvoiceDetail ? (
                    <>
                      <div className="form-actions">
                        <button
                          type="button"
                          disabled={
                            selectedInvoiceDetail.status === "paid" ||
                            selectedInvoiceDetail.status === "cancelled" ||
                            Number(selectedInvoiceDetail.amount_due) <= 0
                          }
                          onClick={() => startInvoicePaymentCollection(selectedInvoiceDetail)}
                        >
                          Collect Payment
                        </button>
                      </div>
                      <div className="detail-grid">
                        <div>
                          <span>Invoice Date</span>
                          <strong>{selectedInvoiceDetail.invoice_date}</strong>
                        </div>
                        <div>
                          <span>Due Date</span>
                          <strong>{selectedInvoiceDetail.due_date}</strong>
                        </div>
                        <div>
                          <span>Period</span>
                          <strong>
                            {selectedInvoiceDetail.billing_period_start} to {selectedInvoiceDetail.billing_period_end}
                          </strong>
                        </div>
                        <div>
                          <span>Total</span>
                          <strong>{selectedInvoiceDetail.total_amount}</strong>
                        </div>
                        <div>
                          <span>Paid</span>
                          <strong>{selectedInvoiceDetail.amount_paid}</strong>
                        </div>
                        <div>
                          <span>Balance</span>
                          <strong>{selectedInvoiceDetail.amount_due}</strong>
                        </div>
                        <div>
                          <span>Status</span>
                          <strong>{selectedInvoiceDetail.status}</strong>
                        </div>
                      </div>
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>#</th>
                              <th>Description</th>
                              <th>Quantity</th>
                              <th>Rate</th>
                              <th>Amount</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedInvoiceDetail.line_items.map((line) => (
                              <tr key={line.id}>
                                <td>{line.line_number}</td>
                                <td>{line.description}</td>
                                <td>{line.quantity}</td>
                                <td>{line.unit_amount}</td>
                                <td>{line.line_amount}</td>
                              </tr>
                            ))}
                            {!selectedInvoiceDetail.line_items.length ? (
                              <tr>
                                <td colSpan={5} className="empty-cell">
                                  No line items on this invoice.
                                </td>
                              </tr>
                            ) : null}
                          </tbody>
                        </table>
                      </div>
                    </>
                  ) : (
                    <div className="empty-state-panel">
                      <h2>Loading invoice</h2>
                      <p>Fetching invoice detail.</p>
                    </div>
                  )}
                </section>
              ) : (
                <>
                  <section className="data-panel full-width-panel">
                    <div className="section-heading">
                      <h2>Invoice Filters</h2>
                      <span className="record-count">Blank filters show all invoices</span>
                    </div>
                    <div className="form-grid">
                      <label>
                        Month
                        <input
                          type="month"
                          value={invoiceFilters.month}
                          onChange={(event) => {
                            const month = event.target.value;
                            const range = monthDateRange(month);
                            setInvoiceFilters((current) => ({
                              ...current,
                              month,
                              invoice_date_from: range.from,
                              invoice_date_to: range.to,
                              page: 1
                            }));
                          }}
                        />
                      </label>
                      <label>
                        Date From
                        <input
                          type="date"
                          value={invoiceFilters.invoice_date_from}
                          onChange={(event) =>
                            setInvoiceFilters((current) => ({
                              ...current,
                              month: "",
                              invoice_date_from: event.target.value,
                              page: 1
                            }))
                          }
                        />
                      </label>
                      <label>
                        Date To
                        <input
                          type="date"
                          value={invoiceFilters.invoice_date_to}
                          onChange={(event) =>
                            setInvoiceFilters((current) => ({
                              ...current,
                              month: "",
                              invoice_date_to: event.target.value,
                              page: 1
                            }))
                          }
                        />
                      </label>
                      <label>
                        Due From
                        <input
                          type="date"
                          value={invoiceFilters.due_date_from}
                          onChange={(event) =>
                            setInvoiceFilters((current) => ({
                              ...current,
                              due_date_from: event.target.value,
                              page: 1
                            }))
                          }
                        />
                      </label>
                      <label>
                        Due To
                        <input
                          type="date"
                          value={invoiceFilters.due_date_to}
                          onChange={(event) =>
                            setInvoiceFilters((current) => ({
                              ...current,
                              due_date_to: event.target.value,
                              page: 1
                            }))
                          }
                        />
                      </label>
                      <label>
                        Flat
                        <select
                          value={invoiceFilters.flat_id}
                          onChange={(event) =>
                            setInvoiceFilters((current) => ({ ...current, flat_id: event.target.value, page: 1 }))
                          }
                        >
                          <option value="">All flats</option>
                          {flats.map((flat) => (
                            <option key={flat.id} value={flat.id}>
                              {flat.flat_number}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label>
                        Status
                        <select
                          value={invoiceFilters.status}
                          onChange={(event) =>
                            setInvoiceFilters((current) => ({ ...current, status: event.target.value, page: 1 }))
                          }
                        >
                          <option value="">All statuses</option>
                          {invoiceStatuses.map((statusValue) => (
                            <option key={statusValue} value={statusValue}>
                              {statusValue}
                            </option>
                          ))}
                        </select>
                      </label>
                    </div>
                    <div className="form-actions">
                      <button
                        type="button"
                        disabled={!selectedTenantId || !selectedSocietyId || isLoadingInvoices}
                        onClick={() => {
                          const nextFilters = { ...invoiceFilters, page: 1 };
                          setInvoiceFilters(nextFilters);
                          void refreshInvoices(selectedTenantId, selectedSocietyId, token, nextFilters);
                        }}
                      >
                        Apply Filters
                      </button>
                      <button
                        type="button"
                        className="secondary"
                        disabled={isLoadingInvoices}
                        onClick={() => {
                          setInvoiceFilters(invoiceFilterDefaults);
                          void refreshInvoices(
                            selectedTenantId,
                            selectedSocietyId,
                            token,
                            invoiceFilterDefaults
                          );
                        }}
                      >
                        Clear
                      </button>
                    </div>
                  </section>
                  <section className="data-panel">
                    <div className="section-heading">
                      <h2>Invoice Registry</h2>
                      <div className="row-actions">
                        <label className="compact-field">
                          Rows
                          <select
                            value={invoiceFilters.page_size}
                            onChange={(event) => {
                              const nextFilters = {
                                ...invoiceFilters,
                                page: 1,
                                page_size: Number(event.target.value)
                              };
                              setInvoiceFilters(nextFilters);
                              void refreshInvoices(selectedTenantId, selectedSocietyId, token, nextFilters);
                            }}
                          >
                            {[25, 50, 100, 200].map((pageSize) => (
                              <option key={pageSize} value={pageSize}>
                                {pageSize}
                              </option>
                            ))}
                          </select>
                        </label>
                        <button
                          type="button"
                          className="secondary compact"
                          disabled={isLoadingInvoices || invoiceFilters.page <= 1}
                          onClick={() => {
                            const nextFilters = {
                              ...invoiceFilters,
                              page: Math.max(invoiceFilters.page - 1, 1)
                            };
                            setInvoiceFilters(nextFilters);
                            void refreshInvoices(selectedTenantId, selectedSocietyId, token, nextFilters);
                          }}
                        >
                          Previous
                        </button>
                        <span className="record-count">
                          Page {invoiceFilters.page} of {Math.max(invoiceTotalPages, 1)}
                        </span>
                        <button
                          type="button"
                          className="secondary compact"
                          disabled={isLoadingInvoices || invoiceFilters.page >= Math.max(invoiceTotalPages, 1)}
                          onClick={() => {
                            const nextFilters = {
                              ...invoiceFilters,
                              page: invoiceFilters.page + 1
                            };
                            setInvoiceFilters(nextFilters);
                            void refreshInvoices(selectedTenantId, selectedSocietyId, token, nextFilters);
                          }}
                        >
                          Next
                        </button>
                        <button
                          type="button"
                          className="secondary compact"
                          disabled={!selectedInvoiceIds.length || isSaving}
                          onClick={handleBulkInvoiceCancel}
                        >
                          Cancel Selected
                        </button>
                        <span className="record-count">
                          {isLoadingInvoices ? "Loading" : `${invoiceTotalItems} records`}
                        </span>
                      </div>
                    </div>
                    {!invoices.length && !isLoadingInvoices ? (
                      <div className="empty-state-panel">
                        <h2>No invoices found</h2>
                        <p>Clear filters or use Invoice Generation to create bills for a selected period.</p>
                      </div>
                    ) : (
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>
                                <input
                                  type="checkbox"
                                  aria-label="Select cancellable invoices"
                                  checked={
                                    invoices.some(
                                      (invoice) =>
                                        invoice.status !== "cancelled" && Number(invoice.amount_paid) === 0
                                    ) &&
                                    invoices
                                      .filter(
                                        (invoice) =>
                                          invoice.status !== "cancelled" && Number(invoice.amount_paid) === 0
                                      )
                                      .every((invoice) => selectedInvoiceIds.includes(invoice.id))
                                  }
                                  onChange={(event) => {
                                    const visibleCancellableIds = invoices
                                      .filter(
                                        (invoice) =>
                                          invoice.status !== "cancelled" && Number(invoice.amount_paid) === 0
                                      )
                                      .map((invoice) => invoice.id);
                                    setSelectedInvoiceIds((current) =>
                                      event.target.checked
                                        ? Array.from(new Set([...current, ...visibleCancellableIds]))
                                        : current.filter((invoiceId) => !visibleCancellableIds.includes(invoiceId))
                                    );
                                  }}
                                />
                              </th>
                              <th>Invoice</th>
                              <th>Flat</th>
                              <th>Date</th>
                              <th>Due</th>
                              <th>Total</th>
                              <th>Balance</th>
                              <th>Status</th>
                              <th>Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {invoices.map((invoice) => {
                              const flat = flats.find((item) => item.id === invoice.flat_id);
                              return (
                                <tr
                                  key={invoice.id}
                                  className="clickable-row"
                                  onClick={() => setSelectedInvoiceId(invoice.id)}
                                >
                                  <td>
                                    <input
                                      type="checkbox"
                                      aria-label={`Select invoice ${invoice.invoice_number}`}
                                      disabled={invoice.status === "cancelled" || Number(invoice.amount_paid) > 0}
                                      checked={selectedInvoiceIds.includes(invoice.id)}
                                      onClick={(event) => event.stopPropagation()}
                                      onChange={(event) =>
                                        setSelectedInvoiceIds((current) =>
                                          event.target.checked
                                            ? [...current, invoice.id]
                                            : current.filter((invoiceId) => invoiceId !== invoice.id)
                                        )
                                      }
                                    />
                                  </td>
                                  <td>{invoice.invoice_number}</td>
                                  <td>{flat?.flat_number ?? ""}</td>
                                  <td>{invoice.invoice_date}</td>
                                  <td>{invoice.due_date}</td>
                                  <td>{invoice.total_amount}</td>
                                  <td>{invoice.amount_due}</td>
                                  <td><StatusPill status={invoice.status} /></td>
                                  <td>
                                    <button
                                      type="button"
                                      className="secondary compact"
                                      disabled={
                                        invoice.status === "paid" ||
                                        invoice.status === "cancelled" ||
                                        Number(invoice.amount_due) <= 0
                                      }
                                      onClick={(event) => {
                                        event.stopPropagation();
                                        startInvoicePaymentCollection(invoice);
                                      }}
                                    >
                                      Collect
                                    </button>
                                    <button
                                      type="button"
                                      className="secondary compact"
                                      disabled={invoice.status === "cancelled" || Number(invoice.amount_paid) > 0}
                                      onClick={(event) => {
                                        event.stopPropagation();
                                        void handleInvoiceCancel(invoice);
                                      }}
                                    >
                                      Cancel
                                    </button>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </section>
                </>
              )}
            </section>
          ) : workspace === "payments" ? (
            <section className="workspace">
              <form className="panel-form" onSubmit={handlePaymentSubmit}>
                <h2>Record Payment</h2>
                <label>
                  Building
                  <select
                    value={paymentForm.building_id}
                    onChange={(event) => void handlePaymentBuildingChange(event.target.value)}
                    required
                  >
                    <option value="">Select building</option>
                    {activeBuildings.map((building) => (
                      <option key={building.id} value={building.id}>
                        {building.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Flat
                  <select
                    value={paymentForm.flat_id}
                    disabled={!paymentForm.building_id}
                    onChange={(event) => void handlePaymentFlatChange(event.target.value)}
                    required
                  >
                    <option value="">Select flat</option>
                    {flats
                      .filter((flat) => flat.building_id === paymentForm.building_id)
                      .map((flat) => (
                        <option key={flat.id} value={flat.id}>
                          {flat.flat_number}
                        </option>
                      ))}
                  </select>
                </label>
                <div className="form-grid">
                  <label>
                    Payment Date
                    <input
                      type="date"
                      value={paymentForm.payment_date}
                      onChange={(event) =>
                        setPaymentForm((current) => ({ ...current, payment_date: event.target.value }))
                      }
                      required
                    />
                  </label>
                  <label>
                    Amount
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={paymentForm.amount}
                      onChange={(event) => {
                        const amount = event.target.value;
                        setPaymentForm((current) => ({ ...current, amount }));
                        setPaymentAllocations(buildOldestFirstPaymentAllocations(paymentOpenInvoices, amount));
                      }}
                      required
                    />
                  </label>
                </div>
                <label>
                  Payment Mode
                  <select
                    value={paymentForm.payment_mode}
                    onChange={(event) =>
                      setPaymentForm((current) => ({ ...current, payment_mode: event.target.value }))
                    }
                  >
                    {paymentModes.map((mode) => (
                      <option key={mode} value={mode}>
                        {mode}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Deposit Account
                  <select
                    value={paymentForm.deposit_account_id}
                    onChange={(event) =>
                      setPaymentForm((current) => ({ ...current, deposit_account_id: event.target.value }))
                    }
                    required
                  >
                    <option value="">Select deposit account</option>
                    {activeAssetAccounts.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.account_code} - {account.account_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Reference
                  <input
                    value={paymentForm.reference_number}
                    onChange={(event) =>
                      setPaymentForm((current) => ({ ...current, reference_number: event.target.value }))
                    }
                  />
                </label>
                <label>
                  Notes
                  <textarea
                    value={paymentForm.notes}
                    onChange={(event) =>
                      setPaymentForm((current) => ({ ...current, notes: event.target.value }))
                    }
                  />
                </label>
                <div className="context-card">
                  <span>Allocated / Unapplied</span>
                  <strong>
                    {paymentAllocatedTotal.toFixed(2)} /{" "}
                    {Math.max((Number(paymentForm.amount) || 0) - paymentAllocatedTotal, 0).toFixed(2)}
                  </strong>
                </div>
                <button
                  type="submit"
                  disabled={
                    isSaving ||
                    !paymentForm.flat_id ||
                    !paymentForm.deposit_account_id ||
                    !paymentForm.amount ||
                    paymentAllocatedTotal > Number(paymentForm.amount)
                  }
                >
                  {isSaving ? "Saving" : "Record Payment"}
                </button>
              </form>

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Open Invoices</h2>
                  <span className="record-count">
                    {isLoadingPaymentOpenInvoices ? "Loading" : `${paymentOpenInvoices.length} open`}
                  </span>
                </div>
                <div className="form-actions">
                  <button
                    type="button"
                    className="secondary"
                    disabled={!paymentForm.amount || !paymentOpenInvoices.length}
                    onClick={() =>
                      setPaymentAllocations(
                        buildOldestFirstPaymentAllocations(paymentOpenInvoices, paymentForm.amount)
                      )
                    }
                  >
                    Auto Allocate Oldest
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={!Object.keys(paymentAllocations).length}
                    onClick={() => setPaymentAllocations({})}
                  >
                    Clear Allocations
                  </button>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Invoice</th>
                        <th>Due</th>
                        <th>Balance</th>
                        <th>Allocate</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paymentOpenInvoices.map((invoice) => (
                        <tr key={invoice.id}>
                          <td>{invoice.invoice_number}</td>
                          <td>{invoice.due_date}</td>
                          <td>{invoice.amount_due}</td>
                          <td>
                            <input
                              type="number"
                              min="0"
                              max={invoice.amount_due}
                              step="0.01"
                              value={paymentAllocations[invoice.id] ?? ""}
                              onChange={(event) =>
                                setPaymentAllocations((current) => ({
                                  ...current,
                                  [invoice.id]: event.target.value
                                }))
                              }
                            />
                          </td>
                        </tr>
                      ))}
                      {!paymentOpenInvoices.length ? (
                        <tr>
                          <td colSpan={4} className="empty-cell">
                            {isLoadingPaymentOpenInvoices
                              ? "Loading open invoices for this flat."
                              : paymentForm.flat_id
                                ? "No open invoices for this flat."
                                : "Select a flat with open invoices."}
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
                <div className="section-heading">
                  <h2>Payment Result</h2>
                  <span className="record-count">Latest saved payment</span>
                </div>
                {lastPaymentResult ? (
                  <div className="payment-result">
                    <div className="metrics-grid compact-metrics">
                      <div className="metric-card">
                        <span>Payment Date</span>
                        <strong>{lastPaymentResult.payment.payment_date}</strong>
                      </div>
                      <div className="metric-card">
                        <span>Amount</span>
                        <strong>{lastPaymentResult.payment.amount}</strong>
                      </div>
                      <div className="metric-card">
                        <span>Unapplied Advance</span>
                        <strong>{lastPaymentResult.payment.unapplied_amount}</strong>
                      </div>
                      <div className="metric-card">
                        <span>Status</span>
                        <strong>{lastPaymentResult.payment.status}</strong>
                      </div>
                    </div>

                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Allocated To</th>
                            <th>Type</th>
                            <th>Due</th>
                            <th>Amount</th>
                          </tr>
                        </thead>
                        <tbody>
                          {lastPaymentResult.payment.allocations.map((allocation) => {
                            const invoice = lastPaymentResult.invoices.find(
                              (item) => item.id === allocation.invoice_id
                            );
                            return (
                              <tr key={allocation.id}>
                                <td>{invoice?.invoice_number ?? allocation.invoice_id}</td>
                                <td>{paymentInvoiceLabel(invoice)}</td>
                                <td>{invoice?.due_date ?? ""}</td>
                                <td>{allocation.allocated_amount}</td>
                              </tr>
                            );
                          })}
                          {!lastPaymentResult.payment.allocations.length ? (
                            <tr>
                              <td colSpan={4} className="empty-cell">
                                No invoice allocation. Full amount was recorded as advance.
                              </td>
                            </tr>
                          ) : null}
                        </tbody>
                      </table>
                    </div>

                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Auto-cancelled Penalty</th>
                            <th>Date</th>
                            <th>Due</th>
                            <th>Amount</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {lastPaymentResult.payment.auto_cancelled_penalty_invoices.map((invoice) => (
                            <tr key={invoice.id}>
                              <td>{invoice.invoice_number}</td>
                              <td>{invoice.invoice_date}</td>
                              <td>{invoice.due_date}</td>
                              <td>{invoice.total_amount}</td>
                              <td><StatusPill status={invoice.status} /></td>
                            </tr>
                          ))}
                          {!lastPaymentResult.payment.auto_cancelled_penalty_invoices.length ? (
                            <tr>
                              <td colSpan={5} className="empty-cell">
                                No penalties were auto-cancelled for this payment.
                              </td>
                            </tr>
                          ) : null}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="empty-state-panel">
                    <h3>No payment result yet</h3>
                    <p>Record a payment to see allocations, advance, and cancelled penalties here.</p>
                  </div>
                )}
              </section>
            </section>
          ) : workspace === "paymentRegister" ? (
            <section className="workspace registry-only">
              <section className="data-panel full-width-panel">
                <div className="section-heading">
                  <h2>Payment Register Filters</h2>
                  <span className="record-count">Blank filters show all payments</span>
                </div>
                <div className="form-grid">
                  <label>
                    Month
                    <input
                      type="month"
                      value={paymentRegisterFilters.month}
                      onChange={(event) => {
                        const month = event.target.value;
                        const range = monthDateRange(month);
                        setPaymentRegisterFilters((current) => ({
                          ...current,
                          month,
                          payment_date_from: range.from,
                          payment_date_to: range.to,
                          page: 1
                        }));
                      }}
                    />
                  </label>
                  <label>
                    Date From
                    <input
                      type="date"
                      value={paymentRegisterFilters.payment_date_from}
                      onChange={(event) =>
                        setPaymentRegisterFilters((current) => ({
                          ...current,
                          month: "",
                          payment_date_from: event.target.value,
                          page: 1
                        }))
                      }
                    />
                  </label>
                  <label>
                    Date To
                    <input
                      type="date"
                      value={paymentRegisterFilters.payment_date_to}
                      onChange={(event) =>
                        setPaymentRegisterFilters((current) => ({
                          ...current,
                          month: "",
                          payment_date_to: event.target.value,
                          page: 1
                        }))
                      }
                    />
                  </label>
                  <label>
                    Flat Number
                    <input
                      value={paymentRegisterFilters.flat_number}
                      onChange={(event) =>
                        setPaymentRegisterFilters((current) => ({
                          ...current,
                          flat_number: event.target.value,
                          page: 1
                        }))
                      }
                    />
                  </label>
                  <label>
                    Mode
                    <select
                      value={paymentRegisterFilters.payment_mode}
                      onChange={(event) =>
                        setPaymentRegisterFilters((current) => ({
                          ...current,
                          payment_mode: event.target.value,
                          page: 1
                        }))
                      }
                    >
                      <option value="">All modes</option>
                      {paymentModes.map((mode) => (
                        <option key={mode} value={mode}>
                          {mode}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Status
                    <select
                      value={paymentRegisterFilters.status}
                      onChange={(event) =>
                        setPaymentRegisterFilters((current) => ({
                          ...current,
                          status: event.target.value,
                          page: 1
                        }))
                      }
                    >
                      <option value="">All statuses</option>
                      {paymentStatuses.map((statusValue) => (
                        <option key={statusValue} value={statusValue}>
                          {statusValue}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="form-actions">
                  <button
                    type="button"
                    onClick={() => {
                      const nextFilters = { ...paymentRegisterFilters, page: 1 };
                      setPaymentRegisterFilters(nextFilters);
                      void refreshPaymentRegister(selectedTenantId, selectedSocietyId, token, nextFilters);
                    }}
                  >
                    Apply Filters
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => {
                      setPaymentRegisterFilters(paymentRegisterFilterDefaults);
                      void refreshPaymentRegister(
                        selectedTenantId,
                        selectedSocietyId,
                        token,
                        paymentRegisterFilterDefaults
                      );
                    }}
                  >
                    Clear
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={isSaving || !paymentRegisterRows.length}
                    onClick={() => void handlePaymentRegisterExport("xlsx")}
                  >
                    Excel
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={isSaving || !paymentRegisterRows.length}
                    onClick={() => void handlePaymentRegisterExport("pdf")}
                  >
                    PDF
                  </button>
                </div>
              </section>

              <section className="data-panel full-width-panel">
                <div className="section-heading">
                  <h2>Payment Register</h2>
                  <span className="record-count">
                    {isLoadingPaymentRegister ? "Loading" : `${paymentRegisterTotalItems} records`}
                  </span>
                </div>
                <div className="pagination-bar">
                  <label>
                    Rows
                    <select
                      value={paymentRegisterFilters.page_size}
                      onChange={(event) => {
                        const nextFilters = {
                          ...paymentRegisterFilters,
                          page: 1,
                          page_size: Number(event.target.value)
                        };
                        setPaymentRegisterFilters(nextFilters);
                        void refreshPaymentRegister(selectedTenantId, selectedSocietyId, token, nextFilters);
                      }}
                    >
                      {[25, 50, 100, 200].map((size) => (
                        <option key={size} value={size}>
                          {size}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button
                    type="button"
                    className="secondary compact"
                    disabled={isLoadingPaymentRegister || paymentRegisterFilters.page <= 1}
                    onClick={() => {
                      const nextFilters = {
                        ...paymentRegisterFilters,
                        page: Math.max(paymentRegisterFilters.page - 1, 1)
                      };
                      setPaymentRegisterFilters(nextFilters);
                      void refreshPaymentRegister(selectedTenantId, selectedSocietyId, token, nextFilters);
                    }}
                  >
                    Previous
                  </button>
                  <span className="record-count">
                    Page {paymentRegisterFilters.page} of {Math.max(paymentRegisterTotalPages, 1)}
                  </span>
                  <button
                    type="button"
                    className="secondary compact"
                    disabled={
                      isLoadingPaymentRegister ||
                      paymentRegisterFilters.page >= Math.max(paymentRegisterTotalPages, 1)
                    }
                    onClick={() => {
                      const nextFilters = {
                        ...paymentRegisterFilters,
                        page: paymentRegisterFilters.page + 1
                      };
                      setPaymentRegisterFilters(nextFilters);
                      void refreshPaymentRegister(selectedTenantId, selectedSocietyId, token, nextFilters);
                    }}
                  >
                    Next
                  </button>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Flat</th>
                        <th>Building</th>
                        <th>Mode</th>
                        <th>Reference</th>
                        <th>Amount</th>
                        <th>Unapplied</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paymentRegisterRows.map((payment) => (
                        <tr key={payment.id}>
                          <td>{payment.payment_date}</td>
                          <td>
                            <strong>{payment.flat_number}</strong>
                            {payment.wing_name ? <span className="table-subtext">{payment.wing_name}</span> : null}
                          </td>
                          <td>{payment.building_name}</td>
                          <td>{payment.payment_mode}</td>
                          <td>{payment.reference_number ?? ""}</td>
                          <td>{payment.amount}</td>
                          <td>{payment.unapplied_amount}</td>
                          <td><StatusPill status={payment.status} /></td>
                          <td>
                            <button
                              type="button"
                              className="secondary compact"
                              disabled={isSaving || payment.status !== "received"}
                              onClick={() => handlePaymentRegisterReverse(payment)}
                            >
                              Reverse
                            </button>
                          </td>
                        </tr>
                      ))}
                      {!paymentRegisterRows.length && !isLoadingPaymentRegister ? (
                        <tr>
                          <td colSpan={9} className="empty-cell">
                            No payments match the selected filters.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : workspace === "operationalReports" ? (
            <section className="workspace registry-only">
              <section className="data-panel">
                <form className="filter-bar report-filter-bar" onSubmit={handleOperationalReportSubmit}>
                  <label>
                    Report
                    <select
                      value={operationalReportType}
                      onChange={(event) => {
                        setOperationalReport(null);
                        setOperationalReportType(event.target.value as OperationalReportType);
                      }}
                    >
                      {operationalReportTypes.map((report) => (
                        <option key={report.value} value={report.value}>
                          {report.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  {operationalReportTypes.find((report) => report.value === operationalReportType)?.mode ===
                  "period" ? (
                    <>
                      <label>
                        Period Start
                        <input
                          required
                          type="date"
                          value={operationalReportFilters.period_start}
                          onChange={(event) => {
                            setOperationalReport(null);
                            setOperationalReportFilters({
                              ...operationalReportFilters,
                              period_start: event.target.value
                            });
                          }}
                        />
                      </label>
                      <label>
                        Period End
                        <input
                          required
                          type="date"
                          value={operationalReportFilters.period_end}
                          onChange={(event) => {
                            setOperationalReport(null);
                            setOperationalReportFilters({
                              ...operationalReportFilters,
                              period_end: event.target.value
                            });
                          }}
                        />
                      </label>
                    </>
                  ) : (
                    <label>
                      As Of Date
                      <input
                        required
                        type="date"
                        value={operationalReportFilters.as_of_date}
                        onChange={(event) => {
                          setOperationalReport(null);
                          setOperationalReportFilters({
                            ...operationalReportFilters,
                            as_of_date: event.target.value
                          });
                        }}
                      />
                    </label>
                  )}
                  <button type="submit" disabled={isLoadingOperationalReport}>
                    {isLoadingOperationalReport ? "Loading" : "Apply"}
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={isSaving || !operationalReport}
                    onClick={() => void handleOperationalReportExport("xlsx")}
                  >
                    Excel
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={isSaving || !operationalReport}
                    onClick={() => void handleOperationalReportExport("pdf")}
                  >
                    PDF
                  </button>
                </form>
              </section>

              <section className="data-panel">
                <div className="section-heading">
                  <h2>
                    {operationalReportTypes.find((report) => report.value === operationalReportType)?.label ??
                      "Reports"}
                  </h2>
                  <span className="record-count">
                    {isLoadingOperationalReport
                      ? "Loading"
                      : operationalReport
                        ? operationalReportType === "billing"
                          ? `${(operationalReport as BillingReport).invoice_count} invoices`
                          : operationalReportType === "collection"
                            ? `${(operationalReport as CollectionReport).payment_count} payments`
                          : operationalReportType === "expenses"
                            ? `${(operationalReport as ExpenseOperationalReport).expense_count} expenses`
                          : operationalReportType === "defaulters"
                            ? `${(operationalReport as DefaulterReport).defaulter_count} defaulters`
                            : `${(operationalReport as OutstandingSummary).flats_with_outstanding} flats`
                        : "No report loaded"}
                  </span>
                </div>

                {operationalReport ? (
                  <>
                    <div className="metrics-grid compact-metrics">
                      {operationalReportType === "billing" ? (
                        <>
                          <article className="metric-tile"><span>Billed</span><strong>{(operationalReport as BillingReport).total_billed}</strong></article>
                          <article className="metric-tile"><span>Paid</span><strong>{(operationalReport as BillingReport).total_paid}</strong></article>
                          <article className="metric-tile"><span>Due</span><strong>{(operationalReport as BillingReport).total_due}</strong></article>
                        </>
                      ) : operationalReportType === "collection" ? (
                        <>
                          <article className="metric-tile"><span>Collected</span><strong>{(operationalReport as CollectionReport).total_collected}</strong></article>
                          <article className="metric-tile"><span>Unapplied</span><strong>{(operationalReport as CollectionReport).total_unapplied}</strong></article>
                          <article className="metric-tile"><span>Payments</span><strong>{(operationalReport as CollectionReport).payment_count}</strong></article>
                        </>
                      ) : operationalReportType === "expenses" ? (
                        <>
                          <article className="metric-tile"><span>Total Expense</span><strong>{(operationalReport as ExpenseOperationalReport).total_expense}</strong></article>
                          <article className="metric-tile"><span>Paid</span><strong>{(operationalReport as ExpenseOperationalReport).total_paid}</strong></article>
                          <article className="metric-tile"><span>Due</span><strong>{(operationalReport as ExpenseOperationalReport).total_due}</strong></article>
                        </>
                      ) : operationalReportType === "defaulters" ? (
                        <>
                          <article className="metric-tile"><span>Defaulters</span><strong>{(operationalReport as DefaulterReport).defaulter_count}</strong></article>
                          <article className="metric-tile"><span>Overdue</span><strong>{(operationalReport as DefaulterReport).total_overdue}</strong></article>
                        </>
                      ) : (
                        <>
                          <article className="metric-tile"><span>Outstanding</span><strong>{(operationalReport as OutstandingSummary).total_outstanding}</strong></article>
                          <article className="metric-tile"><span>Overdue</span><strong>{(operationalReport as OutstandingSummary).overdue_amount}</strong></article>
                          <article className="metric-tile"><span>Flats</span><strong>{(operationalReport as OutstandingSummary).flats_with_outstanding}</strong></article>
                        </>
                      )}
                    </div>
                    <div className="table-wrap">
                      <table>
                        {operationalReportType === "billing" ? (
                          <>
                            <thead><tr><th>Invoice</th><th>Flat</th><th>Date</th><th>Due Date</th><th>Total</th><th>Paid</th><th>Due</th><th>Status</th></tr></thead>
                            <tbody>{(operationalReport as BillingReport).rows.map((row) => (
                              <tr key={row.invoice_id}><td>{row.invoice_number}</td><td>{row.flat_number}</td><td>{row.invoice_date}</td><td>{row.due_date}</td><td>{row.total_amount}</td><td>{row.amount_paid}</td><td>{row.amount_due}</td><td><StatusPill status={row.status} /></td></tr>
                            ))}</tbody>
                          </>
                        ) : operationalReportType === "collection" ? (
                          <>
                            <thead><tr><th>Date</th><th>Flat</th><th>Mode</th><th>Reference</th><th>Amount</th><th>Unapplied</th><th>Status</th></tr></thead>
                            <tbody>{(operationalReport as CollectionReport).rows.map((row) => (
                              <tr key={row.payment_id}><td>{row.payment_date}</td><td>{row.flat_number}</td><td>{row.payment_mode}</td><td>{row.reference_number ?? ""}</td><td>{row.amount}</td><td>{row.unapplied_amount}</td><td><StatusPill status={row.status} /></td></tr>
                            ))}</tbody>
                          </>
                        ) : operationalReportType === "expenses" ? (
                          <>
                            <thead><tr><th>Date</th><th>Category</th><th>Vendor</th><th>Description</th><th>Total</th><th>Paid</th><th>Due</th><th>Status</th></tr></thead>
                            <tbody>{(operationalReport as ExpenseOperationalReport).rows.map((row) => (
                              <tr key={row.expense_id}><td>{row.expense_date}</td><td>{row.category_name}</td><td>{row.vendor_name ?? ""}</td><td>{row.description}</td><td>{row.total_amount}</td><td>{row.amount_paid}</td><td>{row.amount_due}</td><td><StatusPill status={row.status} /></td></tr>
                            ))}</tbody>
                          </>
                        ) : operationalReportType === "defaulters" ? (
                          <>
                            <thead><tr><th>Flat</th><th>Building</th><th>Invoices</th><th>Overdue</th><th>Oldest Due</th><th>Days</th></tr></thead>
                            <tbody>{(operationalReport as DefaulterReport).rows.map((row) => (
                              <tr key={row.flat_id}><td>{row.flat_number}</td><td>{row.building_name}</td><td>{row.invoice_count}</td><td>{row.overdue_amount}</td><td>{row.oldest_due_date ?? ""}</td><td>{row.days_overdue}</td></tr>
                            ))}</tbody>
                          </>
                        ) : (
                          <>
                            <thead><tr><th>Flat</th><th>Building</th><th>Invoices</th><th>Outstanding</th><th>Overdue</th><th>Oldest Due</th></tr></thead>
                            <tbody>{(operationalReport as OutstandingSummary).rows.map((row) => (
                              <tr key={row.flat_id}><td>{row.flat_number}</td><td>{row.building_name}</td><td>{row.invoice_count}</td><td>{row.total_outstanding}</td><td>{row.overdue_amount}</td><td>{row.oldest_due_date ?? ""}</td></tr>
                            ))}</tbody>
                          </>
                        )}
                      </table>
                    </div>
                  </>
                ) : (
                  <div className="empty-state-panel">
                    <h2>Load report</h2>
                    <p>Select a report and period to view society operations.</p>
                  </div>
                )}
              </section>
            </section>
          ) : workspace === "outstanding" ? (
            <section className="workspace registry-only">
              <section className="data-panel">
                <div className="section-heading">
                  <h2>Outstanding Summary</h2>
                  <span className="record-count">
                    {isLoadingOutstanding ? "Loading" : `${outstandingSummary?.rows.length ?? 0} flats`}
                  </span>
                </div>
                <div className="form-grid two-column">
                  <label>
                    As Of Date
                    <input
                      type="date"
                      value={outstandingAsOfDate}
                      onChange={(event) => setOutstandingAsOfDate(event.target.value)}
                    />
                  </label>
                  <button
                    type="button"
                    className="secondary"
                    disabled={!selectedTenantId || !selectedSocietyId || isLoadingOutstanding}
                    onClick={() => void refreshOutstanding(selectedTenantId, selectedSocietyId)}
                  >
                    Load Outstanding
                  </button>
                </div>
                {outstandingSummary ? (
                  <>
                    <section className="metrics-grid compact-metrics">
                      <article className="metric-tile">
                        <span>Total Outstanding</span>
                        <strong>{outstandingSummary.total_outstanding}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Overdue Amount</span>
                        <strong>{outstandingSummary.overdue_amount}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Flats With Dues</span>
                        <strong>{outstandingSummary.flats_with_outstanding}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Open Invoices</span>
                        <strong>{outstandingSummary.invoice_count}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>Current</span>
                        <strong>{outstandingSummary.ageing.current}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>1-30 Days</span>
                        <strong>{outstandingSummary.ageing.days_1_30}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>31-60 Days</span>
                        <strong>{outstandingSummary.ageing.days_31_60}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>61-90 Days</span>
                        <strong>{outstandingSummary.ageing.days_61_90}</strong>
                      </article>
                      <article className="metric-tile">
                        <span>90+ Days</span>
                        <strong>{outstandingSummary.ageing.days_90_plus}</strong>
                      </article>
                    </section>
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Flat</th>
                            <th>Building</th>
                            <th>Wing</th>
                            <th>Invoices</th>
                            <th>Total</th>
                            <th>Overdue</th>
                            <th>Oldest Due</th>
                            <th>Current</th>
                            <th>1-30</th>
                            <th>31-60</th>
                            <th>61-90</th>
                            <th>90+</th>
                          </tr>
                        </thead>
                        <tbody>
                          {outstandingSummary.rows.map((row) => (
                            <tr key={row.flat_id}>
                              <td>{row.flat_number}</td>
                              <td>{row.building_name}</td>
                              <td>{row.wing_name ?? "No wing"}</td>
                              <td>{row.invoice_count}</td>
                              <td>{row.total_outstanding}</td>
                              <td>{row.overdue_amount}</td>
                              <td>{row.oldest_due_date ?? "-"}</td>
                              <td>{row.ageing.current}</td>
                              <td>{row.ageing.days_1_30}</td>
                              <td>{row.ageing.days_31_60}</td>
                              <td>{row.ageing.days_61_90}</td>
                              <td>{row.ageing.days_90_plus}</td>
                            </tr>
                          ))}
                          {!outstandingSummary.rows.length && !isLoadingOutstanding ? (
                            <tr>
                              <td colSpan={12} className="empty-cell">
                                No outstanding balances for this society.
                              </td>
                            </tr>
                          ) : null}
                        </tbody>
                      </table>
                    </div>
                  </>
                ) : (
                  <div className="empty-state-panel">
                    <h2>No outstanding summary loaded</h2>
                    <p>Select an as-of date and load outstanding balances.</p>
                  </div>
                )}
              </section>
            </section>
          ) : workspace === "wings" ? (
            <section className={`workspace ${isWingFormOpen ? "" : "registry-only"}`}>
              {isWingFormOpen ? (
              <form className="panel-form" onSubmit={handleWingSubmit}>
                <div className="form-title-row">
                  <h2>{editingWingId ? "Edit Wing" : "Create Wing"}</h2>
                  {editingWingId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingWingId(null);
                        setWingForm(wingFormDefaults);
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Building</span>
                  <strong>{selectedBuilding?.name ?? "Select a building"}</strong>
                </div>

                <label>
                  Wing Name
                  <input
                    required
                    maxLength={255}
                    value={wingForm.name}
                    onChange={(event) => setWingForm({ ...wingForm, name: event.target.value })}
                  />
                </label>
                <label>
                  Wing Code
                  <input
                    maxLength={50}
                    value={wingForm.code}
                    onChange={(event) => setWingForm({ ...wingForm, code: event.target.value })}
                  />
                </label>
                <button
                  type="submit"
                  disabled={isSaving || !selectedTenantId || !selectedSocietyId || !selectedBuildingId}
                >
                  {isSaving ? "Saving" : editingWingId ? "Save Wing" : "Create Wing"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Wing Registry</h2>
                  <span className="record-count">
                    {isLoadingWings ? "Loading" : `${wings.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Code</th>
                        <th>Status</th>
                        <th>Building</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {wings.map((wing) => (
                        <tr key={wing.id}>
                          <td>{wing.name}</td>
                          <td>{wing.code ?? ""}</td>
                          <td><StatusPill status={wing.status} /></td>
                          <td>{selectedBuilding?.name ?? ""}</td>
                          <td>
                            <div className="row-actions">
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => setWorkspace("flats")}
                              >
                                Flats
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => startEditWing(wing)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => void handleWingStatusChange(wing)}
                              >
                                {wing.status === "active" ? "Suspend" : "Activate"}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                      {!wings.length && !isLoadingWings ? (
                        <tr>
                          <td colSpan={5} className="empty-cell">
                            No wings for this building yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : workspace === "flats" ? (
            <section className={`workspace ${isFlatFormOpen && !isFlatImportOpen ? "" : "registry-only"}`}>
              {isFlatFormOpen ? (
              <form className="panel-form" onSubmit={handleFlatSubmit}>
                <div className="form-title-row">
                  <h2>{editingFlatId ? "Edit Flat" : "Create Flat"}</h2>
                  {editingFlatId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingFlatId(null);
                        setFlatForm(flatFormDefaults);
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Building</span>
                  <strong>{selectedBuilding?.name ?? "Select a building"}</strong>
                </div>

                <label>
                  Flat Type
                  <select
                    required={flatTypes.length > 0}
                    value={flatForm.flat_type_id}
                    onChange={(event) =>
                      setFlatForm({
                        ...flatForm,
                        flat_type_id: event.target.value
                      })
                    }
                  >
                    <option value="">Select flat type</option>
                    {flatTypes.map((flatType) => (
                      <option key={flatType.id} value={flatType.id}>
                        {flatType.name}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="form-grid">
                  <label>
                    Floor
                    <select
                      required={buildingFloors.length > 0}
                      value={flatForm.floor_id}
                      onChange={(event) =>
                        setFlatForm({ ...flatForm, floor_id: event.target.value })
                      }
                    >
                      <option value="">Select floor</option>
                      {buildingFloors.map((floor) => (
                        <option key={floor.id} value={floor.id}>
                          {floor.floor_label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Wing
                    <select
                      value={flatForm.wing_id}
                      onChange={(event) => setFlatForm({ ...flatForm, wing_id: event.target.value })}
                    >
                      <option value="">No wing</option>
                      {wings.map((wing) => (
                        <option key={wing.id} value={wing.id}>
                          {wing.name}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <label>
                  Flat Number
                  <input
                    required
                    maxLength={50}
                    value={flatForm.flat_number}
                    onChange={(event) =>
                      setFlatForm({ ...flatForm, flat_number: event.target.value })
                    }
                  />
                </label>
                <button
                  type="submit"
                  disabled={
                    isSaving ||
                    !selectedTenantId ||
                    !selectedSocietyId ||
                    !selectedBuildingId ||
                    !flatForm.flat_number.trim() ||
                    (flatTypes.length > 0 && !flatForm.flat_type_id) ||
                    (buildingFloors.length > 0 && !flatForm.floor_id)
                  }
                >
                  {isSaving ? "Saving" : editingFlatId ? "Save Flat" : "Create Flat"}
                </button>
              </form>
              ) : null}

              {isFlatImportOpen ? (
                <section className="data-panel">
                  <div className="section-heading">
                    <h2>Bulk Flat Import</h2>
                    <div className="row-actions">
                      <button
                        type="button"
                        className="secondary compact"
                        onClick={downloadFlatImportTemplate}
                      >
                        Template
                      </button>
                    </div>
                  </div>
                  <div className="import-panel-body">
                    <div className="form-grid">
                      <label>
                        CSV File
                        <input
                          type="file"
                          accept=".csv,text/csv"
                          onChange={(event) =>
                            void handleFlatImportFileChange(event.target.files?.[0] ?? null)
                          }
                        />
                      </label>
                      <div className="context-card">
                        <span>Selected Building</span>
                        <strong>{selectedBuilding?.name ?? "Select a building"}</strong>
                      </div>
                    </div>
                    <div className="import-summary">
                      <span>{flatImportFileName || "No file selected"}</span>
                      <strong>{flatImportRows.length} parsed rows</strong>
                      {flatImportPreview ? (
                        <>
                          <strong>{flatImportPreview.valid_rows} valid</strong>
                          <strong>{flatImportPreview.invalid_rows} invalid</strong>
                        </>
                      ) : null}
                    </div>
                    <div className="row-actions">
                      <button
                        type="button"
                        className="secondary"
                        onClick={() => void handleFlatImportPreview()}
                        disabled={isSaving || !flatImportRows.length}
                      >
                        Preview
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleFlatImportConfirm()}
                        disabled={
                          isSaving ||
                          !flatImportPreview ||
                          flatImportPreview.invalid_rows > 0 ||
                          flatImportPreview.valid_rows === 0
                        }
                      >
                        Confirm Import
                      </button>
                    </div>
                    {flatImportPreview ? (
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>Row</th>
                              <th>Flat</th>
                              <th>Type</th>
                              <th>Floor</th>
                              <th>Wing</th>
                              <th>Status</th>
                              <th>Errors</th>
                            </tr>
                          </thead>
                          <tbody>
                            {flatImportPreview.rows.map((row) => (
                              <tr key={row.row_number}>
                                <td>{row.row_number}</td>
                                <td>{row.input.flat_number ?? ""}</td>
                                <td>{row.resolved.flat_type?.label ?? row.input.flat_type_code ?? ""}</td>
                                <td>{row.resolved.floor?.label ?? row.input.floor_label ?? ""}</td>
                                <td>{row.resolved.wing?.label ?? row.input.wing_code ?? "No wing"}</td>
                                <td>
                                  <span className={`status-pill ${row.status === "valid" ? "active" : "muted"}`}>
                                    {row.status}
                                  </span>
                                </td>
                                <td>{row.errors.join(" ")}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : null}
                  </div>
                </section>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Flat Registry</h2>
                  <span className="record-count">
                    {isLoadingFlats ? "Loading" : `${flats.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Flat</th>
                        <th>Type</th>
                        <th>Wing</th>
                        <th>Floor</th>
                        <th>Area</th>
                        <th>Parking</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {flats.map((flat) => {
                        const wing = wings.find((item) => item.id === flat.wing_id);
                        const floor = buildingFloors.find((item) => item.id === flat.floor_id);
                        const flatType = flatTypes.find((item) => item.id === flat.flat_type_id);
                        return (
                          <tr key={flat.id}>
                            <td>{flat.flat_number}</td>
                            <td>{flatType?.name ?? "Unassigned"}</td>
                            <td>{wing?.name ?? "No wing"}</td>
                            <td>{floor?.floor_label ?? "Unassigned"}</td>
                            <td>
                              {[flat.carpet_area_sqft, flat.built_up_area_sqft]
                                .filter(Boolean)
                                .join(" / ")}
                            </td>
                            <td>{flat.parking_count}</td>
                            <td><StatusPill status={flat.status} /></td>
                            <td>
                              <div className="row-actions">
                                <button
                                  type="button"
                                  className="secondary compact"
                                  onClick={() => {
                                    selectFlat(flat.id);
                                    setWorkspace("ownerships");
                                  }}
                                >
                                  Ownerships
                                </button>
                                <button
                                  type="button"
                                  className="secondary compact"
                                  onClick={() => {
                                    selectFlat(flat.id);
                                    setWorkspace("residents");
                                  }}
                                >
                                  Residents
                                </button>
                                <button
                                  type="button"
                                  className="secondary compact"
                                  onClick={() => startEditFlat(flat)}
                                >
                                  Edit
                                </button>
                                <button
                                  type="button"
                                  className="secondary compact"
                                  onClick={() => void handleFlatStatusChange(flat)}
                                >
                                  {flat.status === "active" ? "Inactivate" : "Activate"}
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                      {!flats.length && !isLoadingFlats ? (
                        <tr>
                          <td colSpan={8} className="empty-cell">
                            No flats for this building yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : workspace === "ownerships" ? (
            <section className={`workspace ${isOwnershipFormOpen ? "" : "registry-only"}`}>
              {isOwnershipFormOpen ? (
              <form className="panel-form" onSubmit={handleOwnershipSubmit}>
                <div className="form-title-row">
                  <h2>{editingOwnershipId ? "Edit Ownership" : "Assign Owner"}</h2>
                  {editingOwnershipId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingOwnershipId(null);
                        setOwnershipForm({ ...ownershipFormDefaults, effective_from: todayIsoDate() });
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Flat</span>
                  <strong>{selectedFlat?.flat_number ?? "Select a flat"}</strong>
                </div>

                <label>
                  Owner
                  <select
                    required
                    value={ownershipForm.owner_id}
                    onChange={(event) =>
                      setOwnershipForm({ ...ownershipForm, owner_id: event.target.value })
                    }
                  >
                    <option value="">Select owner</option>
                    {owners.map((owner) => (
                      <option key={owner.id} value={owner.id}>
                        {owner.full_name}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="form-grid">
                  <label>
                    Type
                    <select
                      required
                      value={ownershipForm.ownership_type}
                      onChange={(event) =>
                        setOwnershipForm({
                          ...ownershipForm,
                          ownership_type: event.target.value,
                          ownership_percentage:
                            event.target.value === "primary_owner"
                              ? "100"
                              : ownershipForm.ownership_percentage
                        })
                      }
                    >
                      {ownershipTypes.map((ownershipType) => (
                        <option key={ownershipType} value={ownershipType}>
                          {ownershipType}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Ownership %
                    <input
                      type="number"
                      min="0.01"
                      max="100"
                      step="0.01"
                      value={ownershipForm.ownership_percentage}
                      onChange={(event) =>
                        setOwnershipForm({ ...ownershipForm, ownership_percentage: event.target.value })
                      }
                    />
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Effective From
                    <input
                      required
                      type="date"
                      value={ownershipForm.effective_from || todayIsoDate()}
                      onChange={(event) =>
                        setOwnershipForm({ ...ownershipForm, effective_from: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Effective To
                    <input
                      type="date"
                      value={ownershipForm.effective_to}
                      onChange={(event) =>
                        setOwnershipForm({ ...ownershipForm, effective_to: event.target.value })
                      }
                    />
                  </label>
                </div>
                <button
                  type="submit"
                  disabled={
                    isSaving ||
                    !selectedTenantId ||
                    !selectedSocietyId ||
                    !selectedBuildingId ||
                    !selectedFlatId ||
                    !owners.length
                  }
                >
                  {isSaving ? "Saving" : editingOwnershipId ? "Save Ownership" : "Assign Owner"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Ownership Registry</h2>
                  <span className="record-count">
                    {isLoadingOwnerships ? "Loading" : `${ownerships.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Owner</th>
                        <th>Type</th>
                        <th>Share</th>
                        <th>Effective</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ownerships.map((ownership) => {
                        const owner = owners.find((item) => item.id === ownership.owner_id);
                        return (
                          <tr key={ownership.id}>
                            <td>{owner?.full_name ?? "Unknown owner"}</td>
                            <td>{ownership.ownership_type}</td>
                            <td>{ownership.ownership_percentage ?? ""}</td>
                            <td>
                              {[ownership.effective_from, ownership.effective_to]
                                .filter(Boolean)
                                .join(" to ")}
                            </td>
                            <td><StatusPill status={ownership.status} /></td>
                            <td>
                              <div className="row-actions">
                                <button
                                  type="button"
                                  className="secondary compact"
                                  onClick={() => startEditOwnership(ownership)}
                                >
                                  Edit
                                </button>
                                <button
                                  type="button"
                                  className="secondary compact"
                                  onClick={() => void handleOwnershipStatusChange(ownership)}
                                >
                                  {ownership.status === "active" ? "Close Today" : "Activate"}
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                      {!ownerships.length && !isLoadingOwnerships ? (
                        <tr>
                          <td colSpan={6} className="empty-cell">
                            No ownership assignments for this flat yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : workspace === "residents" ? (
            <section className={`workspace ${isResidentFormOpen ? "" : "registry-only"}`}>
              {isResidentFormOpen ? (
              <form className="panel-form" onSubmit={handleResidentSubmit}>
                <div className="form-title-row">
                  <h2>{editingResidentId ? "Edit Resident" : "Create Resident"}</h2>
                  {editingResidentId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingResidentId(null);
                        setResidentForm({ ...residentFormDefaults, move_in_date: todayIsoDate() });
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Flat</span>
                  <strong>{selectedFlat?.flat_number ?? "Select a flat"}</strong>
                </div>

                <label>
                  Linked Owner
                  <select
                    value={residentForm.owner_id}
                    onChange={(event) =>
                      setResidentForm({ ...residentForm, owner_id: event.target.value })
                    }
                  >
                    <option value="">No owner link</option>
                    {owners.map((owner) => (
                      <option key={owner.id} value={owner.id}>
                        {owner.full_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Resident Type
                  <select
                    required
                    value={residentForm.resident_type}
                    onChange={(event) =>
                      setResidentForm({ ...residentForm, resident_type: event.target.value })
                    }
                  >
                    {residentTypes.map((residentType) => (
                      <option key={residentType} value={residentType}>
                        {residentType}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Full Name
                  <input
                    required
                    maxLength={255}
                    value={residentForm.full_name}
                    onChange={(event) =>
                      setResidentForm({ ...residentForm, full_name: event.target.value })
                    }
                  />
                </label>
                <div className="form-grid">
                  <label>
                    Email
                    <input
                      type="email"
                      value={residentForm.email}
                      onChange={(event) =>
                        setResidentForm({ ...residentForm, email: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Mobile
                    <input
                      maxLength={20}
                      value={residentForm.mobile_number}
                      onChange={(event) =>
                        setResidentForm({ ...residentForm, mobile_number: event.target.value })
                      }
                    />
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Move In
                    <input
                      required
                      type="date"
                      value={residentForm.move_in_date || todayIsoDate()}
                      onChange={(event) =>
                        setResidentForm({ ...residentForm, move_in_date: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Move Out
                    <input
                      type="date"
                      value={residentForm.move_out_date}
                      onChange={(event) =>
                        setResidentForm({ ...residentForm, move_out_date: event.target.value })
                      }
                    />
                  </label>
                </div>
                <button
                  type="submit"
                  disabled={isSaving || !selectedTenantId || !selectedSocietyId || !selectedBuildingId || !selectedFlatId}
                >
                  {isSaving ? "Saving" : editingResidentId ? "Save Resident" : "Create Resident"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Resident Registry</h2>
                  <span className="record-count">
                    {isLoadingResidents ? "Loading" : `${residents.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Owner</th>
                        <th>Contact</th>
                        <th>Move Dates</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {residents.map((resident) => {
                        const owner = owners.find((item) => item.id === resident.owner_id);
                        return (
                          <tr key={resident.id}>
                            <td>{resident.full_name}</td>
                            <td>{resident.resident_type}</td>
                            <td>{owner?.full_name ?? ""}</td>
                            <td>{[resident.email, resident.mobile_number].filter(Boolean).join(" / ")}</td>
                            <td>
                              {[resident.move_in_date, resident.move_out_date]
                                .filter(Boolean)
                                .join(" to ")}
                            </td>
                            <td><StatusPill status={resident.status} /></td>
                            <td>
                              <div className="row-actions">
                                <button
                                  type="button"
                                  className="secondary compact"
                                  onClick={() => startEditResident(resident)}
                                >
                                  Edit
                                </button>
                                <button
                                  type="button"
                                  className="secondary compact"
                                  onClick={() => void handleResidentStatusChange(resident)}
                                >
                                  {resident.status === "active" ? "Move Out" : "Activate"}
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                      {!residents.length && !isLoadingResidents ? (
                        <tr>
                          <td colSpan={7} className="empty-cell">
                            No residents for this flat yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : workspace === "leaseAgreements" ? (
            <section className={`workspace ${isLeaseAgreementFormOpen ? "" : "registry-only"}`}>
              {isLeaseAgreementFormOpen ? (
              <form className="panel-form" onSubmit={handleLeaseAgreementSubmit}>
                <div className="form-title-row">
                  <h2>{editingLeaseAgreementId ? "Edit Lease" : "Create Lease"}</h2>
                  {editingLeaseAgreementId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingLeaseAgreementId(null);
                        setLeaseAgreementForm(leaseAgreementFormDefaults);
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Flat</span>
                  <strong>{selectedFlat?.flat_number ?? "Select a flat"}</strong>
                </div>

                <label>
                  Legal Owner
                  <select
                    required
                    value={leaseAgreementForm.owner_id}
                    onChange={(event) =>
                      setLeaseAgreementForm({ ...leaseAgreementForm, owner_id: event.target.value })
                    }
                  >
                    <option value="">Select owner</option>
                    {owners.map((owner) => (
                      <option key={owner.id} value={owner.id}>
                        {owner.full_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Linked Resident
                  <select
                    value={leaseAgreementForm.resident_id}
                    onChange={(event) => {
                      const resident = residents.find((item) => item.id === event.target.value);
                      setLeaseAgreementForm({
                        ...leaseAgreementForm,
                        resident_id: event.target.value,
                        tenant_name: resident?.full_name ?? leaseAgreementForm.tenant_name,
                        tenant_email: resident?.email ?? leaseAgreementForm.tenant_email,
                        tenant_mobile_number:
                          resident?.mobile_number ?? leaseAgreementForm.tenant_mobile_number
                      });
                    }}
                  >
                    <option value="">No resident link</option>
                    {residents.map((resident) => (
                      <option key={resident.id} value={resident.id}>
                        {resident.full_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Tenant Name
                  <input
                    required
                    maxLength={255}
                    value={leaseAgreementForm.tenant_name}
                    onChange={(event) =>
                      setLeaseAgreementForm({ ...leaseAgreementForm, tenant_name: event.target.value })
                    }
                  />
                </label>
                <div className="form-grid">
                  <label>
                    Tenant Email
                    <input
                      type="email"
                      value={leaseAgreementForm.tenant_email}
                      onChange={(event) =>
                        setLeaseAgreementForm({ ...leaseAgreementForm, tenant_email: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Tenant Mobile
                    <input
                      maxLength={20}
                      value={leaseAgreementForm.tenant_mobile_number}
                      onChange={(event) =>
                        setLeaseAgreementForm({
                          ...leaseAgreementForm,
                          tenant_mobile_number: event.target.value
                        })
                      }
                    />
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Agreement Start
                    <input
                      required
                      type="date"
                      value={leaseAgreementForm.agreement_start_date || todayIsoDate()}
                      onChange={(event) =>
                        setLeaseAgreementForm({
                          ...leaseAgreementForm,
                          agreement_start_date: event.target.value
                        })
                      }
                    />
                  </label>
                  <label>
                    Agreement End
                    <input
                      required
                      type="date"
                      value={leaseAgreementForm.agreement_end_date || todayIsoDate()}
                      onChange={(event) =>
                        setLeaseAgreementForm({
                          ...leaseAgreementForm,
                          agreement_end_date: event.target.value
                        })
                      }
                    />
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Move In
                    <input
                      required
                      type="date"
                      value={leaseAgreementForm.move_in_date || todayIsoDate()}
                      onChange={(event) =>
                        setLeaseAgreementForm({ ...leaseAgreementForm, move_in_date: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Move Out
                    <input
                      type="date"
                      value={leaseAgreementForm.move_out_date}
                      onChange={(event) =>
                        setLeaseAgreementForm({ ...leaseAgreementForm, move_out_date: event.target.value })
                      }
                    />
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Monthly Rent
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={leaseAgreementForm.monthly_rent}
                      onChange={(event) =>
                        setLeaseAgreementForm({ ...leaseAgreementForm, monthly_rent: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Security Deposit
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={leaseAgreementForm.security_deposit}
                      onChange={(event) =>
                        setLeaseAgreementForm({ ...leaseAgreementForm, security_deposit: event.target.value })
                      }
                    />
                  </label>
                </div>
                <label>
                  Police Verification
                  <select
                    required
                    value={leaseAgreementForm.police_verification_status}
                    onChange={(event) =>
                      setLeaseAgreementForm({
                        ...leaseAgreementForm,
                        police_verification_status: event.target.value
                      })
                    }
                  >
                    {policeVerificationStatuses.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Document Reference
                  <input
                    maxLength={255}
                    value={leaseAgreementForm.document_reference}
                    onChange={(event) =>
                      setLeaseAgreementForm({
                        ...leaseAgreementForm,
                        document_reference: event.target.value
                      })
                    }
                  />
                </label>
                <label>
                  Notes
                  <textarea
                    value={leaseAgreementForm.notes}
                    onChange={(event) =>
                      setLeaseAgreementForm({ ...leaseAgreementForm, notes: event.target.value })
                    }
                  />
                </label>
                <button
                  type="submit"
                  disabled={
                    isSaving ||
                    !selectedTenantId ||
                    !selectedSocietyId ||
                    !selectedBuildingId ||
                    !selectedFlatId ||
                    !leaseAgreementForm.owner_id ||
                    !leaseAgreementForm.tenant_name.trim() ||
                    !leaseAgreementForm.agreement_start_date ||
                    !leaseAgreementForm.agreement_end_date ||
                    !leaseAgreementForm.move_in_date
                  }
                >
                  {isSaving ? "Saving" : editingLeaseAgreementId ? "Save Lease" : "Create Lease"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Lease Registry</h2>
                  <span className="record-count">
                    {isLoadingLeaseAgreements ? "Loading" : `${leaseAgreements.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Tenant</th>
                        <th>Contact</th>
                        <th>Owner</th>
                        <th>Agreement</th>
                        <th>Move Dates</th>
                        <th>Rent</th>
                        <th>Police</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {leaseAgreements.map((leaseAgreement) => {
                        const owner = owners.find((item) => item.id === leaseAgreement.owner_id);
                        return (
                          <tr key={leaseAgreement.id}>
                            <td>{leaseAgreement.tenant_name}</td>
                            <td>
                              {[leaseAgreement.tenant_email, leaseAgreement.tenant_mobile_number]
                                .filter(Boolean)
                                .join(" / ")}
                            </td>
                            <td>{owner?.full_name ?? "Unknown owner"}</td>
                            <td>
                              {leaseAgreement.agreement_start_date} to {leaseAgreement.agreement_end_date}
                            </td>
                            <td>
                              {[leaseAgreement.move_in_date, leaseAgreement.move_out_date]
                                .filter(Boolean)
                                .join(" to ")}
                            </td>
                            <td>{leaseAgreement.monthly_rent ?? ""}</td>
                            <td><StatusPill status={leaseAgreement.police_verification_status} /></td>
                            <td><StatusPill status={leaseAgreement.status} /></td>
                            <td>
                              <div className="row-actions">
                                <button
                                  type="button"
                                  className="secondary compact"
                                  onClick={() => startEditLeaseAgreement(leaseAgreement)}
                                >
                                  Edit
                                </button>
                                {leaseAgreement.status === "active" ? (
                                  <button
                                    type="button"
                                    className="secondary compact"
                                    onClick={() => handleLeaseAgreementTerminate(leaseAgreement)}
                                  >
                                    Terminate
                                  </button>
                                ) : null}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                      {!leaseAgreements.length && !isLoadingLeaseAgreements ? (
                        <tr>
                          <td colSpan={9} className="empty-cell">
                            No lease agreements for this flat yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : workspace === "vendors" ? (
            <section className={`workspace ${isVendorFormOpen ? "" : "registry-only"}`}>
              {isVendorFormOpen ? (
              <form className="panel-form" onSubmit={handleVendorSubmit}>
                <div className="form-title-row">
                  <h2>{editingVendorId ? "Edit Vendor" : "Create Vendor"}</h2>
                  {editingVendorId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingVendorId(null);
                        setVendorForm(vendorFormDefaults);
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Society</span>
                  <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                </div>

                <div className="form-grid">
                  <label>
                    Vendor Code
                    <input
                      required
                      maxLength={50}
                      value={vendorForm.vendor_code}
                      onChange={(event) =>
                        setVendorForm({ ...vendorForm, vendor_code: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Vendor Type
                    <select
                      required
                      value={vendorForm.vendor_type}
                      onChange={(event) =>
                        setVendorForm({ ...vendorForm, vendor_type: event.target.value })
                      }
                    >
                      {vendorTypes.map((vendorType) => (
                        <option key={vendorType} value={vendorType}>
                          {vendorType}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <label>
                  Vendor Name
                  <input
                    required
                    maxLength={255}
                    value={vendorForm.vendor_name}
                    onChange={(event) =>
                      setVendorForm({ ...vendorForm, vendor_name: event.target.value })
                    }
                  />
                </label>
                <label>
                  Contact Person
                  <input
                    maxLength={255}
                    value={vendorForm.contact_person}
                    onChange={(event) =>
                      setVendorForm({ ...vendorForm, contact_person: event.target.value })
                    }
                  />
                </label>
                <div className="form-grid">
                  <label>
                    Email
                    <input
                      type="email"
                      value={vendorForm.email}
                      onChange={(event) =>
                        setVendorForm({ ...vendorForm, email: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Mobile
                    <input
                      maxLength={20}
                      value={vendorForm.mobile_number}
                      onChange={(event) =>
                        setVendorForm({ ...vendorForm, mobile_number: event.target.value })
                      }
                    />
                  </label>
                </div>
                <label>
                  Tax Identifier
                  <input
                    maxLength={50}
                    value={vendorForm.tax_identifier}
                    onChange={(event) =>
                      setVendorForm({ ...vendorForm, tax_identifier: event.target.value })
                    }
                  />
                </label>
                <label>
                  Billing Address
                  <textarea
                    value={vendorForm.billing_address}
                    onChange={(event) =>
                      setVendorForm({ ...vendorForm, billing_address: event.target.value })
                    }
                  />
                </label>
                <button
                  type="submit"
                  disabled={
                    isSaving ||
                    !selectedTenantId ||
                    !selectedSocietyId ||
                    !vendorForm.vendor_code.trim() ||
                    !vendorForm.vendor_name.trim()
                  }
                >
                  {isSaving ? "Saving" : editingVendorId ? "Save Vendor" : "Create Vendor"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Vendor Registry</h2>
                  <span className="record-count">
                    {isLoadingVendors ? "Loading" : `${vendors.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Contact</th>
                        <th>Tax ID</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {vendors.map((vendor) => (
                        <tr key={vendor.id}>
                          <td>{vendor.vendor_code}</td>
                          <td>{vendor.vendor_name}</td>
                          <td>{vendor.vendor_type}</td>
                          <td>
                            {[vendor.contact_person, vendor.email, vendor.mobile_number]
                              .filter(Boolean)
                              .join(" / ")}
                          </td>
                          <td>{vendor.tax_identifier ?? ""}</td>
                          <td><StatusPill status={vendor.status} /></td>
                          <td>
                            <div className="row-actions">
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => startEditVendor(vendor)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => void handleVendorStatusChange(vendor)}
                              >
                                {vendor.status === "active" ? "Inactivate" : "Activate"}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                      {!vendors.length && !isLoadingVendors ? (
                        <tr>
                          <td colSpan={7} className="empty-cell">
                            No vendors for this society yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : workspace === "expenses" ? (
            <section className={`workspace ${isExpenseFormOpen ? "" : "registry-only"}`}>
              {isExpenseFormOpen ? (
              <form className="panel-form" onSubmit={handleExpenseSubmit}>
                <div className="form-title-row">
                  <h2>{editingExpenseId ? "Edit Expense" : "Record Expense"}</h2>
                  {editingExpenseId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingExpenseId(null);
                        setExpenseForm({
                          ...expenseFormDefaults,
                          expense_date: todayIsoDate(),
                          due_date: todayIsoDate()
                        });
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Society</span>
                  <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                </div>

                <label>
                  Expense Type
                  <select
                    required
                    value={expenseForm.expense_type}
                    onChange={(event) =>
                      setExpenseForm({
                        ...expenseForm,
                        expense_type: event.target.value,
                        vendor_id: event.target.value === "vendor_bill" ? expenseForm.vendor_id : ""
                      })
                    }
                  >
                    <option value="vendor_bill">vendor_bill</option>
                    <option value="cash_expense">cash_expense</option>
                    <option value="other">other</option>
                  </select>
                </label>
                <label>
                  Vendor
                  <select
                    required={expenseForm.expense_type === "vendor_bill"}
                    value={expenseForm.vendor_id}
                    onChange={(event) => setExpenseForm({ ...expenseForm, vendor_id: event.target.value })}
                  >
                    <option value="">No vendor</option>
                    {vendors
                      .filter((vendor) => vendor.status === "active")
                      .map((vendor) => (
                        <option key={vendor.id} value={vendor.id}>
                          {vendor.vendor_code} - {vendor.vendor_name}
                        </option>
                      ))}
                  </select>
                </label>
                <label>
                  Expense Category
                  <select
                    required
                    value={expenseForm.expense_category_id}
                    onChange={(event) =>
                      setExpenseForm({ ...expenseForm, expense_category_id: event.target.value })
                    }
                  >
                    <option value="">Select category</option>
                    {expenseCategories
                      .filter((category) => category.status === "active")
                      .map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.code ? `${category.code} - ` : ""}{category.name}
                        </option>
                      ))}
                  </select>
                </label>
                <label>
                  Paid From Account
                  <select
                    value={expenseForm.payment_account_id}
                    onChange={(event) =>
                      setExpenseForm({ ...expenseForm, payment_account_id: event.target.value })
                    }
                  >
                    <option value="">Not paid yet</option>
                    {activeAssetAccounts.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.account_code} - {account.account_name}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="form-grid">
                  <label>
                    Bill Number
                    <input
                      maxLength={100}
                      value={expenseForm.vendor_bill_number}
                      onChange={(event) =>
                        setExpenseForm({ ...expenseForm, vendor_bill_number: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Reference
                    <input
                      maxLength={100}
                      value={expenseForm.reference_number}
                      onChange={(event) =>
                        setExpenseForm({ ...expenseForm, reference_number: event.target.value })
                      }
                    />
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Expense Date
                    <input
                      required
                      type="date"
                      value={expenseForm.expense_date}
                      onChange={(event) =>
                        setExpenseForm({ ...expenseForm, expense_date: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Due Date
                    <input
                      required
                      type="date"
                      value={expenseForm.due_date}
                      onChange={(event) =>
                        setExpenseForm({ ...expenseForm, due_date: event.target.value })
                      }
                    />
                  </label>
                </div>
                <label>
                  Description
                  <input
                    required
                    maxLength={255}
                    value={expenseForm.description}
                    onChange={(event) =>
                      setExpenseForm({ ...expenseForm, description: event.target.value })
                    }
                  />
                </label>
                <div className="form-grid">
                  <label>
                    Amount
                    <input
                      required
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={expenseForm.amount}
                      onChange={(event) =>
                        setExpenseForm({ ...expenseForm, amount: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Tax Amount
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={expenseForm.tax_amount}
                      onChange={(event) =>
                        setExpenseForm({ ...expenseForm, tax_amount: event.target.value })
                      }
                    />
                  </label>
                </div>
                <label>
                  Notes
                  <textarea
                    value={expenseForm.notes}
                    onChange={(event) => setExpenseForm({ ...expenseForm, notes: event.target.value })}
                  />
                </label>
                <button
                  type="submit"
                  disabled={
                    isSaving ||
                    !selectedTenantId ||
                    !selectedSocietyId ||
                    !expenseForm.expense_category_id ||
                    !expenseForm.description.trim() ||
                    !expenseForm.amount ||
                    (expenseForm.expense_type === "vendor_bill" && !expenseForm.vendor_id)
                  }
                >
                  {isSaving ? "Saving" : editingExpenseId ? "Save Expense" : "Record Expense"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Expense Registry</h2>
                  <span className="record-count">
                    {isLoadingExpenses ? "Loading" : `${expenses.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Vendor</th>
                        <th>Category</th>
                        <th>Description</th>
                        <th>Total</th>
                        <th>Due</th>
                        <th>Status</th>
                        <th>Payment</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {expenses.map((expense) => {
                        const vendor = vendors.find((item) => item.id === expense.vendor_id);
                        const category = expenseCategories.find(
                          (item) => item.id === expense.expense_category_id
                        );
                        return (
                          <tr key={expense.id}>
                            <td>{expense.expense_date}</td>
                            <td>{vendor?.vendor_name ?? ""}</td>
                            <td>{category?.name ?? ""}</td>
                            <td>{expense.description}</td>
                            <td>{expense.total_amount}</td>
                            <td>{expense.amount_due}</td>
                            <td><StatusPill status={expense.status} /></td>
                            <td><StatusPill status={expense.payment_status} /></td>
                            <td>
                              <div className="row-actions">
                                <button
                                  type="button"
                                  className="secondary compact"
                                  disabled={expense.status === "cancelled" || Number(expense.amount_paid) > 0}
                                  onClick={() => startEditExpense(expense)}
                                >
                                  Edit
                                </button>
                                <button
                                  type="button"
                                  className="secondary compact"
                                  disabled={expense.status !== "recorded"}
                                  onClick={() => void handleExpenseApprove(expense)}
                                >
                                  Approve
                                </button>
                                <button
                                  type="button"
                                  className="secondary compact"
                                  disabled={expense.status === "cancelled" || Number(expense.amount_paid) > 0}
                                  onClick={() => void handleExpenseCancel(expense)}
                                >
                                  Cancel
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                      {!expenses.length && !isLoadingExpenses ? (
                        <tr>
                          <td colSpan={9} className="empty-cell">
                            No expenses recorded for this society yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
              <form className="panel-form" onSubmit={handleExpensePaymentSubmit}>
                <h2>Record Expense Payment</h2>
                <label>
                  Vendor
                  <select
                    value={expensePaymentForm.vendor_id}
                    onChange={(event) => {
                      setExpensePaymentForm({ ...expensePaymentForm, vendor_id: event.target.value });
                      setExpensePaymentAllocations({});
                    }}
                  >
                    <option value="">Any vendor / no vendor</option>
                    {vendors
                      .filter((vendor) => vendor.status === "active")
                      .map((vendor) => (
                        <option key={vendor.id} value={vendor.id}>
                          {vendor.vendor_code} - {vendor.vendor_name}
                        </option>
                      ))}
                  </select>
                </label>
                <label>
                  Payment Account
                  <select
                    required
                    value={expensePaymentForm.payment_account_id}
                    onChange={(event) =>
                      setExpensePaymentForm({ ...expensePaymentForm, payment_account_id: event.target.value })
                    }
                  >
                    <option value="">Select asset account</option>
                    {activeAssetAccounts.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.account_code} - {account.account_name}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="form-grid">
                  <label>
                    Payment Date
                    <input
                      required
                      type="date"
                      value={expensePaymentForm.payment_date}
                      onChange={(event) =>
                        setExpensePaymentForm({ ...expensePaymentForm, payment_date: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Amount
                    <input
                      required
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={expensePaymentForm.amount}
                      onChange={(event) =>
                        setExpensePaymentForm({ ...expensePaymentForm, amount: event.target.value })
                      }
                    />
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Mode
                    <select
                      value={expensePaymentForm.payment_mode}
                      onChange={(event) =>
                        setExpensePaymentForm({ ...expensePaymentForm, payment_mode: event.target.value })
                      }
                    >
                      {paymentModes.map((mode) => (
                        <option key={mode} value={mode}>
                          {mode}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Reference
                    <input
                      value={expensePaymentForm.reference_number}
                      onChange={(event) =>
                        setExpensePaymentForm({ ...expensePaymentForm, reference_number: event.target.value })
                      }
                    />
                  </label>
                </div>
                <div className="context-card">
                  <span>Allocated / Unapplied</span>
                  <strong>
                    {expensePaymentAllocatedTotal.toFixed(2)} /{" "}
                    {Math.max((Number(expensePaymentForm.amount) || 0) - expensePaymentAllocatedTotal, 0).toFixed(2)}
                  </strong>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Vendor</th>
                        <th>Description</th>
                        <th>Due</th>
                        <th>Allocate</th>
                      </tr>
                    </thead>
                    <tbody>
                      {expensePaymentOpenExpenses.map((expense) => {
                        const vendor = vendors.find((item) => item.id === expense.vendor_id);
                        return (
                          <tr key={expense.id}>
                            <td>{expense.expense_date}</td>
                            <td>{vendor?.vendor_name ?? ""}</td>
                            <td>{expense.description}</td>
                            <td>{expense.amount_due}</td>
                            <td>
                              <input
                                type="number"
                                min="0"
                                max={expense.amount_due}
                                step="0.01"
                                value={expensePaymentAllocations[expense.id] ?? ""}
                                onChange={(event) =>
                                  setExpensePaymentAllocations((current) => ({
                                    ...current,
                                    [expense.id]: event.target.value
                                  }))
                                }
                              />
                            </td>
                          </tr>
                        );
                      })}
                      {!expensePaymentOpenExpenses.length ? (
                        <tr>
                          <td colSpan={5} className="empty-cell">
                            No open expenses available for payment.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
                <button
                  type="submit"
                  disabled={
                    isSaving ||
                    !expensePaymentForm.payment_account_id ||
                    !expensePaymentForm.amount ||
                    expensePaymentAllocatedTotal > Number(expensePaymentForm.amount)
                  }
                >
                  {isSaving ? "Saving" : "Record Expense Payment"}
                </button>
              </form>
              <section className="data-panel">
                <div className="section-heading">
                  <h2>Expense Payment Registry</h2>
                  <span className="record-count">
                    {isLoadingExpensePayments ? "Loading" : `${expensePayments.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Vendor</th>
                        <th>Amount</th>
                        <th>Unapplied</th>
                        <th>Mode</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {expensePayments.map((payment) => {
                        const vendor = vendors.find((item) => item.id === payment.vendor_id);
                        return (
                          <tr key={payment.id}>
                            <td>{payment.payment_date}</td>
                            <td>{vendor?.vendor_name ?? ""}</td>
                            <td>{payment.amount}</td>
                            <td>{payment.unapplied_amount}</td>
                            <td>{payment.payment_mode}</td>
                            <td><StatusPill status={payment.status} /></td>
                          </tr>
                        );
                      })}
                      {!expensePayments.length && !isLoadingExpensePayments ? (
                        <tr>
                          <td colSpan={6} className="empty-cell">
                            No expense payments recorded yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          ) : (
            <section className={`workspace ${isOwnerFormOpen ? "" : "registry-only"}`}>
              {isOwnerFormOpen ? (
              <form className="panel-form" onSubmit={handleOwnerSubmit}>
                <div className="form-title-row">
                  <h2>{editingOwnerId ? "Edit Owner" : "Create Owner"}</h2>
                  {editingOwnerId ? (
                    <button
                      type="button"
                      className="secondary compact"
                      onClick={() => {
                        setEditingOwnerId(null);
                        setOwnerForm(ownerFormDefaults);
                        setFormWorkspace(null);
                      }}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>

                <div className="context-card">
                  <span>Selected Society</span>
                  <strong>{selectedSociety?.name ?? "Select a society"}</strong>
                </div>

                <label>
                  Owner Type
                  <select
                    required
                    value={ownerForm.owner_type}
                    onChange={(event) =>
                      setOwnerForm({ ...ownerForm, owner_type: event.target.value })
                    }
                  >
                    {ownerTypes.map((ownerType) => (
                      <option key={ownerType} value={ownerType}>
                        {ownerType}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Full Name
                  <input
                    required
                    maxLength={255}
                    value={ownerForm.full_name}
                    onChange={(event) =>
                      setOwnerForm({ ...ownerForm, full_name: event.target.value })
                    }
                  />
                </label>
                <div className="form-grid">
                  <label>
                    Email
                    <input
                      type="email"
                      value={ownerForm.email}
                      onChange={(event) =>
                        setOwnerForm({ ...ownerForm, email: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Mobile
                    <input
                      maxLength={20}
                      value={ownerForm.mobile_number}
                      onChange={(event) =>
                        setOwnerForm({ ...ownerForm, mobile_number: event.target.value })
                      }
                    />
                  </label>
                </div>
                <label>
                  Tax Identifier
                  <input
                    maxLength={50}
                    value={ownerForm.tax_identifier}
                    onChange={(event) =>
                      setOwnerForm({ ...ownerForm, tax_identifier: event.target.value })
                    }
                  />
                </label>
                <label>
                  Billing Address
                  <textarea
                    value={ownerForm.billing_address}
                    onChange={(event) =>
                      setOwnerForm({ ...ownerForm, billing_address: event.target.value })
                    }
                  />
                </label>
                <button type="submit" disabled={isSaving || !selectedTenantId || !selectedSocietyId}>
                  {isSaving ? "Saving" : editingOwnerId ? "Save Owner" : "Create Owner"}
                </button>
              </form>
              ) : null}

              <section className="data-panel">
                <div className="section-heading">
                  <h2>Owner Registry</h2>
                  <span className="record-count">
                    {isLoadingOwners ? "Loading" : `${owners.length} records`}
                  </span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Contact</th>
                        <th>Tax ID</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {owners.map((owner) => (
                        <tr key={owner.id}>
                          <td>{owner.full_name}</td>
                          <td>{owner.owner_type}</td>
                          <td>{[owner.email, owner.mobile_number].filter(Boolean).join(" / ")}</td>
                          <td>{owner.tax_identifier ?? ""}</td>
                          <td><StatusPill status={owner.status} /></td>
                          <td>
                            <div className="row-actions">
                              <button
                                type="button"
                                className="secondary compact"
                                disabled={!selectedFlatId}
                                onClick={() => {
                                  setOwnershipForm({
                                    ...ownershipFormDefaults,
                                    owner_id: owner.id,
                                    effective_from: todayIsoDate()
                                  });
                                  setEditingOwnershipId(null);
                                  setWorkspace("ownerships");
                                }}
                              >
                                Assign
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => startEditOwner(owner)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="secondary compact"
                                onClick={() => void handleOwnerStatusChange(owner)}
                              >
                                {owner.status === "active" ? "Inactivate" : "Activate"}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                      {!owners.length && !isLoadingOwners ? (
                        <tr>
                          <td colSpan={6} className="empty-cell">
                            No owners for this society yet.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          )}
        </section>
      </div>
      {reasonDialog ? (
        <div className="modal-backdrop" role="presentation">
          <section
            className="modal-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="reason-dialog-title"
          >
            <form onSubmit={handleReasonDialogSubmit}>
              <div className="modal-header">
                <div>
                  <h2 id="reason-dialog-title">{reasonDialog.title}</h2>
                  <p>{reasonDialog.description}</p>
                </div>
                <button
                  type="button"
                  className="icon-button"
                  onClick={closeReasonDialog}
                  disabled={isSaving}
                  aria-label="Close"
                >
                  X
                </button>
              </div>
              <label className="modal-field">
                {reasonDialog.reasonLabel}
                <textarea
                  required
                  minLength={3}
                  rows={4}
                  value={reasonDialogText}
                  onChange={(event) => setReasonDialogText(event.target.value)}
                  autoFocus
                />
              </label>
              <div className="modal-actions">
                <button type="button" className="secondary" onClick={closeReasonDialog} disabled={isSaving}>
                  Cancel
                </button>
                <button type="submit" disabled={isSaving || reasonDialogText.trim().length < 3}>
                  {isSaving ? "Saving" : reasonDialog.confirmLabel}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : null}
    </main>
  );
}

function StatusPill({ status }: { status: string }) {
  return <span className={`status-pill ${status === "active" ? "active" : "muted"}`}>{status}</span>;
}

export default App;
