from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class ProjectExpense(Base):
    __tablename__ = "project_expenses"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    category = Column(String(80), nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    gst_amount = Column(Float, default=0.0)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    vendor_name = Column(String(150), nullable=True)
    invoice_reference = Column(String(100), nullable=True)
    payment_method = Column(String(50), default="BANK_TRANSFER")
    approval_status = Column(String(50), default="APPROVED")
    document_url = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    expense_date = Column(Date, nullable=True)
    recorded_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("SalesOrder")
    supplier = relationship("Supplier")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(60), unique=True, index=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    subtotal = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.138)  # 13.8% composite solar GST
    tax_amount = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    balance_due = Column(Float, default=0.0)
    status = Column(String(50), default="UNPAID")
    due_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    items_json = Column(Text, default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order = relationship("SalesOrder")
    customer = relationship("Customer")
