from sqlalchemy import Column, Integer, String, Boolean, Float, Date, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=False)
    email = Column(String(150), nullable=True)
    address = Column(Text, nullable=True)
    category = Column(String(80), default="Solar Panels & Inverters")
    lead_time_days = Column(Integer, default=7)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    sku = Column(String(80), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, nullable=False, default=0)
    reorder_level = Column(Integer, default=5)
    unit_price = Column(Float, default=0.0)
    warehouse_location = Column(String(120), default="Main Warehouse - Hall 1")
    supplier = Column(String(120), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product = relationship("Product", back_populates="inventory_item")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    movement_type = Column(String(60), nullable=False)
    quantity = Column(Integer, nullable=False)
    reference_type = Column(String(60), nullable=True)
    reference_id = Column(String(80), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")


class Dispatch(Base):
    __tablename__ = "dispatches"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    delivery_reference = Column(String(80), unique=True, index=True, nullable=False)
    dispatch_date = Column(Date, nullable=True)
    delivery_date = Column(Date, nullable=True)
    status = Column(String(60), default="DISPATCHED")
    customer_confirmed = Column(Boolean, default=False)
    delivery_proof_url = Column(Text, nullable=True)
    dispatched_by = Column(String(100), nullable=True)
    serial_numbers = Column(Text, default="[]")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("SalesOrder")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])


class SerializedEquipment(Base):
    __tablename__ = "serialized_equipment"

    id = Column(Integer, primary_key=True, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    serial_number = Column(String(120), unique=True, index=True, nullable=False)
    status = Column(String(60), default="AVAILABLE")
    supplier = Column(String(120), nullable=True)
    purchase_reference = Column(String(120), nullable=True)
    current_location = Column(String(120), default="Warehouse - Rack S1")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    dispatch_id = Column(Integer, ForeignKey("dispatches.id"), nullable=True)
    installation_id = Column(Integer, nullable=True)
    dispatch_date = Column(Date, nullable=True)
    warranty_start = Column(Date, nullable=True)
    warranty_end = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")
    customer = relationship("Customer")
    order = relationship("SalesOrder")
    dispatch = relationship("Dispatch")
