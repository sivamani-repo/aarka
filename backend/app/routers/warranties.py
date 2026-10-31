from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.service import WarrantyRecord
from app.models.product import Product
from app.models.customer import Customer
from app.schemas.schemas import WarrantyOut
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/warranties", tags=["Warranty Management"])


@router.get("", response_model=List[WarrantyOut])
def list_warranties(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(WarrantyRecord).join(Product, WarrantyRecord.product_id == Product.id)
    if status and status != "ALL":
        query = query.filter(WarrantyRecord.status == status)
    if customer_id:
        query = query.filter(WarrantyRecord.customer_id == customer_id)

    warranties = query.order_by(WarrantyRecord.id.desc()).all()
    results = []
    today = date.today()

    for w in warranties:
        # Dynamic check for expiry
        calc_status = w.status
        if w.warranty_end and w.warranty_end < today:
            calc_status = "EXPIRED"

        results.append(WarrantyOut(
            id=w.id,
            warranty_number=w.warranty_number,
            serial_number=w.serial_number,
            product_id=w.product_id,
            product_name=w.product.name if w.product else None,
            category=w.product.category if w.product else None,
            customer_id=w.customer_id,
            customer_name=w.customer.name if w.customer else None,
            customer_phone=w.customer.phone if w.customer else None,
            order_id=w.order_id,
            order_number=w.order.order_number if w.order else None,
            delivery_date=w.delivery_date,
            warranty_start=w.warranty_start,
            warranty_end=w.warranty_end,
            status=calc_status,
            coverage_terms=w.coverage_terms,
            created_at=w.created_at
        ))
    return results


@router.get("/search")
def search_warranty(
    query: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clean_q = query.strip()
    search_filter = f"%{clean_q}%"

    records = db.query(WarrantyRecord).join(Customer, WarrantyRecord.customer_id == Customer.id).filter(
        or_(
            WarrantyRecord.serial_number.ilike(search_filter),
            WarrantyRecord.warranty_number.ilike(search_filter),
            Customer.name.ilike(search_filter),
            Customer.phone.ilike(search_filter)
        )
    ).all()

    today = date.today()
    results = []
    for w in records:
        is_active = w.warranty_start <= today <= w.warranty_end
        status = "COVERED" if is_active else ("EXPIRED" if today > w.warranty_end else "NOT_YET_ACTIVE")
        days_remaining = max(0, (w.warranty_end - today).days) if is_active else 0

        results.append({
            "warranty_number": w.warranty_number,
            "serial_number": w.serial_number,
            "product_name": w.product.name if w.product else "",
            "category": w.product.category if w.product else "",
            "customer_name": w.customer.name if w.customer else "",
            "customer_phone": w.customer.phone if w.customer else "",
            "warranty_start": w.warranty_start,
            "warranty_end": w.warranty_end,
            "days_remaining": days_remaining,
            "status": status,
            "coverage_terms": w.coverage_terms
        })

    return {
        "query": clean_q,
        "count": len(results),
        "results": results
    }

