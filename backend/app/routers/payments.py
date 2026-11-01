import random
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.commercial import SalesOrder, Payment
from app.models.customer import Customer
from app.models.finance import Invoice
from app.schemas.schemas import PaymentCreate, PaymentOut
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/payments", tags=["Payments & Accounts Receivable"])


@router.get("", response_model=List[PaymentOut])
def list_payments(
    order_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    method: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Payment)
    if order_id:
        query = query.filter(Payment.order_id == order_id)
    if customer_id:
        query = query.filter(Payment.customer_id == customer_id)
    if method and method != "ALL":
        query = query.filter(Payment.method == method)
    if start_date:
        query = query.filter(Payment.payment_date >= start_date)
    if end_date:
        query = query.filter(Payment.payment_date <= end_date)
    if search:
        s = f"%{search}%"
        query = query.filter(or_(
            Payment.payment_number.ilike(s),
            Payment.reference.ilike(s)
        ))

    payments = query.order_by(Payment.id.desc()).all()
    results = []
    for p in payments:
        inv = db.query(Invoice).filter(Invoice.order_id == p.order_id).first()
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
            invoice_number=inv.invoice_number if inv else None,
            remaining_balance=p.order.balance_due if p.order else 0.0,
            created_at=p.created_at
        ))
    return results


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment_details(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment record not found")

    inv = db.query(Invoice).filter(Invoice.order_id == p.order_id).first()
    return PaymentOut(
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
        invoice_number=inv.invoice_number if inv else None,
        remaining_balance=p.order.balance_due if p.order else 0.0,
        created_at=p.created_at
    )


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

    # Prevent duplicate payment reference submission on the same order
    clean_ref = payload.reference.strip() if payload.reference else None
    if clean_ref:
        dup_payment = db.query(Payment).filter(Payment.order_id == order.id, Payment.reference == clean_ref).first()
        if dup_payment:
            raise HTTPException(
                status_code=400,
                detail=f"A transaction with reference '{clean_ref}' has already been recorded for this order ({dup_payment.payment_number})."
            )

    # CRITICAL BUSINESS RULE #16: Payment totals cannot exceed payable totals without an authorized credit or refund process
    current_paid = order.advance_paid or 0.0
    total_payable = order.total_amount or 0.0
    if current_paid + payload.amount > total_payable + 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Business Rule Violation: Payment amount of ₹{payload.amount} exceeds the balance due of ₹{order.balance_due}. Total payments cannot exceed the payable total without authorized credit."
        )

    year = date.today().year
    pay_num = f"PAY-{year}-{random.randint(1000, 9999)}"
    while db.query(Payment).filter(Payment.payment_number == pay_num).first():
        pay_num = f"PAY-{year}-{random.randint(1000, 9999)}"

    gen_ref = clean_ref or f"UPI-REF-{random.randint(100000, 999999)}"

    payment = Payment(
        payment_number=pay_num,
        order_id=order.id,
        customer_id=order.customer_id,
        amount=round(payload.amount, 2),
        method=payload.method,
        reference=gen_ref,
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

    # Synchronize with linked Invoice if present
    inv = db.query(Invoice).filter(Invoice.order_id == order.id).first()
    if inv:
        inv.paid_amount = round((inv.paid_amount or 0.0) + payload.amount, 2)
        inv.balance_due = max(0.0, round(inv.total_amount - inv.paid_amount, 2))
        if inv.balance_due <= 0:
            inv.status = "PAID"
        elif inv.paid_amount > 0:
            inv.status = "PARTIALLY_PAID"

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
        invoice_number=inv.invoice_number if inv else None,
        remaining_balance=order.balance_due,
        created_at=payment.created_at
    )
