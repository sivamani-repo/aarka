from sqlalchemy import Column, Integer, String, Boolean, Float, Date, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class InstallationJob(Base):
    __tablename__ = "installations"

    id = Column(Integer, primary_key=True, index=True)
    job_number = Column(String(60), unique=True, index=True, nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    scheduled_date = Column(Date, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(60), default="ASSIGNED")
    capacity_kw = Column(Float, default=3.0)
    checklist_state = Column(Text, default="{}")
    installed_equipment = Column(Text, nullable=True)
    technical_observations = Column(Text, nullable=True)
    customer_signature = Column(Text, nullable=True)
    photo_urls = Column(Text, default="[]")
    testing_results = Column(String(255), default="Grid voltage 238V, Power output verified")
    labour_hours = Column(Float, default=6.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order = relationship("SalesOrder")
    customer = relationship("Customer")
    technician = relationship("Technician")

