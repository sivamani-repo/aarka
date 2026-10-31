from sqlalchemy import Column, Integer, String, Boolean, Float, Date, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    quotation_number = Column(String(60), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    survey_id = Column(Integer, ForeignKey("site_surveys.id"), nullable=True)
    package_type = Column(String(60), nullable=False, default="On-Grid System")
    capacity_kw = Column(Float, nullable=False, default=3.0)
    system_type = Column(String(50), default="On-Grid")
    hardware_cost = Column(Float, default=0.0)
    installation_cost = Column(Float, default=0.0)
    additional_expenses = Column(Float, default=0.0)
    subtotal = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.18)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    advance_amount = Column(Float, default=0.0)
    balance_amount = Column(Float, default=0.0)
    valid_until = Column(Date, nullable=True)
    terms_conditions = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(60), default="DRAFT")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer")
    lead = relationship("Lead")
    survey = relationship("SiteSurvey")
    items = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")


class QuotationItem(Base):
    __tablename__ = "quotation_items"

    id = Column(Integer, primary_key=True, index=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(150), nullable=False)
    category = Column(String(80), nullable=True)
    sku = Column(String(80), nullable=True)
    quantity = Column(Float, nullable=False, default=1.0)
    unit = Column(String(30), default="nos")
    unit_price = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)
    is_serialized = Column(Boolean, default=False)

    quotation = relationship("Quotation", back_populates="items")
    product = relationship("Product")


class SalesOrder(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(60), unique=True, index=True, nullable=False)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    package_type = Column(String(60), nullable=True)
    capacity_kw = Column(Float, default=3.0)
    hardware_cost = Column(Float, default=0.0)
    installation_cost = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)
    advance_paid = Column(Float, nullable=False, default=0.0)
    balance_due = Column(Float, nullable=False, default=0.0)
    delivery_address = Column(Text, nullable=True)
    status = Column(String(60), default="CONFIRMED")
    picklist_generated = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer")
    quotation = relationship("Quotation")
    items = relationship("SalesOrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order")


class SalesOrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(150), nullable=False)
    category = Column(String(80), nullable=True)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)
    is_serialized = Column(Boolean, default=False)

    order = relationship("SalesOrder", back_populates="items")
    product = relationship("Product")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(60), unique=True, index=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    method = Column(String(50), default="UPI")
    reference = Column(String(120), nullable=True)
    payment_date = Column(Date, nullable=True)
    verified_status = Column(String(60), default="VERIFIED")
    status = Column(String(60), default="COMPLETED")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("SalesOrder", back_populates="payments")
    customer = relationship("Customer")

