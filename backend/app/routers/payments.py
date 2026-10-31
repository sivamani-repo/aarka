import random
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commercial import SalesOrder, Payment
from app.models.customer import Customer
from app.schemas.schemas import PaymentCreate, PaymentOut
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/payments", tags=["Payments & Accounts Receivable"])


@router.get("", response_model=List[PaymentOut])
def list_payments(
    order_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Payment)
    if order_id:
        query = query.filter(Payment.order_id == order_id)
    if customer_id:
        query = query.filter(Payment.customer_id == customer_id)

    payments = query.order_by(Payment.id.desc()).all()
    results = []
    for p in payments:
        results.append(PaymentOut(
            id=p.id,
            payment_number=p.payment_number,
            order_id=p.order_id,
            customer_id=p.customer_id,
            amount=p.amount,
            method=p.method,
            reference=p.reference,
            payment_date=p.payment_date,
            verified_status=p.verified_status,
            status=p.status,
            notes=p.notes,
            customer_name=p.customer.name if p.customer else None,
            order_number=p.order.order_number if p.order else None,
            created_at=p.created_at
        ))
    return results


@router.post("", response_model=PaymentOut)
def record_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(SalesOrder).filter(SalesOrder.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than zero")

    # CRITICAL BUSINESS RULE #16: Payment totals cannot exceed payable totals without an authorized credit or refund process
    current_paid = order.advance_paid or 0.0
    total_payable = order.total_amount or 0.0
    if current_paid + payload.amount > total_payable + 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Business Rule Violation: Payment amount of ₹{payload.amount} exceeds the balance due of ₹{order.balance_due}. Total payments cannot exceed the payable total without authorized credit."
        )

    pay_num = f"PAY-2026-{random.randint(1000, 9999)}"
    while db.query(Payment).filter(Payment.payment_number == pay_num).first():
        pay_num = f"PAY-2026-{random.randint(1000, 9999)}"

    payment = Payment(
        payment_number=pay_num,
        order_id=order.id,
        customer_id=order.customer_id,
        amount=payload.amount,
        method=payload.method,
        reference=payload.reference or f"UPI-REF-{random.randint(100000, 999999)}",
        payment_date=payload.payment_date or date.today(),
        verified_status="VERIFIED",
        status="COMPLETED",
        notes=payload.notes or f"Payment recorded by {current_user.name}"
    )
    db.add(payment)

    # Update order financial status
    new_advance_paid = round(current_paid + payload.amount, 2)
    new_balance_due = max(0.0, round(total_payable - new_advance_paid, 2))
    order.advance_paid = new_advance_paid
    order.balance_due = new_balance_due

    # If advance is now >= 20% or initial advance paid, transition order to READY_FOR_DISPATCH if still CONFIRMED
    if order.status == "CONFIRMED" and new_advance_paid > 0:
        order.status = "READY_FOR_DISPATCH"

    db.commit()
    db.refresh(payment)

    return PaymentOut(
        id=payment.id,
        payment_number=payment.payment_number,
        order_id=payment.order_id,
        customer_id=payment.customer_id,
        amount=payment.amount,
        method=payment.method,
        reference=payment.reference,
        payment_date=payment.payment_date,
        verified_status=payment.verified_status,
        status=payment.status,
        notes=payment.notes,
        customer_name=order.customer.name if order.customer else None,
        order_number=order.order_number,
        created_at=payment.created_at
    )

