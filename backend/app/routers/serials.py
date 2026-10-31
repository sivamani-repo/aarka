from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.inventory import SerializedEquipment, InventoryItem
from app.models.product import Product
from app.models.commercial import SalesOrder
from app.models.customer import Customer
from app.models.service import WarrantyRecord, ServiceTicket
from app.schemas.schemas import SerialCreate, SerialScanRequest, SerialOut
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/serials", tags=["Serial Numbers & Barcode Tracking"])


@router.get("", response_model=List[SerialOut])
def list_serials(
    search: Optional[str] = None,
    product_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(SerializedEquipment).join(Product, SerializedEquipment.product_id == Product.id)
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                SerializedEquipment.serial_number.ilike(search_filter),
                Product.name.ilike(search_filter),
                SerializedEquipment.supplier.ilike(search_filter)
            )
        )
    if product_id:
        query = query.filter(SerializedEquipment.product_id == product_id)
    if status and status != "ALL":
        query = query.filter(SerializedEquipment.status == status)

    serials = query.order_by(SerializedEquipment.id.desc()).all()
    results = []
    for s in serials:
        results.append(SerialOut(
            id=s.id,
            serial_number=s.serial_number,
            product_id=s.product_id,
            product_name=s.product.name if s.product else None,
            category=s.product.category if s.product else None,
            status=s.status,
            supplier=s.supplier,
            purchase_reference=s.purchase_reference,
            current_location=s.current_location,
            customer_id=s.customer_id,
            customer_name=s.customer.name if s.customer else None,
            order_id=s.order_id,
            order_number=s.order.order_number if s.order else None,
            dispatch_date=s.dispatch_date,
            warranty_start=s.warranty_start,
            warranty_end=s.warranty_end,
            created_at=s.created_at
        ))
    return results


@router.post("", response_model=SerialOut)
def register_serial(
    payload: SerialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clean_sn = payload.serial_number.strip().upper()
    # CRITICAL BUSINESS RULE #5: Prevent duplicate serial numbers
    existing = db.query(SerializedEquipment).filter(SerializedEquipment.serial_number == clean_sn).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Business Rule Violation: Serial number '{clean_sn}' is already registered in the system. Duplicates are strictly prohibited."
        )

    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    ser = SerializedEquipment(
        product_id=product.id,
        serial_number=clean_sn,
        status="AVAILABLE",
        supplier=payload.supplier or product.manufacturer,
        purchase_reference=payload.purchase_reference or "PO-INWARD",
        current_location=payload.current_location or product.warehouse_location
    )
    db.add(ser)
    db.commit()
    db.refresh(ser)

    return SerialOut(
        id=ser.id,
        serial_number=ser.serial_number,
        product_id=ser.product_id,
        product_name=product.name,
        category=product.category,
        status=ser.status,
        supplier=ser.supplier,
        purchase_reference=ser.purchase_reference,
        current_location=ser.current_location,
        created_at=ser.created_at
    )


@router.post("/scan")
def scan_serial_barcode(
    payload: SerialScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clean_code = payload.barcode.strip().upper()
    ser = db.query(SerializedEquipment).filter(SerializedEquipment.serial_number == clean_code).first()
    if not ser:
        raise HTTPException(
            status_code=404,
            detail=f"Serial Number '{clean_code}' not found in warehouse inventory records."
        )

    order = None
    if payload.order_id:
        order = db.query(SalesOrder).filter(SalesOrder.id == payload.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # CRITICAL BUSINESS RULE #5: A serial cannot be allocated to multiple customers simultaneously
        if ser.status in ["DISPATCHED", "INSTALLED"]:
            raise HTTPException(
                status_code=400,
                detail=f"Business Rule Violation: Serial {clean_code} is already {ser.status} to Customer '{ser.customer.name if ser.customer else 'Another customer'}'. It cannot be reallocated."
            )

        if ser.order_id and ser.order_id != payload.order_id:
            raise HTTPException(
                status_code=400,
                detail=f"Business Rule Violation: Serial {clean_code} is already allocated to Order '{ser.order.order_number if ser.order else ser.order_id}'."
            )

    return {
        "valid": True,
        "serial_number": ser.serial_number,
        "product_id": ser.product_id,
        "product_name": ser.product.name if ser.product else "",
        "category": ser.product.category if ser.product else "",
        "status": ser.status,
        "current_location": ser.current_location,
        "supplier": ser.supplier,
        "is_available": ser.status in ["AVAILABLE", "RECEIVED"] or (payload.order_id and ser.order_id == payload.order_id)
    }


@router.get("/history/{serial_number}")
def get_serial_history(
    serial_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clean_sn = serial_number.strip().upper()
    ser = db.query(SerializedEquipment).filter(SerializedEquipment.serial_number == clean_sn).first()
    if not ser:
        raise HTTPException(status_code=404, detail=f"Serial Number {clean_sn} not found")

    warranties = db.query(WarrantyRecord).filter(WarrantyRecord.serial_number == clean_sn).all()
    tickets = db.query(ServiceTicket).filter(ServiceTicket.serial_number == clean_sn).all()

    return {
        "serial_number": ser.serial_number,
        "product": {
            "id": ser.product.id if ser.product else None,
            "name": ser.product.name if ser.product else "",
            "category": ser.product.category if ser.product else "",
            "sku": ser.product.sku if ser.product else "",
            "manufacturer": ser.supplier or (ser.product.manufacturer if ser.product else "")
        },
        "status": ser.status,
        "warehouse_location": ser.current_location,
        "order": {
            "id": ser.order.id if ser.order else None,
            "order_number": ser.order.order_number if ser.order else None,
            "customer_name": ser.customer.name if ser.customer else None,
            "customer_phone": ser.customer.phone if ser.customer else None
        } if ser.order else None,
        "dispatch_date": ser.dispatch_date,
        "warranties": [
            {
                "id": w.id,
                "warranty_number": w.warranty_number,
                "status": w.status,
                "start": w.warranty_start,
                "end": w.warranty_end,
                "terms": w.coverage_terms
            }
            for w in warranties
        ],
        "service_tickets": [
            {
                "id": t.id,
                "ticket_number": t.ticket_number,
                "fault": t.fault_description,
                "status": t.status,
                "warranty_status": t.warranty_status,
                "reported_date": t.reported_date
            }
            for t in tickets
        ]
    }

