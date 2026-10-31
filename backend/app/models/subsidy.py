from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class SubsidyApplication(Base):
    __tablename__ = "subsidy_applications"

    id = Column(Integer, primary_key=True, index=True)
    application_number = Column(String(80), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    scheme_name = Column(String(120), default="PM Surya Ghar Muft Bijli Yojana")
    installation_id = Column(Integer, ForeignKey("installations.id"), nullable=True)
    category = Column(String(50), default="RESIDENTIAL")  # RESIDENTIAL | GHS_RWA | COMMERCIAL
    state = Column(String(80), default="Telangana")
    discom_name = Column(String(80), default="TSSPDCL")
    consumer_number = Column(String(80), nullable=True)
    portal_application_ref = Column(String(100), nullable=True)
    capacity_kw = Column(Float, default=3.0)
    submission_date = Column(Date, nullable=True)
    inspection_date = Column(Date, nullable=True)
    approval_date = Column(Date, nullable=True)
    disbursement_date = Column(Date, nullable=True)
    verification_status = Column(String(60), default="PENDING")
    approval_status = Column(String(60), default="UNDER_REVIEW")
    subsidy_amount = Column(Float, default=78000.0)
    approved_amount = Column(Float, default=0.0)
    disbursed_amount = Column(Float, default=0.0)
    disbursement_reference = Column(String(120), nullable=True)
    payment_status = Column(String(60), default="PENDING")
    assigned_officer = Column(String(100), nullable=True)
    eligibility_notes = Column(Text, nullable=True)
    documents = Column(Text, default="[]")
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer")
    installation = relationship("InstallationJob")
    order = relationship("SalesOrder")
