from typing import List, Optional, Dict, Any, Literal
from datetime import date, datetime
import re
from pydantic import BaseModel, Field, field_validator, model_validator


def validate_password_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Za-z]", v):
        raise ValueError("Password must contain at least one letter")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one digit")
    return v


def validate_email_format(v: str) -> str:
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, v.strip()):
        raise ValueError("Invalid email format")
    return v.strip().lower()


# ================= USER & AUTH =================
class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str
    password: str = Field(..., min_length=8)
    confirm_password: str
    phone: Optional[str] = None

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @model_validator(mode="after")
    def check_passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class GoogleAuthRequest(BaseModel):
    credential: str


class ResendVerificationRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8)
    confirm_password: str

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @model_validator(mode="after")
    def check_passwords_match(self) -> "ResetPasswordRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str
    password: str = Field(..., min_length=8)
    role: str
    phone: Optional[str] = None
    reporting_manager_id: Optional[int] = None
    permissions: List[str] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    email: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    reporting_manager_id: Optional[int] = None
    permissions: Optional[List[str]] = None

    @field_validator("email")
    @classmethod
    def check_email(cls, v: Optional[str]) -> Optional[str]:
        return validate_email_format(v) if v is not None else None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    is_active: bool
    is_verified: bool = False
    created_at: Optional[datetime] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    reporting_manager_id: Optional[int] = None
    permissions: List[Dict[str, str]] = Field(default_factory=list)
    additional_permissions: List[Dict[str, str]] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ================= CUSTOMER & LEAD =================
class CustomerCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    address: str
    city: Optional[str] = "Hyderabad"
    customer_type: str = "Residential"
    lead_source: str = "Website"
    required_capacity_kw: float = 3.0
    solar_requirement: str = "On-Grid"
    monthly_bill: float = 0.0
    subsidy_required: bool = False
    assigned_user_id: Optional[int] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    customer_type: Optional[str] = None
    status: Optional[str] = None
    monthly_bill: Optional[float] = None
    required_capacity_kw: Optional[float] = None
    assigned_user_id: Optional[int] = None


class CustomerOut(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str] = None
    address: str
    city: Optional[str] = None
    customer_type: str
    lead_source: Optional[str] = None
    required_capacity_kw: Optional[float] = None
    solar_requirement: Optional[str] = None
    monthly_bill: Optional[float] = None
    subsidy_required: Optional[bool] = None
    status: str
    assigned_user_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PublicEnquiryRequest(BaseModel):
    customer_name: str
    phone: str
    email: Optional[str] = None
    address: str
    city: Optional[str] = "Hyderabad"
    customer_category: str = "Residential"
    preferred_contact_method: str = "Phone"
    lead_source: str = "Website"
    required_capacity: float = 3.0
    solar_requirement: str = "On-Grid"
    monthly_electricity_bill: float = 2500.0
    subsidy_requirement: bool = True
    additional_requirements: Optional[str] = None


class LeadCreate(BaseModel):
    customer_name: str
    phone: str
    email: Optional[str] = None
    address: str
    city: Optional[str] = "Hyderabad"
    customer_type: str = "Residential"
    lead_source: str = "Website"
    preferred_contact_method: str = "Phone"
    required_capacity_kw: float = 3.0
    solar_requirement: str = "On-Grid"
    monthly_bill: float = 0.0
    subsidy_required: bool = False
    roof_availability: Optional[str] = None
    grid_suitable: bool = True
    estimated_value: float = 0.0
    assigned_sales_rep: Optional[str] = None
    assigned_user_id: Optional[int] = None
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    required_capacity_kw: Optional[float] = None
    solar_requirement: Optional[str] = None
    monthly_bill: Optional[float] = None
    assigned_sales_rep: Optional[str] = None
    assigned_user_id: Optional[int] = None
    follow_up_date: Optional[date] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    roof_availability: Optional[str] = None
    grid_suitable: Optional[bool] = None
    estimated_value: Optional[float] = None


class LeadQualify(BaseModel):
    shadow_free_roof_space: str
    monthly_electricity_bill: float
    grid_suitability: bool
    customer_interest: str
    estimated_opportunity_value: float
    notes: Optional[str] = None


class LeadOut(BaseModel):
    id: int
    lead_reference: str
    customer_id: Optional[int] = None
    customer_name: str
    phone: str
    email: Optional[str] = None
    address: str
    city: Optional[str] = None
    customer_type: str
    lead_source: str
    preferred_contact_method: Optional[str] = None
    required_capacity_kw: float
    solar_requirement: str
    monthly_bill: float
    subsidy_required: bool
    roof_availability: Optional[str] = None
    grid_suitable: bool
    estimated_value: float
    assigned_sales_rep: Optional[str] = None
    assigned_user_id: Optional[int] = None
    follow_up_date: Optional[date] = None
    stage: str
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ================= TECHNICIAN & SURVEY =================
TechnicianCategory = Literal[
    "Supervisor",
    "Senior Technician",
    "Junior Technician",
    "Electrician",
    "Solar Installer",
    "Labourer",
]


class TechnicianCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    skills: str = "Rooftop, Inverters, Electrical"
    category: TechnicianCategory = "Junior Technician"
    experience_years: int = 3
    availability: str = "AVAILABLE"
    employment_status: str = "FULL_TIME"


class TechnicianCategoryUpdate(BaseModel):
    category: TechnicianCategory


class TechnicianOut(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str] = None
    skills: str
    category: str
    experience_years: int
    availability: str
    status: str
    employment_status: str
    active_assignments: Optional[int] = 0

    class Config:
        from_attributes = True


class SurveyCreate(BaseModel):
    customer_id: int
    lead_id: Optional[int] = None
    technician_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    scheduled_date: date
    required_capacity_kw: float = 3.0
    monthly_bill: float = 0.0
    observations: Optional[str] = None


class SurveyUpdate(BaseModel):
    technician_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    actual_survey_date: Optional[date] = None
    roof_area: Optional[float] = None
    shadow_free_area: Optional[float] = None
    roof_direction: Optional[str] = None
    roof_tilt: Optional[float] = None
    cable_distance: Optional[float] = None
    structural_condition: Optional[str] = None
    grid_connection_suitable: Optional[bool] = None
    observations: Optional[str] = None
    technician_recommendation: Optional[str] = None
    photo_urls: Optional[str] = None
    status: Optional[str] = None


class SurveyApprove(BaseModel):
    action: str  # "APPROVE" or "REJECT"
    rejection_reason: Optional[str] = None
    approved_by: Optional[str] = "Sales Director"


class SurveyOut(BaseModel):
    id: int
    survey_reference: str
    lead_id: Optional[int] = None
    customer_id: int
    technician_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    scheduled_date: Optional[date] = None
    actual_survey_date: Optional[date] = None
    roof_area: float
    shadow_free_area: float
    roof_direction: str
    roof_tilt: float
    cable_distance: float
    structural_condition: str
    grid_connection_suitable: bool
    monthly_bill: float
    required_capacity_kw: float
    observations: Optional[str] = None
    technician_recommendation: Optional[str] = None
    rejection_reason: Optional[str] = None
    photo_urls: str
    status: str
    approval_status: str
    approved_by: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    technician_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ================= PRODUCTS, PACKAGES & BOM =================
class ProductCreate(BaseModel):
    name: str
    sku: str
    category: str
    manufacturer: str = "Aarka Tech"
    model: Optional[str] = None
    unit: str = "nos"
    capacity_kw: Optional[float] = None
    system_type: str = "Both"
    purchase_price: float
    selling_price: float
    min_stock: int = 5
    warranty_months: int = 24
    requires_serial: bool = False
    warehouse_location: str = "Rack A-1"
    description: Optional[str] = None


class ProductOut(BaseModel):
    id: int
    name: str
    sku: str
    category: str
    manufacturer: str
    model: Optional[str] = None
    unit: str
    capacity_kw: Optional[float] = None
    system_type: str
    purchase_price: float
    selling_price: float
    min_stock: int
    warranty_months: int
    requires_serial: bool
    warehouse_location: str
    description: Optional[str] = None
    stock_quantity: Optional[int] = 0

    class Config:
        from_attributes = True


class PackageOut(BaseModel):
    id: int
    name: str
    package_type: str
    capacity_kw: float
    base_price: float
    description: Optional[str] = None

    class Config:
        from_attributes = True


class BOMItemOut(BaseModel):
    product_id: int
    product_name: str
    sku: str
    category: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    is_serialized: bool


class BOMCalculationResult(BaseModel):
    package_type: str
    capacity_kw: float
    hardware_cost: float
    installation_cost: float
    subtotal: float
    tax_rate: float = 0.18
    tax_amount: float
    grand_total: float
    components: List[BOMItemOut]


# ================= QUOTATION & COMMERCIAL =================
class QuotationItemIn(BaseModel):
    product_id: Optional[int] = None
    product_name: str
    category: Optional[str] = None
    sku: Optional[str] = None
    quantity: float
    unit: str = "nos"
    unit_price: float
    is_serialized: bool = False


class QuotationCreate(BaseModel):
    customer_id: int
    lead_id: Optional[int] = None
    survey_id: Optional[int] = None
    package_type: str = "On-Grid System"
    capacity_kw: float = 3.0
    discount: float = 0.0
    advance_percentage: float = 20.0
    terms_conditions: Optional[str] = None
    custom_items: Optional[List[QuotationItemIn]] = None


class QuotationOut(BaseModel):
    id: int
    quotation_number: str
    customer_id: int
    lead_id: Optional[int] = None
    survey_id: Optional[int] = None
    package_type: str
    capacity_kw: float
    system_type: str
    hardware_cost: float
    installation_cost: float
    additional_expenses: float
    subtotal: float
    discount: float
    tax_rate: float
    tax_amount: float
    total_amount: float
    advance_amount: float
    balance_amount: float
    valid_until: Optional[date] = None
    terms_conditions: Optional[str] = None
    notes: Optional[str] = None
    status: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    items: List[Dict[str, Any]] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ================= SALES ORDER & PAYMENTS =================
class OrderOut(BaseModel):
    id: int
    order_number: str
    quotation_id: Optional[int] = None
    customer_id: int
    package_type: Optional[str] = None
    capacity_kw: float
    hardware_cost: float
    installation_cost: float
    total_amount: float
    advance_paid: float
    balance_due: float
    delivery_address: Optional[str] = None
    status: str
    picklist_generated: bool
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    items: List[Dict[str, Any]] = []
    payments: List[Dict[str, Any]] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    order_id: int
    customer_id: int
    amount: float
    method: str = "UPI"
    reference: Optional[str] = None
    payment_date: Optional[date] = None
    notes: Optional[str] = None


class PaymentOut(BaseModel):
    id: int
    payment_number: str
    order_id: int
    customer_id: int
    amount: float
    method: str
    reference: Optional[str] = None
    payment_date: Optional[date] = None
    verified_status: str
    status: str
    notes: Optional[str] = None
    customer_name: Optional[str] = None
    order_number: Optional[str] = None
    invoice_number: Optional[str] = None
    remaining_balance: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ================= INVENTORY & SERIALS =================
class StockReceiveRequest(BaseModel):
    product_id: int
    quantity: int
    supplier: Optional[str] = None
    purchase_reference: Optional[str] = None
    warehouse_location: Optional[str] = "Main Warehouse - Hall 1"
    unit_price: Optional[float] = None
    serial_numbers: Optional[List[str]] = None


class StockAdjustmentRequest(BaseModel):
    product_id: int
    quantity_delta: int
    reason: str


class InventoryItemOut(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    sku: str
    category: Optional[str] = None
    quantity: int
    reserved_quantity: int
    available_quantity: int
    reorder_level: int
    unit_price: float
    total_valuation: float
    warehouse_location: str
    supplier: Optional[str] = None

    class Config:
        from_attributes = True


class SerialCreate(BaseModel):
    product_id: int
    serial_number: str
    supplier: Optional[str] = "Aarka Tech"
    purchase_reference: Optional[str] = None
    current_location: Optional[str] = "Warehouse - Rack S1"


class SerialScanRequest(BaseModel):
    barcode: str
    order_id: Optional[int] = None


class SerialOut(BaseModel):
    id: int
    serial_number: str
    product_id: int
    product_name: Optional[str] = None
    category: Optional[str] = None
    status: str
    supplier: Optional[str] = None
    purchase_reference: Optional[str] = None
    current_location: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    order_id: Optional[int] = None
    order_number: Optional[str] = None
    dispatch_date: Optional[date] = None
    warranty_start: Optional[date] = None
    warranty_end: Optional[date] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ================= DISPATCH =================
class DispatchCreate(BaseModel):
    order_id: int
    delivery_reference: Optional[str] = None
    dispatch_date: Optional[date] = None
    dispatched_by: Optional[str] = "Warehouse Manager"
    assigned_user_id: Optional[int] = None
    serial_numbers: List[str]
    notes: Optional[str] = None


class DispatchConfirmDelivery(BaseModel):
    delivery_date: date
    delivery_proof_url: Optional[str] = None
    customer_confirmed: bool = True
    notes: Optional[str] = None


class DispatchOut(BaseModel):
    id: int
    order_id: int
    assigned_user_id: Optional[int] = None
    order_number: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    delivery_reference: str
    dispatch_date: Optional[date] = None
    delivery_date: Optional[date] = None
    status: str
    customer_confirmed: bool
    delivery_proof_url: Optional[str] = None
    dispatched_by: Optional[str] = None
    serial_numbers: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ================= INSTALLATION =================
class InstallationCreate(BaseModel):
    order_id: int
    technician_id: int
    assigned_user_id: Optional[int] = None
    scheduled_date: date
    capacity_kw: float = 3.0


class InstallationChecklistUpdate(BaseModel):
    checklist_state: Dict[str, bool]
    technical_observations: Optional[str] = None
    testing_results: Optional[str] = None


class InstallationComplete(BaseModel):
    checklist_state: Dict[str, bool]
    technical_observations: str
    testing_results: str
    customer_signature: str  # Data URL or signature string
    photo_urls: Optional[List[str]] = None
    labour_hours: float = 6.0


class InstallationOut(BaseModel):
    id: int
    job_number: Optional[str] = None
    order_id: int
    order_number: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    technician_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    technician_name: Optional[str] = None
    assigned_at: Optional[datetime] = None
    scheduled_date: Optional[date] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str
    capacity_kw: float
    checklist_state: str
    installed_equipment: Optional[str] = None
    technical_observations: Optional[str] = None
    customer_signature: Optional[str] = None
    photo_urls: str
    testing_results: Optional[str] = None
    labour_hours: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ================= WARRANTY & SERVICE =================
class WarrantyOut(BaseModel):
    id: int
    warranty_number: Optional[str] = None
    serial_number: str
    product_id: int
    product_name: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    warranty_type: Optional[str] = "PRODUCT"
    duration_months: Optional[int] = 24
    customer_id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    order_id: Optional[int] = None
    order_number: Optional[str] = None
    installation_id: Optional[int] = None
    delivery_date: Optional[date] = None
    warranty_start: date
    warranty_end: date
    days_remaining: Optional[int] = None
    status: str
    coverage_terms: str
    certificate_url: Optional[str] = None
    notes: Optional[str] = None
    open_claims_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WarrantyStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class WarrantyClaimCreate(BaseModel):
    warranty_id: int
    issue_description: str
    supporting_documents: Optional[List[str]] = None
    manufacturer_reference: Optional[str] = None
    assigned_technician_id: Optional[int] = None


class WarrantyClaimUpdate(BaseModel):
    claim_status: Optional[str] = None
    manufacturer_reference: Optional[str] = None
    assigned_technician_id: Optional[int] = None
    replacement_serial_number: Optional[str] = None
    resolution_details: Optional[str] = None
    resolution_date: Optional[date] = None


class WarrantyClaimOut(BaseModel):
    id: int
    claim_number: str
    warranty_id: int
    warranty_number: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    order_id: Optional[int] = None
    order_number: Optional[str] = None
    serial_number: str
    equipment_name: Optional[str] = None
    issue_description: str
    supporting_documents: List[str] = []
    manufacturer_reference: Optional[str] = None
    assigned_technician_id: Optional[int] = None
    assigned_technician_name: Optional[str] = None
    claim_status: str
    replacement_serial_number: Optional[str] = None
    resolution_details: Optional[str] = None
    resolution_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ServiceTicketCreate(BaseModel):
    customer_id: int
    assigned_user_id: Optional[int] = None
    serial_number: Optional[str] = None
    reported_serial_number: Optional[str] = None
    fault_description: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    fault_code: Optional[str] = "ERR-04"
    priority: str = "MEDIUM"
    installation_id: Optional[int] = None
    complaint_photos: Optional[List[str]] = None


class ServiceTicketUpdate(BaseModel):
    technician_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    diagnosis: Optional[str] = None
    repair_details: Optional[str] = None
    resolution_notes: Optional[str] = None
    parts_used: Optional[str] = None
    labour_charges: Optional[float] = None
    parts_charges: Optional[float] = None
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    status: Optional[str] = None
    customer_approved_estimate: Optional[bool] = None
    customer_signature: Optional[str] = None


class ServiceTicketReplaceEquipment(BaseModel):
    replacement_serial_number: Optional[str] = None
    new_serial_number: Optional[str] = None
    reason: Optional[str] = None
    replacement_reason: Optional[str] = None


class ServiceTicketOut(BaseModel):
    id: int
    ticket_number: str
    customer_id: int
    assigned_user_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    serial_number: str
    equipment_type: Optional[str] = None
    installation_id: Optional[int] = None
    fault_code: str
    fault_description: str
    complaint_photos: str
    priority: str
    technician_id: Optional[int] = None
    technician_name: Optional[str] = None
    warranty_eligible: bool
    warranty_status: str
    diagnosis: Optional[str] = None
    repair_details: Optional[str] = None
    parts_used: str
    labour_charges: float
    parts_charges: float
    total_charges: float
    customer_approved_estimate: bool
    replacement_serial_number: Optional[str] = None
    status: str
    reported_date: Optional[date] = None
    resolution_date: Optional[date] = None
    customer_confirmed: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ================= SUPPLIER & FINANCE =================
class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    category: str = "Solar Panels & Inverters"
    lead_time_days: int = 7


class SupplierOut(BaseModel):
    id: int
    name: str
    contact_person: Optional[str] = None
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    category: str
    lead_time_days: int
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExpenseCreate(BaseModel):
    order_id: Optional[int] = None
    category: str
    amount: float
    gst_amount: Optional[float] = 0.0
    supplier_id: Optional[int] = None
    vendor_name: Optional[str] = None
    invoice_reference: Optional[str] = None
    payment_method: Optional[str] = "BANK_TRANSFER"
    approval_status: Optional[str] = "APPROVED"
    document_url: Optional[str] = None
    description: Optional[str] = None
    expense_date: Optional[date] = None


class ExpenseOut(BaseModel):
    id: int
    order_id: Optional[int] = None
    order_number: Optional[str] = None
    category: str
    amount: float
    gst_amount: Optional[float] = 0.0
    supplier_id: Optional[int] = None
    vendor_name: Optional[str] = None
    invoice_reference: Optional[str] = None
    payment_method: Optional[str] = "BANK_TRANSFER"
    approval_status: Optional[str] = "APPROVED"
    document_url: Optional[str] = None
    description: Optional[str] = None
    expense_date: Optional[date] = None
    recorded_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InvoiceItemSchema(BaseModel):
    description: str
    category: Optional[str] = "EQUIPMENT"
    quantity: float = 1.0
    unit: Optional[str] = "nos"
    unit_price: float = 0.0
    tax_rate: Optional[float] = 0.138
    tax_amount: Optional[float] = 0.0
    total_amount: float = 0.0


class InvoiceCreate(BaseModel):
    order_id: int
    due_date: Optional[date] = None
    tax_rate: Optional[float] = 0.138
    discount: Optional[float] = 0.0
    notes: Optional[str] = None
    custom_items: Optional[List[InvoiceItemSchema]] = None


class InvoiceStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class InvoiceOut(BaseModel):
    id: int
    invoice_number: str
    order_id: int
    order_number: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    subtotal: float
    tax_rate: float
    tax_amount: float
    discount: float
    total_amount: float
    paid_amount: float
    balance_due: float
    status: str
    due_date: Optional[date] = None
    notes: Optional[str] = None
    items: List[InvoiceItemSchema] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectProfitabilityOut(BaseModel):
    order_id: int
    order_number: str
    customer_name: str
    capacity_kw: float
    package_type: str
    recognized_revenue: float
    advance_paid: float
    balance_due: float
    hardware_cost: float
    labour_cost: float
    transportation_cost: float
    other_expenses: float
    total_cost: float
    gross_margin: float
    gross_margin_percentage: float
    status: str


# ================= SUBSIDY =================
class SubsidyEligibilityCheckRequest(BaseModel):
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    category: str = "RESIDENTIAL"  # RESIDENTIAL | GHS_RWA | COMMERCIAL
    state: str = "Telangana"
    discom_name: str = "TSSPDCL"
    consumer_number: str
    capacity_kw: float = 3.0
    prior_subsidy_claimed: bool = False
    is_grid_connected: bool = True


class SubsidyEligibilityCheckResponse(BaseModel):
    is_eligible: bool
    scheme_name: str
    category: str
    capacity_kw: float
    eligible_capacity_kw: float
    estimated_subsidy: float
    central_subsidy: float
    state_subsidy: float
    benchmark_cost: float
    estimated_project_cost: float
    estimated_customer_outlay: float
    status: str  # ELIGIBLE | INELIGIBLE | REQUIRES_DOCUMENTATION
    reasons: List[str]
    conditions: List[str]
    disclaimer: str
    scheme_source: str


class SubsidyCalculateResponse(BaseModel):
    scheme_name: str
    category: str
    capacity_kw: float
    eligible_capacity_kw: float
    central_subsidy: float
    state_subsidy: float
    total_subsidy: float
    estimated_cost: float
    customer_contribution: float
    calculation_steps: List[str]
    max_subsidy_limit: float
    disclaimer: str


class SubsidyCreate(BaseModel):
    customer_id: int
    order_id: Optional[int] = None
    installation_id: Optional[int] = None
    scheme_name: str = "PM Surya Ghar Muft Bijli Yojana"
    category: str = "RESIDENTIAL"
    state: str = "Telangana"
    discom_name: str = "TSSPDCL"
    consumer_number: Optional[str] = None
    portal_application_ref: Optional[str] = None
    capacity_kw: float = 3.0
    subsidy_amount: Optional[float] = 78000.0
    assigned_officer: Optional[str] = None
    remarks: Optional[str] = None


class SubsidyUpdate(BaseModel):
    verification_status: Optional[str] = None
    approval_status: Optional[str] = None
    portal_application_ref: Optional[str] = None
    consumer_number: Optional[str] = None
    inspection_date: Optional[date] = None
    approval_date: Optional[date] = None
    disbursement_date: Optional[date] = None
    approved_amount: Optional[float] = None
    disbursed_amount: Optional[float] = None
    disbursement_reference: Optional[str] = None
    subsidy_amount: Optional[float] = None
    payment_status: Optional[str] = None
    assigned_officer: Optional[str] = None
    remarks: Optional[str] = None


class SubsidyOut(BaseModel):
    id: int
    application_number: str
    customer_id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    order_id: Optional[int] = None
    order_number: Optional[str] = None
    scheme_name: str
    scheme_id: Optional[int] = None
    assessment_id: Optional[int] = None
    installation_id: Optional[int] = None
    category: Optional[str] = "RESIDENTIAL"
    state: Optional[str] = "Telangana"
    discom_name: Optional[str] = "TSSPDCL"
    consumer_number: Optional[str] = None
    portal_application_ref: Optional[str] = None
    capacity_kw: float
    submission_date: Optional[date] = None
    inspection_date: Optional[date] = None
    approval_date: Optional[date] = None
    commissioning_date: Optional[date] = None
    disbursement_date: Optional[date] = None
    internal_status: Optional[str] = "DRAFT"
    verification_status: str
    official_status: Optional[str] = "NOT_SUBMITTED"
    approval_status: str
    estimated_amount: Optional[float] = 78000.0
    requested_amount: Optional[float] = 78000.0
    subsidy_amount: float
    approved_amount: Optional[float] = 0.0
    disbursed_amount: Optional[float] = 0.0
    disbursement_reference: Optional[str] = None
    payment_status: str
    assigned_officer: Optional[str] = None
    assigned_employee_id: Optional[int] = None
    eligibility_notes: Optional[str] = None
    documents: str
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SchemeRuleOut(BaseModel):
    id: int
    scheme_id: int
    customer_category: str
    state: str
    capacity_min: float
    capacity_max: float
    rate_per_kw: float
    maximum_assistance: float
    calculation_type: str
    rule_version: str
    eligibility_configuration: str
    document_checklist_configuration: str
    effective_from: date
    effective_until: Optional[date] = None

    class Config:
        from_attributes = True


class GovernmentSchemeOut(BaseModel):
    id: int
    code: str
    name: str
    authority: str
    category: str
    jurisdiction: str
    state: Optional[str] = None
    description: str
    source_url: str
    notification_reference: Optional[str] = None
    effective_from: date
    effective_until: Optional[date] = None
    last_verified_at: date
    verification_status: str
    is_active: bool
    rules: List[SchemeRuleOut] = []

    class Config:
        from_attributes = True


class SubsidyAssessmentCreate(BaseModel):
    customer_id: Optional[int] = None
    applicant_name: Optional[str] = None
    applicant_phone: Optional[str] = None
    applicant_email: Optional[str] = None
    order_id: Optional[int] = None
    scheme_code: str = "PM_SURYA_GHAR_RES"
    state: str = "Telangana"
    district: Optional[str] = None
    customer_category: str = "RESIDENTIAL"
    proposed_capacity: float = 3.0
    discom_name: str = "TSSPDCL"
    consumer_number: str
    tariff_category: Optional[str] = "LT-1 Residential"
    sanctioned_load_kw: Optional[float] = 3.0
    monthly_consumption_units: Optional[float] = 250.0
    roof_type: Optional[str] = "RCC Flat Concrete"
    available_roof_area_sqft: Optional[float] = 300.0
    has_roof_rights: bool = True
    is_grid_connected: bool = True
    prior_subsidy_claimed: bool = False
    scheme_specific_data: Optional[Dict[str, Any]] = None


class SubsidyAssessmentOut(BaseModel):
    id: int
    customer_id: Optional[int] = None
    applicant_name: Optional[str] = None
    applicant_phone: Optional[str] = None
    applicant_email: Optional[str] = None
    scheme_code: Optional[str] = None
    state: str
    customer_category: str
    proposed_capacity: float
    discom_name: Optional[str] = None
    consumer_number: Optional[str] = None
    rule_version: str
    estimated_central_assistance: float
    estimated_state_assistance: float
    estimated_total_assistance: float
    estimated_project_cost: float
    estimated_customer_outlay: float
    eligibility_status: str
    calculation_breakdown: str
    disclaimer_acknowledged: bool
    assessment_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubsidyDocumentOut(BaseModel):
    id: int
    application_id: int
    document_type: str
    storage_path: str
    original_filename: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_by: str
    review_status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    version_number: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubsidyDocumentReviewRequest(BaseModel):
    decision: str  # VERIFIED | REJECTED | CORRECTION_REQUESTED
    remarks: Optional[str] = None


class VerificationRecordOut(BaseModel):
    id: int
    application_id: int
    document_id: Optional[int] = None
    reviewer_name: str
    verification_type: str
    decision: str
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubsidyStatusHistoryOut(BaseModel):
    id: int
    application_id: int
    previous_status: Optional[str] = None
    new_status: str
    status_type: str
    updated_by: str
    actor_type: str
    evidence_reference: Optional[str] = None
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubsidyOfficialStatusUpdateRequest(BaseModel):
    official_status: str  # NOT_SUBMITTED | SUBMITTED | FEASIBILITY_PENDING | FEASIBILITY_APPROVED | FEASIBILITY_REJECTED | INSPECTION_PENDING | COMMISSIONED | SUBSIDY_CLAIM_PENDING | APPROVED | REJECTED | DISBURSED
    portal_application_ref: Optional[str] = None
    evidence_reference: Optional[str] = None
    remarks: Optional[str] = None
    inspection_date: Optional[date] = None
    commissioning_date: Optional[date] = None
    approval_date: Optional[date] = None
    disbursement_date: Optional[date] = None
    approved_amount: Optional[float] = None
    disbursed_amount: Optional[float] = None
    disbursement_reference: Optional[str] = None
