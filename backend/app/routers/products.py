from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product, Package
from app.models.inventory import InventoryItem
from app.schemas.schemas import ProductCreate, ProductOut, PackageOut
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/products", tags=["Products & Catalogue"])


@router.get("", response_model=List[ProductOut])
def list_products(
    category: Optional[str] = None,
    requires_serial: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Product)
    if category and category != "ALL":
        query = query.filter(Product.category == category)
    if requires_serial is not None:
        query = query.filter(Product.requires_serial == requires_serial)

    products = query.order_by(Product.category.asc(), Product.name.asc()).all()
    results = []
    for p in products:
        p_out = ProductOut.from_orm(p)
        inv = db.query(InventoryItem).filter(InventoryItem.product_id == p.id).first()
        p_out.stock_quantity = inv.quantity if inv else 0
        results.append(p_out)
    return results


@router.post("", response_model=ProductOut)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Product).filter(Product.sku == payload.sku.strip().upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")

    product = Product(
        name=payload.name.strip(),
        sku=payload.sku.strip().upper(),
        category=payload.category,
        manufacturer=payload.manufacturer,
        model=payload.model,
        unit=payload.unit,
        capacity_kw=payload.capacity_kw,
        system_type=payload.system_type,
        purchase_price=payload.purchase_price,
        selling_price=payload.selling_price,
        min_stock=payload.min_stock,
        warranty_months=payload.warranty_months,
        requires_serial=payload.requires_serial,
        warehouse_location=payload.warehouse_location,
        description=payload.description
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # Initialize inventory item balance record
    inv = InventoryItem(
        product_id=product.id,
        sku=product.sku,
        quantity=0,
        reserved_quantity=0,
        reorder_level=product.min_stock,
        unit_price=product.purchase_price,
        warehouse_location=product.warehouse_location,
        supplier=product.manufacturer,
        description=f"Stock record for {product.name}"
    )
    db.add(inv)
    db.commit()

    p_out = ProductOut.from_orm(product)
    p_out.stock_quantity = 0
    return p_out


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.name = payload.name.strip()
    product.sku = payload.sku.strip().upper()
    product.category = payload.category
    product.manufacturer = payload.manufacturer
    product.model = payload.model
    product.unit = payload.unit
    product.capacity_kw = payload.capacity_kw
    product.system_type = payload.system_type
    product.purchase_price = payload.purchase_price
    product.selling_price = payload.selling_price
    product.min_stock = payload.min_stock
    product.warranty_months = payload.warranty_months
    product.requires_serial = payload.requires_serial
    product.warehouse_location = payload.warehouse_location
    product.description = payload.description

    db.commit()
    db.refresh(product)

    inv = db.query(InventoryItem).filter(InventoryItem.product_id == product.id).first()
    p_out = ProductOut.from_orm(product)
    p_out.stock_quantity = inv.quantity if inv else 0
    return p_out


@router.get("/packages", response_model=List[PackageOut])
def list_packages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    packages = db.query(Package).order_by(Package.capacity_kw.asc(), Package.package_type.asc()).all()
    return packages

