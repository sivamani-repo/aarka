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
    delivery_date = Column(Date, nullable=True)
    warranty_start = Column(Date, nullable=False)
    warranty_end = Column(Date, nullable=False)
    status = Column(String(60), default="COVERED")
    coverage_terms = Column(Text, default="100% parts & labor covered under manufacturer warranty policy")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")
    customer = relationship("Customer")
    order = relationship("SalesOrder")


class ServiceTicket(Base):
    __tablename__ = "service_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(60), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
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

