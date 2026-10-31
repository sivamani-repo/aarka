from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    sku = Column(String(80), unique=True, index=True, nullable=False)
    category = Column(String(80), nullable=False)
    manufacturer = Column(String(100), default="Aarka Tech")
    model = Column(String(100), nullable=True)
    unit = Column(String(30), default="nos")
    capacity_kw = Column(Float, nullable=True)
    system_type = Column(String(50), default="Both")
    purchase_price = Column(Float, nullable=False, default=0.0)
    selling_price = Column(Float, nullable=False, default=0.0)
    min_stock = Column(Integer, default=5)
    warranty_months = Column(Integer, default=24)
    requires_serial = Column(Boolean, default=False)
    warehouse_location = Column(String(100), default="Rack A-1")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inventory_item = relationship("InventoryItem", back_populates="product", uselist=False)


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    package_type = Column(String(60), nullable=False)
    capacity_kw = Column(Float, nullable=False)
    base_price = Column(Float, nullable=False, default=0.0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BOMTemplate(Base):
    __tablename__ = "bom_templates"

    id = Column(Integer, primary_key=True, index=True)
    package_type = Column(String(60), nullable=False)
    capacity_kw = Column(Float, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    is_mandatory = Column(Boolean, default=True)
    notes = Column(String(200), nullable=True)

    product = relationship("Product")

