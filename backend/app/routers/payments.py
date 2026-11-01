from typing import List, Optional
from datetime import date
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.commercial import SalesOrder, Payment
from app.models.finance import Invoice
from app.schemas.schemas import PaymentCreate, PaymentOut, PaymentVerification
from app.core.permissions import get_current_user
from app.core.rbac import APPROVE, has_permission
from app.models.user import AuditLog, User

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
    order = (
        db.query(SalesOrder)
        .filter(SalesOrder.id == payload.order_id)
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if payload.customer_id != order.customer_id:
        raise HTTPException(status_code=400, detail="Customer does not match the sales order.")

    clean_ref = payload.reference.strip() if payload.reference else None
    clean_ref = clean_ref or None
    if clean_ref:
        dup_payment = db.query(Payment).filter(Payment.order_id == order.id, Payment.reference == clean_ref).first()
        if dup_payment:
            raise HTTPException(
                status_code=400,
                detail=f"A transaction with reference '{clean_ref}' has already been recorded for this order ({dup_payment.payment_number})."
            )

    confirmed_total = (
        db.query(func.coalesce(func.sum(Payment.amount), 0.0))
        .filter(
            Payment.order_id == order.id,
            Payment.status == "COMPLETED",
            Payment.verified_status == "VERIFIED",
        )
        .scalar()
    )
    pending_total = (
        db.query(func.coalesce(func.sum(Payment.amount), 0.0))
        .filter(Payment.order_id == order.id, Payment.status == "PENDING")
        .scalar()
    )
    current_paid = max(order.advance_paid or 0.0, confirmed_total or 0.0)
    total_payable = order.total_amount or 0.0
    if current_paid + pending_total + payload.amount > total_payable + 0.01:
        raise HTTPException(
            status_code=409,
            detail="Payment exceeds the remaining order balance after pending and confirmed payments.",
        )
    if current_paid + pending_total == 0 and payload.amount < total_payable * 0.10:
        raise HTTPException(
            status_code=400,
            detail="The initial advance payment must be at least 10% of the order total.",
        )

    payment_number = f"PAY-{date.today().year}-{uuid4().hex[:12].upper()}"
    payment = Payment(
        payment_number=payment_number,
        order_id=order.id,
        customer_id=order.customer_id,
        amount=round(payload.amount, 2),
        method=payload.method,
        reference=clean_ref,
        payment_date=payload.payment_date or date.today(),
        verified_status="PENDING",
        status="PENDING",
        notes=payload.notes,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    invoice = db.query(Invoice).filter(Invoice.order_id == order.id).first()

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
        invoice_number=invoice.invoice_number if invoice else None,
        remaining_balance=order.balance_due,
        created_at=payment.created_at
    )


@router.post("/{payment_id}/verify", response_model=PaymentOut)
def verify_payment(
    payment_id: int,
    payload: PaymentVerification,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not has_permission(db, current_user, "payments", APPROVE):
        raise HTTPException(status_code=403, detail="Payment approval permission is required.")

    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .with_for_update()
        .first()
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment record not found")
    if payment.status != "PENDING" or payment.verified_status == "VERIFIED":
        raise HTTPException(status_code=409, detail="Only pending payments can be verified.")

    order = (
        db.query(SalesOrder)
        .filter(SalesOrder.id == payment.order_id)
        .with_for_update()
        .first()
    )
    if order is None:
        raise HTTPException(status_code=409, detail="Payment order is unavailable.")

    completed_total = (
        db.query(func.coalesce(func.sum(Payment.amount), 0.0))
        .filter(
            Payment.order_id == order.id,
            Payment.status == "COMPLETED",
            Payment.verified_status == "VERIFIED",
        )
        .scalar()
    )
    current_paid = max(order.advance_paid or 0.0, completed_total or 0.0)
    if current_paid + payment.amount > (order.total_amount or 0.0) + 0.01:
        raise HTTPException(
            status_code=409,
            detail="Payment can no longer be verified because it exceeds the remaining order balance.",
        )

    payment.status = "COMPLETED"
    payment.verified_status = "VERIFIED"
    payment.notes = "\n".join(
        note for note in (payment.notes, f"Verified by {current_user.name}: {payload.confirmation_note.strip()}") if note
    )
    order.advance_paid = round(current_paid + payment.amount, 2)
    order.balance_due = max(0.0, round(order.total_amount - order.advance_paid, 2))
    if (
        order.status == "CONFIRMED"
        and order.advance_paid >= order.total_amount * 0.10
    ):
        order.status = "READY_FOR_DISPATCH"

    invoice = db.query(Invoice).filter(Invoice.order_id == order.id).first()
    if invoice:
        invoice.paid_amount = order.advance_paid
        invoice.balance_due = max(0.0, round(invoice.total_amount - invoice.paid_amount, 2))
        invoice.status = (
            "PAID" if invoice.balance_due <= 0
            else "PARTIALLY_PAID" if invoice.paid_amount > 0
            else invoice.status
        )

    db.add(
        AuditLog(
            user_id=current_user.id,
            action="VERIFY",
            entity_type="payment",
            entity_id=payment.id,
            details=f"Payment verification: {payload.confirmation_note.strip()}",
        )
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Payment verification conflicted with another update.") from exc
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
        invoice_number=invoice.invoice_number if invoice else None,
        remaining_balance=order.balance_due,
        created_at=payment.created_at,
    )
