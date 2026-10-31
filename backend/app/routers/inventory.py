from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory import InventoryItem, StockMovement, SerializedEquipment
from app.models.product import Product
from app.schemas.schemas import InventoryItemOut, StockReceiveRequest, StockAdjustmentRequest
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/inventory", tags=["Warehouse & Inventory"])


@router.get("", response_model=List[InventoryItemOut])
def list_inventory(
    low_stock_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(InventoryItem).join(Product, InventoryItem.product_id == Product.id)
    if low_stock_only:
        query = query.filter(InventoryItem.quantity <= InventoryItem.reorder_level)

    items = query.order_by(Product.category.asc(), Product.name.asc()).all()
    results = []
    for it in items:
        prod = it.product
        results.append(InventoryItemOut(
            id=it.id,
            product_id=it.product_id,
            product_name=prod.name if prod else "",
            sku=it.sku,
            category=prod.category if prod else "",
            quantity=it.quantity,
            reserved_quantity=it.reserved_quantity,
            available_quantity=max(0, it.quantity - it.reserved_quantity),
            reorder_level=it.reorder_level,
            unit_price=it.unit_price,
            total_valuation=round(it.quantity * it.unit_price, 2),
            warehouse_location=it.warehouse_location,
            supplier=it.supplier
        ))
    return results


@router.post("/receive")
def receive_stock(
    payload: StockReceiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")

    inv = db.query(InventoryItem).filter(InventoryItem.product_id == product.id).first()
    if not inv:
        inv = InventoryItem(
            product_id=product.id,
            sku=product.sku,
            quantity=payload.quantity,
            reserved_quantity=0,
            reorder_level=product.min_stock,
            unit_price=payload.unit_price or product.purchase_price,
            warehouse_location=payload.warehouse_location or product.warehouse_location,
            supplier=payload.supplier or product.manufacturer
        )
        db.add(inv)
    else:
        inv.quantity += payload.quantity
        if payload.unit_price:
            inv.unit_price = payload.unit_price
        if payload.warehouse_location:
            inv.warehouse_location = payload.warehouse_location

    # Record StockMovement
    movement = StockMovement(
        product_id=product.id,
        movement_type="RECEIVED",
        quantity=payload.quantity,
        reference_type="PURCHASE_RECEIPT",
        reference_id=payload.purchase_reference or "GRN-2026-INWARD",
        notes=f"Received {payload.quantity} units from {payload.supplier or product.manufacturer}"
    )
    db.add(movement)

    # If product requires serial numbers and serials are provided, create SerializedEquipment records
    if product.requires_serial and payload.serial_numbers:
        for sn in payload.serial_numbers:
            clean_sn = sn.strip().upper()
            existing_sn = db.query(SerializedEquipment).filter(SerializedEquipment.serial_number == clean_sn).first()
            if existing_sn:
                raise HTTPException(status_code=400, detail=f"Duplicate Serial Number: {clean_sn} already exists in database")
            ser = SerializedEquipment(
                inventory_item_id=inv.id,
                product_id=product.id,
                serial_number=clean_sn,
                status="AVAILABLE",
                supplier=payload.supplier or product.manufacturer,
                purchase_reference=payload.purchase_reference,
                current_location=payload.warehouse_location or product.warehouse_location
            )
            db.add(ser)

    db.commit()
    return {
        "success": True,
        "message": f"Successfully received {payload.quantity} units of {product.name}",
        "new_stock": inv.quantity
    }


@router.post("/adjust")
def adjust_stock(
    payload: StockAdjustmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    inv = db.query(InventoryItem).filter(InventoryItem.product_id == product.id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found")

    # CRITICAL BUSINESS RULE #6: Inventory cannot become negative
    if inv.quantity + payload.quantity_delta < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Business Rule Violation: Adjustment of {payload.quantity_delta} would result in negative inventory ({inv.quantity + payload.quantity_delta}). Negative stock is strictly prohibited."
        )

    inv.quantity += payload.quantity_delta

    movement = StockMovement(
        product_id=product.id,
        movement_type="ADJUSTMENT",
        quantity=payload.quantity_delta,
        reference_type="STOCK_ADJUSTMENT",
        notes=payload.reason
    )
    db.add(movement)
    db.commit()

    return {"success": True, "new_stock": inv.quantity}


@router.get("/movements")
def list_stock_movements(
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(StockMovement).join(Product, StockMovement.product_id == Product.id)
    if product_id:
        query = query.filter(StockMovement.product_id == product_id)

    movements = query.order_by(StockMovement.id.desc()).limit(100).all()
    return [
        {
            "id": m.id,
            "product_id": m.product_id,
            "product_name": m.product.name if m.product else "",
            "sku": m.product.sku if m.product else "",
            "movement_type": m.movement_type,
            "quantity": m.quantity,
            "reference_type": m.reference_type,
            "reference_id": m.reference_id,
            "notes": m.notes,
            "created_at": m.created_at
        }
        for m in movements
    ]

