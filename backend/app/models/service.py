from sqlalchemy import Column, Integer, String, Boolean, Float, Date, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class WarrantyRecord(Base):
    __tablename__ = "warranty_records"

    id = Column(Integer, primary_key=True, index=True)
    warranty_number = Column(String(60), unique=True, index=True, nullable=True)
    serial_number = Column(String(120), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    installation_id = Column(Integer, ForeignKey("installations.id"), nullable=True)
    warranty_type = Column(String(50), default="PRODUCT")  # PRODUCT | PERFORMANCE | WORKMANSHIP
    manufacturer = Column(String(100), default="Aarka Tech")
    model_number = Column(String(100), nullable=True)
    duration_months = Column(Integer, default=24)
    delivery_date = Column(Date, nullable=True)
    warranty_start = Column(Date, nullable=False)
    warranty_end = Column(Date, nullable=False)
    status = Column(String(60), default="ACTIVE")  # PENDING_ACTIVATION | ACTIVE | EXPIRING_SOON | EXPIRED | CLAIM_RAISED | UNDER_REVIEW | RESOLVED
    coverage_terms = Column(Text, default="100% parts & labor covered under manufacturer warranty policy")
    certificate_url = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    expiry_alert_90d_sent = Column(Boolean, default=False)
    expiry_alert_30d_sent = Column(Boolean, default=False)
    expiry_alert_7d_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product = relationship("Product")
    customer = relationship("Customer")
    order = relationship("SalesOrder")
    installation = relationship("InstallationJob")
    claims = relationship("WarrantyClaim", back_populates="warranty", cascade="all, delete-orphan")


class WarrantyClaim(Base):
    __tablename__ = "warranty_claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String(60), unique=True, index=True, nullable=False)
    warranty_id = Column(Integer, ForeignKey("warranty_records.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    serial_number = Column(String(120), index=True, nullable=False)
    equipment_name = Column(String(150), nullable=True)
    issue_description = Column(Text, nullable=False)
    supporting_documents = Column(Text, default="[]")
    manufacturer_reference = Column(String(100), nullable=True)  # OEM RMA tracking #
    assigned_technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    claim_status = Column(String(60), default="CLAIM_RAISED")  # CLAIM_RAISED | UNDER_REVIEW | APPROVED_BY_OEM | REPLACEMENT_IN_PROGRESS | REPAIRED | REJECTED | RESOLVED
    replacement_serial_number = Column(String(120), nullable=True)
    resolution_details = Column(Text, nullable=True)
    resolution_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    warranty = relationship("WarrantyRecord", back_populates="claims")
    customer = relationship("Customer")
    technician = relationship("Technician")
    order = relationship("SalesOrder")


class ServiceTicket(Base):
    __tablename__ = "service_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(60), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    serial_number = Column(String(120), index=True, nullable=False)
    equipment_type = Column(String(100), nullable=True)
    installation_id = Column(Integer, ForeignKey("installations.id"), nullable=True)
    fault_code = Column(String(60), default="ERR-04")
    fault_description = Column(Text, nullable=False)
    complaint_photos = Column(Text, default="[]")
    priority = Column(String(60), default="MEDIUM")
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    warranty_eligible = Column(Boolean, default=True)
    warranty_status = Column(String(60), default="COVERED")
    diagnosis = Column(Text, nullable=True)
    repair_details = Column(Text, nullable=True)
    parts_used = Column(Text, default="[]")
    labour_charges = Column(Float, default=0.0)
    parts_charges = Column(Float, default=0.0)
    total_charges = Column(Float, default=0.0)
    customer_approved_estimate = Column(Boolean, default=False)
    replacement_serial_number = Column(String(120), nullable=True)
    status = Column(String(60), default="OPEN")
    reported_date = Column(Date, nullable=True)
    resolution_date = Column(Date, nullable=True)
    customer_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer")
    technician = relationship("Technician")
    installation = relationship("InstallationJob")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
