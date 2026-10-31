from typing import List, Optional, Dict, Any
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
    name: str
    email: str
    password: str
    role: str = "Sales Representative"
    phone: Optional[str] = None

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    is_active: bool
    is_verified: bool = False
    created_at: Optional[datetime] = None

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
    follow_up_date: Optional[date] = None
    stage: str
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ================= TECHNICIAN & SURVEY =================
class TechnicianCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    skills: str = "Rooftop, Inverters, Electrical"
    experience_years: int = 3
    availability: str = "AVAILABLE"
    employment_status: str = "FULL_TIME"


class TechnicianOut(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str] = None
    skills: str
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
    scheduled_date: date
    required_capacity_kw: float = 3.0
    monthly_bill: float = 0.0
    observations: Optional[str] = None


class SurveyUpdate(BaseModel):
    technician_id: Optional[int] = None
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
    customer_id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    order_id: Optional[int] = None
    order_number: Optional[str] = None
    delivery_date: Optional[date] = None
    warranty_start: date
    warranty_end: date
    status: str
    coverage_terms: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ServiceTicketCreate(BaseModel):
    customer_id: int
    serial_number: str
    fault_description: str
    fault_code: Optional[str] = "ERR-04"
    priority: str = "MEDIUM"
    installation_id: Optional[int] = None
    complaint_photos: Optional[List[str]] = None


class ServiceTicketUpdate(BaseModel):
    technician_id: Optional[int] = None
    diagnosis: Optional[str] = None
    repair_details: Optional[str] = None
    parts_used: Optional[str] = None
    labour_charges: Optional[float] = None
    parts_charges: Optional[float] = None
    status: Optional[str] = None
    customer_approved_estimate: Optional[bool] = None


class ServiceTicketReplaceEquipment(BaseModel):
    replacement_serial_number: str
    reason: str


class ServiceTicketOut(BaseModel):
    id: int
    ticket_number: str
    customer_id: int
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
    description: Optional[str] = None
    expense_date: Optional[date] = None


class ExpenseOut(BaseModel):
    id: int
    order_id: Optional[int] = None
    category: str
    amount: float
    description: Optional[str] = None
    expense_date: Optional[date] = None
    recorded_by: Optional[str] = None
    created_at: Optional[datetime] = None

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
class SubsidyCreate(BaseModel):
    customer_id: int
    scheme_name: str = "PM Surya Ghar Muft Bijli Yojana"
    installation_id: Optional[int] = None
    capacity_kw: float = 3.0
    subsidy_amount: float = 78000.0
    remarks: Optional[str] = None


class SubsidyUpdate(BaseModel):
    verification_status: Optional[str] = None
    approval_status: Optional[str] = None
    subsidy_amount: Optional[float] = None
    payment_status: Optional[str] = None
    remarks: Optional[str] = None


class SubsidyOut(BaseModel):
    id: int
    application_number: str
    customer_id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    scheme_name: str
    installation_id: Optional[int] = None
    capacity_kw: float
    submission_date: Optional[date] = None
    verification_status: str
    approval_status: str
    subsidy_amount: float
    payment_status: str
    documents: str
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
