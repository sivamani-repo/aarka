from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class SubsidyApplication(Base):
    __tablename__ = "subsidy_applications"

    id = Column(Integer, primary_key=True, index=True)
    application_number = Column(String(80), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    scheme_name = Column(String(120), default="PM Surya Ghar Muft Bijli Yojana")
    installation_id = Column(Integer, ForeignKey("installations.id"), nullable=True)
    capacity_kw = Column(Float, default=3.0)
    submission_date = Column(Date, nullable=True)
    verification_status = Column(String(60), default="PENDING")
    approval_status = Column(String(60), default="UNDER_REVIEW")
    subsidy_amount = Column(Float, default=78000.0)
    payment_status = Column(String(60), default="PENDING")
    documents = Column(Text, default="[]")
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer")
    installation = relationship("InstallationJob")

