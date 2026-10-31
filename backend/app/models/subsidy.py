from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class GovernmentScheme(Base):
    __tablename__ = "government_schemes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(60), unique=True, index=True, nullable=False)
    name = Column(String(160), nullable=False)
    authority = Column(String(140), nullable=False)
    category = Column(String(60), nullable=False)  # RESIDENTIAL | GHS_RWA | AGRICULTURAL | COMMERCIAL
    jurisdiction = Column(String(60), default="CENTRAL")  # CENTRAL | STATE
    state = Column(String(80), nullable=True)  # Specific state or null for pan-India
    description = Column(Text, nullable=False)
    source_url = Column(String(255), nullable=False)
    notification_reference = Column(String(150), nullable=True)
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date, nullable=True)
    last_verified_at = Column(Date, nullable=False)
    verification_status = Column(String(60), default="OFFICIALLY_VERIFIED")  # OFFICIALLY_VERIFIED | REQUIRES_CONFIRMATION | EXPIRED
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    rules = relationship("SchemeRule", back_populates="scheme", cascade="all, delete-orphan")
    applications = relationship("SubsidyApplication", back_populates="scheme")


class SchemeRule(Base):
    __tablename__ = "scheme_rules"

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(Integer, ForeignKey("government_schemes.id"), nullable=False)
    customer_category = Column(String(60), nullable=False)  # RESIDENTIAL | GHS_RWA | AGRICULTURAL
    state = Column(String(80), default="ALL")
    capacity_min = Column(Float, default=1.0)
    capacity_max = Column(Float, default=10.0)
    rate_per_kw = Column(Float, default=30000.0)
    maximum_assistance = Column(Float, default=78000.0)
    calculation_type = Column(String(60), default="TIERED_PMSG")  # TIERED_PMSG | FLAT_PER_KW | PERCENTAGE_BENCHMARK | CUSTOM_GBI
    eligibility_configuration = Column(Text, default="{}")  # JSON rules & questions
    document_checklist_configuration = Column(Text, default="[]")  # JSON list of required docs by phase
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date, nullable=True)
    rule_version = Column(String(50), default="2024.1-MNRE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    scheme = relationship("GovernmentScheme", back_populates="rules")


class SubsidyAssessment(Base):
    __tablename__ = "subsidy_assessments"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    applicant_name = Column(String(120), nullable=True)
    applicant_phone = Column(String(30), nullable=True)
    applicant_email = Column(String(120), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    scheme_id = Column(Integer, ForeignKey("government_schemes.id"), nullable=True)
    scheme_code = Column(String(60), nullable=True)
    state = Column(String(80), default="Telangana")
    customer_category = Column(String(60), default="RESIDENTIAL")
    proposed_capacity = Column(Float, default=3.0)
    discom_name = Column(String(100), nullable=True)
    consumer_number = Column(String(100), nullable=True)
    rule_version = Column(String(50), default="2024.1-MNRE")
    estimated_central_assistance = Column(Float, default=0.0)
    estimated_state_assistance = Column(Float, default=0.0)
    estimated_total_assistance = Column(Float, default=0.0)
    estimated_project_cost = Column(Float, default=0.0)
    estimated_customer_outlay = Column(Float, default=0.0)
    eligibility_status = Column(String(60), default="POTENTIALLY_ELIGIBLE")  # POTENTIALLY_ELIGIBLE | MORE_INFO_REQUIRED | POTENTIALLY_NOT_ELIGIBLE
    calculation_breakdown = Column(Text, default="{}")  # JSON explanation and calculations
    disclaimer_acknowledged = Column(Boolean, default=True)
    assessment_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer")
    order = relationship("SalesOrder")
    scheme = relationship("GovernmentScheme")
    application = relationship("SubsidyApplication", back_populates="assessment", uselist=False)


class SubsidyApplication(Base):
    __tablename__ = "subsidy_applications"

    id = Column(Integer, primary_key=True, index=True)
    application_number = Column(String(80), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    installation_id = Column(Integer, ForeignKey("installations.id"), nullable=True)
    scheme_id = Column(Integer, ForeignKey("government_schemes.id"), nullable=True)
    assessment_id = Column(Integer, ForeignKey("subsidy_assessments.id"), nullable=True)
    assigned_employee_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    scheme_name = Column(String(120), default="PM Surya Ghar Muft Bijli Yojana")
    category = Column(String(50), default="RESIDENTIAL")  # RESIDENTIAL | GHS_RWA | AGRICULTURAL | COMMERCIAL
    state = Column(String(80), default="Telangana")
    discom_name = Column(String(80), default="TSSPDCL")
    consumer_number = Column(String(80), nullable=True)
    portal_application_ref = Column(String(100), nullable=True)
    capacity_kw = Column(Float, default=3.0)

    # Internal AARKA Lifecycle & Readiness
    internal_status = Column(String(60), default="DRAFT")  # DRAFT | DOCUMENTS_PENDING | UNDER_INTERNAL_REVIEW | CORRECTION_REQUIRED | READY_FOR_SUBMISSION
    verification_status = Column(String(60), default="PENDING")  # PENDING | VERIFIED | REJECTED

    # Official Government & DISCOM Lifecycle Tracking
    official_status = Column(String(60), default="NOT_SUBMITTED")  # NOT_SUBMITTED | SUBMITTED | FEASIBILITY_PENDING | FEASIBILITY_APPROVED | FEASIBILITY_REJECTED | INSPECTION_PENDING | COMMISSIONED | SUBSIDY_CLAIM_PENDING | APPROVED | REJECTED | DISBURSED
    approval_status = Column(String(60), default="UNDER_REVIEW")  # Kept for backward compatibility with existing records

    # Key Milestone Dates
    submission_date = Column(Date, nullable=True)
    inspection_date = Column(Date, nullable=True)
    approval_date = Column(Date, nullable=True)
    commissioning_date = Column(Date, nullable=True)
    disbursement_date = Column(Date, nullable=True)

    # Financial Assistance Accounting
    estimated_amount = Column(Float, default=78000.0)
    requested_amount = Column(Float, default=78000.0)
    subsidy_amount = Column(Float, default=78000.0)  # Kept for backward compatibility
    approved_amount = Column(Float, default=0.0)
    disbursed_amount = Column(Float, default=0.0)
    disbursement_reference = Column(String(120), nullable=True)
    payment_status = Column(String(60), default="PENDING")  # PENDING | SANCTIONED | DISBURSED

    assigned_officer = Column(String(100), nullable=True)
    eligibility_notes = Column(Text, nullable=True)
    documents = Column(Text, default="[]")  # JSON snapshot for backward compatibility
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer")
    installation = relationship("InstallationJob")
    order = relationship("SalesOrder")
    scheme = relationship("GovernmentScheme", back_populates="applications")
    assessment = relationship("SubsidyAssessment", back_populates="application")
    assigned_employee = relationship("User", foreign_keys=[assigned_employee_id])
    documents_list = relationship("SubsidyDocument", back_populates="application", cascade="all, delete-orphan")
    verification_records = relationship("VerificationRecord", back_populates="application", cascade="all, delete-orphan")
    status_history = relationship("SubsidyStatusHistory", back_populates="application", cascade="all, delete-orphan")


class SubsidyDocument(Base):
    __tablename__ = "subsidy_documents"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("subsidy_applications.id"), nullable=False)
    document_type = Column(String(80), nullable=False)  # ELECTRICITY_BILL | PROPERTY_TAX_OR_ROOF_CONSENT | AADHAAR_CARD | BANK_PASSBOOK_OR_CHEQUE | INSTALLATION_PHOTO | NET_METER_REPORT | COMMISSIONING_CERTIFICATE | RWA_RESOLUTION | FARMER_LAND_RECORD
    storage_path = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(80), nullable=True)
    uploaded_by = Column(String(100), nullable=False)
    review_status = Column(String(60), default="UPLOADED")  # NOT_UPLOADED | UPLOADED | UNDER_REVIEW | VERIFIED_BY_AARKA | REJECTED | RE_UPLOAD_REQUIRED | NOT_REQUIRED
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    version_number = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    application = relationship("SubsidyApplication", back_populates="documents_list")
    verifications = relationship("VerificationRecord", back_populates="document")


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("subsidy_applications.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("subsidy_documents.id"), nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewer_name = Column(String(100), nullable=False)
    verification_type = Column(String(60), default="EMPLOYEE_DOCUMENT_REVIEW")  # AUTOMATED_VALIDATION | EMPLOYEE_DOCUMENT_REVIEW | OFFICIAL_GOVERNMENT_STATUS
    decision = Column(String(60), nullable=False)  # VERIFIED | REJECTED | CORRECTION_REQUESTED | MATCH | MISMATCH
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("SubsidyApplication", back_populates="verification_records")
    document = relationship("SubsidyDocument", back_populates="verifications")
    reviewer = relationship("User")


class SubsidyStatusHistory(Base):
    __tablename__ = "subsidy_status_history"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("subsidy_applications.id"), nullable=False)
    previous_status = Column(String(60), nullable=True)
    new_status = Column(String(60), nullable=False)
    status_type = Column(String(40), default="OFFICIAL")  # INTERNAL | OFFICIAL | PAYMENT
    updated_by = Column(String(100), nullable=False)
    actor_type = Column(String(60), default="AARKA_EMPLOYEE")  # SYSTEM | AARKA_EMPLOYEE | DISCOM | GOVT_PORTAL | CUSTOMER
    evidence_reference = Column(String(150), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("SubsidyApplication", back_populates="status_history")
