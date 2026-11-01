from sqlalchemy import Column, Integer, String, Boolean, Float, Date, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Technician(Base):
    __tablename__ = "technicians"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    phone = Column(String(30), nullable=False)
    email = Column(String(150), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True)
    skills = Column(String(200), default="Rooftop, Inverters, Electrical")
    experience_years = Column(Integer, default=3)
    availability = Column(String(50), default="AVAILABLE")
    availability_updated_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
    status = Column(String(50), default="ACTIVE")
    employment_status = Column(String(50), default="FULL_TIME")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    surveys = relationship("SiteSurvey", back_populates="technician")


class SiteSurvey(Base):
    __tablename__ = "site_surveys"

    id = Column(Integer, primary_key=True, index=True)
    survey_reference = Column(String(60), unique=True, index=True, nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    scheduled_date = Column(Date, nullable=True)
    actual_survey_date = Column(Date, nullable=True)
    roof_area = Column(Float, default=0.0)
    shadow_free_area = Column(Float, default=0.0)
    roof_direction = Column(String(60), default="South")
    roof_tilt = Column(Float, default=15.0)
    cable_distance = Column(Float, default=15.0)
    structural_condition = Column(String(80), default="Good")
    grid_connection_suitable = Column(Boolean, default=True)
    monthly_bill = Column(Float, default=0.0)
    required_capacity_kw = Column(Float, default=3.0)
    observations = Column(Text, nullable=True)
    technician_recommendation = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    photo_urls = Column(Text, default="[]")
    status = Column(String(60), default="SCHEDULED")
    approval_status = Column(String(60), default="PENDING")
    approved_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    technician = relationship("Technician", back_populates="surveys")
    customer = relationship("Customer")
    lead = relationship("Lead")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
