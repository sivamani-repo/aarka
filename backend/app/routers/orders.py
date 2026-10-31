from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commercial import SalesOrder, SalesOrderItem, Payment
from app.schemas.schemas import OrderOut
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/orders", tags=["Sales Orders"])


@router.get("", response_model=List[OrderOut])
def list_orders(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(SalesOrder)
    if status and status != "ALL":
        query = query.filter(SalesOrder.status == status)
    if customer_id:
        query = query.filter(SalesOrder.customer_id == customer_id)

    orders = query.order_by(SalesOrder.id.desc()).all()
    results = []
    for o in orders:
        items = [
            {
                "id": it.id,
                "product_id": it.product_id,
                "product_name": it.product_name,
                "category": it.category,
                "quantity": it.quantity,
                "unit_price": it.unit_price,
                "total_price": it.total_price,
                "is_serialized": it.is_serialized
            }
            for it in o.items
        ]
        payments = [
            {
                "id": p.id,
                "payment_number": p.payment_number,
                "amount": p.amount,
                "method": p.method,
                "reference": p.reference,
                "payment_date": p.payment_date,
                "status": p.status
            }
            for p in o.payments
        ]
        results.append(OrderOut(
            id=o.id,
            order_number=o.order_number,
            quotation_id=o.quotation_id,
            customer_id=o.customer_id,
            package_type=o.package_type,
            capacity_kw=o.capacity_kw,
            hardware_cost=o.hardware_cost,
            installation_cost=o.installation_cost,
            total_amount=o.total_amount,
            advance_paid=o.advance_paid,
            balance_due=o.balance_due,
            delivery_address=o.delivery_address,
            status=o.status,
            picklist_generated=o.picklist_generated,
            customer_name=o.customer.name if o.customer else None,
            customer_phone=o.customer.phone if o.customer else None,
            items=items,
            payments=payments,
            created_at=o.created_at
        ))
    return results


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    o = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")

    items = [
        {
            "id": it.id,
            "product_id": it.product_id,
            "product_name": it.product_name,
            "category": it.category,
            "quantity": it.quantity,
            "unit_price": it.unit_price,
            "total_price": it.total_price,
            "is_serialized": it.is_serialized
        }
        for it in o.items
    ]
    payments = [
        {
            "id": p.id,
            "payment_number": p.payment_number,
            "amount": p.amount,
            "method": p.method,
            "reference": p.reference,
            "payment_date": p.payment_date,
            "status": p.status
        }
        for p in o.payments
    ]

    return OrderOut(
        id=o.id,
        order_number=o.order_number,
        quotation_id=o.quotation_id,
        customer_id=o.customer_id,
        package_type=o.package_type,
        capacity_kw=o.capacity_kw,
        hardware_cost=o.hardware_cost,
        installation_cost=o.installation_cost,
        total_amount=o.total_amount,
        advance_paid=o.advance_paid,
        balance_due=o.balance_due,
        delivery_address=o.delivery_address,
        status=o.status,
        picklist_generated=o.picklist_generated,
        customer_name=o.customer.name if o.customer else None,
        customer_phone=o.customer.phone if o.customer else None,
        items=items,
        payments=payments,
        created_at=o.created_at
    )


@router.post("/{order_id}/reserve-materials")
def reserve_order_materials(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    o = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")

    o.status = "MATERIAL_RESERVED"
    db.commit()
    return {"success": True, "message": f"Materials reserved for order {o.order_number}", "status": o.status}


@router.get("/{order_id}/picklist")
def get_order_picklist(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    o = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")

    serialized_items = [
        {"id": it.id, "product_id": it.product_id, "name": it.product_name, "category": it.category, "quantity": it.quantity}
        for it in o.items if it.is_serialized
    ]
    standard_items = [
        {"id": it.id, "product_id": it.product_id, "name": it.product_name, "category": it.category, "quantity": it.quantity}
        for it in o.items if not it.is_serialized
    ]

    return {
        "order_number": o.order_number,
        "customer_name": o.customer.name if o.customer else None,
        "delivery_address": o.delivery_address,
        "package_type": o.package_type,
        "capacity_kw": o.capacity_kw,
        "serialized_items": serialized_items,
        "standard_items": standard_items
    }

