from sqlalchemy import Column, Integer, String, Boolean, Float, Date, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    phone = Column(String(30), nullable=False, index=True)
    email = Column(String(150), nullable=True, index=True)
    address = Column(Text, nullable=False)
    city = Column(String(80), nullable=True)
    customer_type = Column(String(40), nullable=False, default="Residential")
    lead_source = Column(String(60), nullable=True, default="Website")
    required_capacity_kw = Column(Float, nullable=True, default=3.0)
    solar_requirement = Column(String(60), nullable=True, default="On-Grid")
    monthly_bill = Column(Float, nullable=True, default=0.0)
    subsidy_required = Column(Boolean, default=False)
    status = Column(String(60), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    leads = relationship("Lead", back_populates="customer")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    lead_reference = Column(String(60), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String(150), nullable=False)
    phone = Column(String(30), nullable=False, index=True)
    email = Column(String(150), nullable=True)
    address = Column(Text, nullable=False)
    city = Column(String(80), nullable=True)
    customer_type = Column(String(40), default="Residential")
    lead_source = Column(String(60), default="Website")
    preferred_contact_method = Column(String(40), default="Phone")
    required_capacity_kw = Column(Float, default=3.0)
    solar_requirement = Column(String(60), default="On-Grid")
    monthly_bill = Column(Float, default=0.0)
    subsidy_required = Column(Boolean, default=False)
    roof_availability = Column(String(80), nullable=True)
    grid_suitable = Column(Boolean, default=True)
    estimated_value = Column(Float, default=0.0)
    assigned_sales_rep = Column(String(100), nullable=True)
    follow_up_date = Column(Date, nullable=True)
    stage = Column(String(60), default="NEW")
    status = Column(String(60), default="OPEN")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="leads")

