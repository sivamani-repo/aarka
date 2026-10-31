from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.commercial import SalesOrder, Payment
from app.models.finance import ProjectExpense, Invoice
from app.schemas.schemas import ExpenseCreate, ExpenseOut, ProjectProfitabilityOut
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/finance", tags=["Finance & Project Profitability"])


@router.get("/overview")
def get_finance_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orders = db.query(SalesOrder).all()
    total_revenue = sum(o.total_amount for o in orders)
    cash_received = sum(o.advance_paid for o in orders)
    outstanding_receivables = sum(o.balance_due for o in orders)

    expenses = db.query(ProjectExpense).all()
    total_expenses = sum(e.amount for e in expenses)

    # Calculate hardware and labour costs from orders
    total_hardware_cost = sum(o.hardware_cost for o in orders)
    total_labour_cost = sum(o.installation_cost for o in orders)

    total_recorded_costs = total_hardware_cost + total_labour_cost + total_expenses
    gross_margin = total_revenue - total_recorded_costs
    gross_margin_pct = round((gross_margin / total_revenue * 100), 2) if total_revenue > 0 else 0.0

    return {
        "total_revenue": round(total_revenue, 2),
        "cash_received": round(cash_received, 2),
        "outstanding_receivables": round(outstanding_receivables, 2),
        "total_recorded_costs": round(total_recorded_costs, 2),
        "hardware_cost": round(total_hardware_cost, 2),
        "labour_cost": round(total_labour_cost, 2),
        "operating_expenses": round(total_expenses, 2),
        "gross_margin": round(gross_margin, 2),
        "gross_margin_percentage": gross_margin_pct
    }


@router.get("/project-profitability", response_model=List[ProjectProfitabilityOut])
def get_project_profitability(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orders = db.query(SalesOrder).order_by(SalesOrder.id.desc()).all()
    results = []

    for o in orders:
        expenses = db.query(ProjectExpense).filter(ProjectExpense.order_id == o.id).all()
        transport_cost = sum(e.amount for e in expenses if e.category == "TRANSPORTATION")
        other_exp = sum(e.amount for e in expenses if e.category not in ["TRANSPORTATION", "LABOUR", "HARDWARE"])

        hw_cost = o.hardware_cost or 0.0
        labour_cost = o.installation_cost or 0.0
        total_cost = hw_cost + labour_cost + transport_cost + other_exp
        gross_margin = o.total_amount - total_cost
        margin_pct = round((gross_margin / o.total_amount * 100), 2) if o.total_amount > 0 else 0.0

        results.append(ProjectProfitabilityOut(
            order_id=o.id,
            order_number=o.order_number,
            customer_name=o.customer.name if o.customer else "Customer",
            capacity_kw=o.capacity_kw,
            package_type=o.package_type or "On-Grid System",
            recognized_revenue=o.total_amount,
            advance_paid=o.advance_paid,
            balance_due=o.balance_due,
            hardware_cost=round(hw_cost, 2),
            labour_cost=round(labour_cost, 2),
            transportation_cost=round(transport_cost, 2),
            other_expenses=round(other_exp, 2),
            total_cost=round(total_cost, 2),
            gross_margin=round(gross_margin, 2),
            gross_margin_percentage=margin_pct,
            status=o.status
        ))
    return results


@router.get("/expenses", response_model=List[ExpenseOut])
def list_expenses(
    order_id: Optional[int] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ProjectExpense)
    if order_id:
        query = query.filter(ProjectExpense.order_id == order_id)
    if category and category != "ALL":
        query = query.filter(ProjectExpense.category == category)

    expenses = query.order_by(ProjectExpense.id.desc()).all()
    results = []
    for e in expenses:
        results.append(ExpenseOut(
            id=e.id,
            order_id=e.order_id,
            category=e.category,
            amount=e.amount,
            description=e.description,
            expense_date=e.expense_date,
            recorded_by=e.recorded_by,
            created_at=e.created_at
        ))
    return results


@router.post("/expenses", response_model=ExpenseOut)
def record_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = ProjectExpense(
        order_id=payload.order_id,
        category=payload.category,
        amount=payload.amount,
        description=payload.description,
        expense_date=payload.expense_date or date.today(),
        recorded_by=current_user.name
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)

    return ExpenseOut(
        id=exp.id,
        order_id=exp.order_id,
        category=exp.category,
        amount=exp.amount,
        description=exp.description,
        expense_date=exp.expense_date,
        recorded_by=exp.recorded_by,
        created_at=exp.created_at
    )


@router.get("/invoices")
def list_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoices = db.query(Invoice).order_by(Invoice.id.desc()).all()
    return [
        {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "order_id": inv.order_id,
            "order_number": inv.order.order_number if inv.order else "",
            "customer_name": inv.customer.name if inv.customer else "",
            "customer_phone": inv.customer.phone if inv.customer else "",
            "total_amount": inv.total_amount,
            "paid_amount": inv.paid_amount,
            "balance_due": inv.balance_due,
            "status": inv.status,
            "due_date": inv.due_date,
            "created_at": inv.created_at
        }
        for inv in invoices
    ]

