import json
import random
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.database import get_db
from app.models.commercial import SalesOrder, Payment
from app.models.customer import Customer
from app.models.finance import ProjectExpense, Invoice
from app.models.subsidy import SubsidyApplication
from app.models.inventory import Supplier
from app.schemas.schemas import (
    ExpenseCreate, ExpenseOut, ProjectProfitabilityOut,
    InvoiceCreate, InvoiceOut, InvoiceStatusUpdate, InvoiceItemSchema
)
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/finance", tags=["Finance & Project Profitability"])


def _parse_date_filter(period: str, start_date: Optional[date] = None, end_date: Optional[date] = None):
    today = date.today()
    if period == "7d":
        return today - timedelta(days=7), today
    elif period == "30d":
        return today - timedelta(days=30), today
    elif period == "month":
        return today.replace(day=1), today
    elif period == "last_month":
        first_this_month = today.replace(day=1)
        last_day_last_month = first_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        return first_day_last_month, last_day_last_month
    elif period == "year":
        # Indian Financial Year starts April 1st
        fy_year = today.year if today.month >= 4 else today.year - 1
        return date(fy_year, 4, 1), today
    elif period == "custom" and start_date and end_date:
        return start_date, end_date
    return None, None


@router.get("/overview")
def get_finance_overview(
    period: str = Query("all", description="Period filter: all, 7d, 30d, month, last_month, year, custom"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dt_start, dt_end = _parse_date_filter(period, start_date, end_date)

    orders_query = db.query(SalesOrder)
    payments_query = db.query(Payment)
    expenses_query = db.query(ProjectExpense)

    if dt_start and dt_end:
        orders_query = orders_query.filter(func.date(SalesOrder.created_at) >= dt_start, func.date(SalesOrder.created_at) <= dt_end)
        payments_query = payments_query.filter(Payment.payment_date >= dt_start, Payment.payment_date <= dt_end)
        expenses_query = expenses_query.filter(ProjectExpense.expense_date >= dt_start, ProjectExpense.expense_date <= dt_end)

    orders = orders_query.all()
    payments = payments_query.all()
    expenses = expenses_query.all()

    total_revenue = sum(o.total_amount for o in orders)
    cash_received = sum(p.amount for p in payments)
    outstanding_receivables = sum(o.balance_due for o in orders)

    # COGS breakdown from orders
    total_hardware_cost = sum(o.hardware_cost for o in orders)
    total_labour_cost = sum(o.installation_cost for o in orders)

    # Operating and project expenses
    transportation_expenses = sum(e.amount for e in expenses if e.category == "TRANSPORTATION")
    operating_expenses = sum(e.amount for e in expenses if e.category != "TRANSPORTATION")
    total_expenses_recorded = sum(e.amount for e in expenses)

    # Total Cost of Goods Sold = Hardware + Installation Labour + Direct Logistics
    cogs = total_hardware_cost + total_labour_cost + transportation_expenses
    gross_margin = total_revenue - cogs
    gross_margin_pct = round((gross_margin / total_revenue * 100), 2) if total_revenue > 0 else 0.0

    # Net Profit = Gross Margin - Operating Expenses
    net_profit = gross_margin - operating_expenses
    net_profit_pct = round((net_profit / total_revenue * 100), 2) if total_revenue > 0 else 0.0

    # Current month cash flow
    first_of_this_month = date.today().replace(day=1)
    month_payments = db.query(Payment).filter(Payment.payment_date >= first_of_this_month).all()
    month_expenses = db.query(ProjectExpense).filter(ProjectExpense.expense_date >= first_of_this_month).all()
    monthly_cash_inflow = sum(p.amount for p in month_payments)
    monthly_cash_outflow = sum(e.amount for e in month_expenses)

    # Subsidy Receivables: Approved applications awaiting disbursement
    subsidy_receivables = db.query(func.sum(SubsidyApplication.subsidy_amount)).filter(
        SubsidyApplication.approval_status == "APPROVED",
        SubsidyApplication.payment_status != "DISBURSED"
    ).scalar() or 0.0

    # Pending supplier payables
    pending_supplier_payables = db.query(func.sum(ProjectExpense.amount)).filter(
        ProjectExpense.approval_status == "PENDING_REVIEW"
    ).scalar() or 0.0

    return {
        "period": period,
        "total_revenue": round(total_revenue, 2),
        "cash_received": round(cash_received, 2),
        "outstanding_receivables": round(outstanding_receivables, 2),
        "total_recorded_costs": round(cogs + operating_expenses, 2),
        "cogs": round(cogs, 2),
        "hardware_cost": round(total_hardware_cost, 2),
        "labour_cost": round(total_labour_cost, 2),
        "transportation_cost": round(transportation_expenses, 2),
        "operating_expenses": round(operating_expenses, 2),
        "gross_margin": round(gross_margin, 2),
        "gross_margin_percentage": gross_margin_pct,
        "net_profit": round(net_profit, 2),
        "net_profit_percentage": net_profit_pct,
        "monthly_cash_inflow": round(monthly_cash_inflow, 2),
        "monthly_cash_outflow": round(monthly_cash_outflow, 2),
        "subsidy_receivables": round(subsidy_receivables, 2),
        "pending_supplier_payables": round(pending_supplier_payables, 2),
    }


@router.get("/analytics")
def get_finance_analytics(
    period: str = Query("all"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns verified backend dataset for Finance Dashboard charts:
    1. Monthly revenue vs expenses vs profit trend (last 6 months)
    2. Cash inflow vs outflow
    3. Revenue by capacity tier
    4. Payment status distribution
    5. Expense category breakdown
    """
    today = date.today()
    months_data = []

    # Last 6 months
    for i in range(5, -1, -1):
        # Calculate start and end of month
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1

        start_m = date(year, month, 1)
        if month == 12:
            end_m = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_m = date(year, month + 1, 1) - timedelta(days=1)

        m_name = start_m.strftime("%b %Y")

        m_orders = db.query(SalesOrder).filter(
            func.date(SalesOrder.created_at) >= start_m,
            func.date(SalesOrder.created_at) <= end_m
        ).all()
        m_payments = db.query(Payment).filter(
            Payment.payment_date >= start_m,
            Payment.payment_date <= end_m
        ).all()
        m_expenses = db.query(ProjectExpense).filter(
            ProjectExpense.expense_date >= start_m,
            ProjectExpense.expense_date <= end_m
        ).all()

        rev = sum(o.total_amount for o in m_orders)
        hw = sum(o.hardware_cost for o in m_orders)
        lab = sum(o.installation_cost for o in m_orders)
        exp = sum(e.amount for e in m_expenses)
        inflow = sum(p.amount for p in m_payments)
        outflow = exp

        months_data.append({
            "month": m_name,
            "revenue": round(rev, 2),
            "expenses": round(hw + lab + exp, 2),
            "profit": round(rev - (hw + lab + exp), 2),
            "inflow": round(inflow, 2),
            "outflow": round(outflow, 2),
        })

    # Capacity distribution
    all_orders = db.query(SalesOrder).all()
    capacity_tiers = {
        "1-3 kW (Residential Small)": 0.0,
        "3.1-5 kW (Residential Standard)": 0.0,
        "5.1-10 kW (Large Residential)": 0.0,
        "> 10 kW (Commercial / Society)": 0.0,
    }
    for o in all_orders:
        cap = o.capacity_kw or 3.0
        if cap <= 3.0:
            capacity_tiers["1-3 kW (Residential Small)"] += o.total_amount
        elif cap <= 5.0:
            capacity_tiers["3.1-5 kW (Residential Standard)"] += o.total_amount
        elif cap <= 10.0:
            capacity_tiers["5.1-10 kW (Large Residential)"] += o.total_amount
        else:
            capacity_tiers["> 10 kW (Commercial / Society)"] += o.total_amount

    capacity_breakdown = [
        {"name": k, "value": round(v, 2)} for k, v in capacity_tiers.items() if v > 0
    ]

    # Payment status distribution
    paid_count = db.query(SalesOrder).filter(SalesOrder.balance_due <= 0).count()
    partial_count = db.query(SalesOrder).filter(SalesOrder.advance_paid > 0, SalesOrder.balance_due > 0).count()
    pending_count = db.query(SalesOrder).filter(SalesOrder.advance_paid == 0).count()

    payment_distribution = [
        {"status": "Fully Paid", "count": paid_count, "color": "#15803d"},
        {"status": "Partially Paid", "count": partial_count, "color": "#d97706"},
        {"status": "Payment Pending", "count": pending_count, "color": "#dc2626"},
    ]

    # Expense category breakdown
    expenses = db.query(ProjectExpense).all()
    exp_cats: Dict[str, float] = {}
    for e in expenses:
        cat_name = e.category.replace("_", " ").title()
        exp_cats[cat_name] = exp_cats.get(cat_name, 0.0) + e.amount

    expense_breakdown = [
        {"category": k, "amount": round(v, 2)} for k, v in exp_cats.items()
    ]

    return {
        "monthly_trend": months_data,
        "capacity_breakdown": capacity_breakdown,
        "payment_distribution": payment_distribution,
        "expense_breakdown": expense_breakdown,
    }


@router.get("/project-profitability", response_model=List[ProjectProfitabilityOut])
@router.get("/profitability", response_model=List[ProjectProfitabilityOut])
def get_project_profitability(
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(SalesOrder).order_by(SalesOrder.id.desc())

    if status_filter and status_filter != "ALL":
        query = query.filter(SalesOrder.status == status_filter)

    orders = query.all()
    results = []

    for o in orders:
        if search:
            q = search.lower()
            c_name = o.customer.name.lower() if o.customer else ""
            if q not in o.order_number.lower() and q not in c_name:
                continue

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
            recognized_revenue=round(o.total_amount, 2),
            advance_paid=round(o.advance_paid, 2),
            balance_due=round(o.balance_due, 2),
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


# ================= EXPENSES & PROCUREMENT =================
@router.get("/expenses", response_model=List[ExpenseOut])
def list_expenses(
    order_id: Optional[int] = None,
    category: Optional[str] = None,
    approval_status: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ProjectExpense)
    if order_id:
        query = query.filter(ProjectExpense.order_id == order_id)
    if category and category != "ALL":
        query = query.filter(ProjectExpense.category == category)
    if approval_status and approval_status != "ALL":
        query = query.filter(ProjectExpense.approval_status == approval_status)
    if start_date:
        query = query.filter(ProjectExpense.expense_date >= start_date)
    if end_date:
        query = query.filter(ProjectExpense.expense_date <= end_date)
    if search:
        s = f"%{search}%"
        query = query.filter(or_(
            ProjectExpense.description.ilike(s),
            ProjectExpense.vendor_name.ilike(s),
            ProjectExpense.invoice_reference.ilike(s)
        ))

    expenses = query.order_by(ProjectExpense.id.desc()).all()
    results = []
    for e in expenses:
        results.append(ExpenseOut(
            id=e.id,
            order_id=e.order_id,
            order_number=e.order.order_number if e.order else None,
            category=e.category,
            amount=e.amount,
            gst_amount=e.gst_amount or 0.0,
            supplier_id=e.supplier_id,
            vendor_name=e.vendor_name or (e.supplier.name if e.supplier else None),
            invoice_reference=e.invoice_reference,
            payment_method=e.payment_method or "BANK_TRANSFER",
            approval_status=e.approval_status or "APPROVED",
            document_url=e.document_url,
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
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Expense amount must be greater than zero")

    order = None
    if payload.order_id:
        order = db.query(SalesOrder).filter(SalesOrder.id == payload.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Referenced project/sales order not found")

    supplier = None
    if payload.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()

    exp = ProjectExpense(
        order_id=payload.order_id,
        category=payload.category,
        amount=round(payload.amount, 2),
        gst_amount=round(payload.gst_amount or 0.0, 2),
        supplier_id=payload.supplier_id,
        vendor_name=payload.vendor_name or (supplier.name if supplier else None),
        invoice_reference=payload.invoice_reference,
        payment_method=payload.payment_method or "BANK_TRANSFER",
        approval_status=payload.approval_status or "APPROVED",
        document_url=payload.document_url,
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
        order_number=order.order_number if order else None,
        category=exp.category,
        amount=exp.amount,
        gst_amount=exp.gst_amount,
        supplier_id=exp.supplier_id,
        vendor_name=exp.vendor_name,
        invoice_reference=exp.invoice_reference,
        payment_method=exp.payment_method,
        approval_status=exp.approval_status,
        document_url=exp.document_url,
        description=exp.description,
        expense_date=exp.expense_date,
        recorded_by=exp.recorded_by,
        created_at=exp.created_at
    )


# ================= INVOICES & BILLING =================
def _parse_invoice_items(inv: Invoice) -> List[InvoiceItemSchema]:
    if not inv.items_json:
        return []
    try:
        raw_items = json.loads(inv.items_json)
        return [InvoiceItemSchema(**item) for item in raw_items]
    except Exception:
        return []


@router.get("/invoices", response_model=List[InvoiceOut])
def list_invoices(
    status_filter: Optional[str] = None,
    customer_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Invoice).order_by(Invoice.id.desc())
    if status_filter and status_filter != "ALL":
        query = query.filter(Invoice.status == status_filter)
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)

    invoices = query.all()
    results = []

    for inv in invoices:
        if search:
            s = search.lower()
            c_name = inv.customer.name.lower() if inv.customer else ""
            inv_num = inv.invoice_number.lower()
            ord_num = inv.order.order_number.lower() if inv.order else ""
            if s not in inv_num and s not in c_name and s not in ord_num:
                continue

        results.append(InvoiceOut(
            id=inv.id,
            invoice_number=inv.invoice_number,
            order_id=inv.order_id,
            order_number=inv.order.order_number if inv.order else None,
            customer_id=inv.customer_id,
            customer_name=inv.customer.name if inv.customer else None,
            customer_phone=inv.customer.phone if inv.customer else None,
            customer_email=inv.customer.email if inv.customer else None,
            customer_address=inv.customer.address if inv.customer else None,
            subtotal=round(inv.subtotal, 2),
            tax_rate=round(inv.tax_rate or 0.138, 4),
            tax_amount=round(inv.tax_amount, 2),
            discount=round(inv.discount or 0.0, 2),
            total_amount=round(inv.total_amount, 2),
            paid_amount=round(inv.paid_amount, 2),
            balance_due=round(inv.balance_due, 2),
            status=inv.status,
            due_date=inv.due_date,
            notes=inv.notes,
            items=_parse_invoice_items(inv),
            created_at=inv.created_at,
            updated_at=inv.updated_at
        ))
    return results


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice_details(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return InvoiceOut(
        id=inv.id,
        invoice_number=inv.invoice_number,
        order_id=inv.order_id,
        order_number=inv.order.order_number if inv.order else None,
        customer_id=inv.customer_id,
        customer_name=inv.customer.name if inv.customer else None,
        customer_phone=inv.customer.phone if inv.customer else None,
        customer_email=inv.customer.email if inv.customer else None,
        customer_address=inv.customer.address if inv.customer else None,
        subtotal=round(inv.subtotal, 2),
        tax_rate=round(inv.tax_rate or 0.138, 4),
        tax_amount=round(inv.tax_amount, 2),
        discount=round(inv.discount or 0.0, 2),
        total_amount=round(inv.total_amount, 2),
        paid_amount=round(inv.paid_amount, 2),
        balance_due=round(inv.balance_due, 2),
        status=inv.status,
        due_date=inv.due_date,
        notes=inv.notes,
        items=_parse_invoice_items(inv),
        created_at=inv.created_at,
        updated_at=inv.updated_at
    )


@router.post("/invoices", response_model=InvoiceOut)
def create_invoice_from_order(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates an itemized formal Tax Invoice from an approved Sales Order.
    Generates standard solar line items according to Indian GST Composite Solar Structure (70% goods @ 12%, 30% services @ 18% = 13.8%).
    """
    order = db.query(SalesOrder).filter(SalesOrder.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales Order not found")

    existing_inv = db.query(Invoice).filter(Invoice.order_id == order.id).first()
    if existing_inv:
        raise HTTPException(
            status_code=400,
            detail=f"An invoice ({existing_inv.invoice_number}) has already been generated for this Sales Order."
        )

    # Generate unique Tax Invoice Number
    year = date.today().year
    rand_seq = random.randint(1000, 9999)
    inv_number = f"INV-{year}-{rand_seq}"
    while db.query(Invoice).filter(Invoice.invoice_number == inv_number).first():
        rand_seq = random.randint(1000, 9999)
        inv_number = f"INV-{year}-{rand_seq}"

    # Build itemized invoice lines
    items: List[Dict[str, Any]] = []
    cap = order.capacity_kw or 3.0
    panel_count = max(4, int(cap * 2))  # ~540W modules

    if payload.custom_items and len(payload.custom_items) > 0:
        for ci in payload.custom_items:
            items.append(ci.model_dump())
        subtotal = sum(i["quantity"] * i["unit_price"] for i in items)
    else:
        # Standardized itemized breakdown from order values
        hw_val = order.hardware_cost or (order.total_amount * 0.75)
        inst_val = order.installation_cost or (order.total_amount * 0.25)

        items = [
            {
                "description": f"Tier-1 Mono PERC Bifacial Solar PV Modules (540Wp) - {cap} kW System",
                "category": "SOLAR_MODULES",
                "quantity": float(panel_count),
                "unit": "nos",
                "unit_price": round((hw_val * 0.65) / panel_count, 2),
                "tax_rate": 0.12,
                "tax_amount": round((hw_val * 0.65) * 0.12, 2),
                "total_amount": round((hw_val * 0.65) * 1.12, 2)
            },
            {
                "description": f"High-Efficiency On-Grid Solar Inverter ({cap} kW MPPT)",
                "category": "INVERTER",
                "quantity": 1.0,
                "unit": "unit",
                "unit_price": round(hw_val * 0.22, 2),
                "tax_rate": 0.12,
                "tax_amount": round((hw_val * 0.22) * 0.12, 2),
                "total_amount": round((hw_val * 0.22) * 1.12, 2)
            },
            {
                "description": f"Elevated Hot-Dip Galvanized Module Mounting Structure (Wind rated 150 km/h)",
                "category": "STRUCTURE",
                "quantity": 1.0,
                "unit": "set",
                "unit_price": round(hw_val * 0.08, 2),
                "tax_rate": 0.18,
                "tax_amount": round((hw_val * 0.08) * 0.18, 2),
                "total_amount": round((hw_val * 0.08) * 1.18, 2)
            },
            {
                "description": f"Balance of System (ACDB/DCDB, 4sqmm Solar DC Cable, Copper Earthing Kits, Lightning Arrester)",
                "category": "BOS_ELECTRICAL",
                "quantity": 1.0,
                "unit": "set",
                "unit_price": round(hw_val * 0.05, 2),
                "tax_rate": 0.18,
                "tax_amount": round((hw_val * 0.05) * 0.18, 2),
                "total_amount": round((hw_val * 0.05) * 1.18, 2)
            },
            {
                "description": f"Turnkey Mechanical Installation, Electrical Wiring, Testing & DISCOM Net-Metering Liaison",
                "category": "SERVICES_LABOUR",
                "quantity": 1.0,
                "unit": "job",
                "unit_price": round(inst_val, 2),
                "tax_rate": 0.18,
                "tax_amount": round(inst_val * 0.18, 2),
                "total_amount": round(inst_val * 1.18, 2)
            }
        ]
        subtotal = hw_val + inst_val

    # Tax calculation
    tax_rate = payload.tax_rate if payload.tax_rate is not None else 0.138
    tax_amount = sum(i.get("tax_amount", 0.0) for i in items)
    if tax_amount <= 0:
        tax_amount = round(subtotal * tax_rate, 2)

    discount = round(payload.discount or 0.0, 2)
    total_amount = round(subtotal + tax_amount - discount, 2)

    # Sync paid amount from current order payments
    paid_amount = round(order.advance_paid or 0.0, 2)
    balance_due = max(0.0, round(total_amount - paid_amount, 2))

    status_str = "UNPAID"
    if balance_due <= 0:
        status_str = "PAID"
    elif paid_amount > 0:
        status_str = "PARTIALLY_PAID"

    due_dt = payload.due_date or (date.today() + timedelta(days=15))

    invoice = Invoice(
        invoice_number=inv_number,
        order_id=order.id,
        customer_id=order.customer_id,
        subtotal=round(subtotal, 2),
        tax_rate=tax_rate,
        tax_amount=round(tax_amount, 2),
        discount=discount,
        total_amount=total_amount,
        paid_amount=paid_amount,
        balance_due=balance_due,
        status=status_str,
        due_date=due_dt,
        notes=payload.notes or f"Official Tax Invoice for Solar PV System Order {order.order_number}",
        items_json=json.dumps(items)
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return InvoiceOut(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        order_id=invoice.order_id,
        order_number=order.order_number,
        customer_id=invoice.customer_id,
        customer_name=order.customer.name if order.customer else None,
        customer_phone=order.customer.phone if order.customer else None,
        customer_email=order.customer.email if order.customer else None,
        customer_address=order.customer.address if order.customer else None,
        subtotal=invoice.subtotal,
        tax_rate=invoice.tax_rate,
        tax_amount=invoice.tax_amount,
        discount=invoice.discount,
        total_amount=invoice.total_amount,
        paid_amount=invoice.paid_amount,
        balance_due=invoice.balance_due,
        status=invoice.status,
        due_date=invoice.due_date,
        notes=invoice.notes,
        items=_parse_invoice_items(invoice),
        created_at=invoice.created_at,
        updated_at=invoice.updated_at
    )


@router.put("/invoices/{invoice_id}/status", response_model=InvoiceOut)
def update_invoice_status(
    invoice_id: int,
    payload: InvoiceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    valid_statuses = ["DRAFT", "ISSUED", "PARTIALLY_PAID", "PAID", "OVERDUE", "CANCELLED"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid invoice status. Must be one of {valid_statuses}")

    inv.status = payload.status
    if payload.notes:
        inv.notes = payload.notes

    db.commit()
    db.refresh(inv)

    return InvoiceOut(
        id=inv.id,
        invoice_number=inv.invoice_number,
        order_id=inv.order_id,
        order_number=inv.order.order_number if inv.order else None,
        customer_id=inv.customer_id,
        customer_name=inv.customer.name if inv.customer else None,
        customer_phone=inv.customer.phone if inv.customer else None,
        customer_email=inv.customer.email if inv.customer else None,
        customer_address=inv.customer.address if inv.customer else None,
        subtotal=inv.subtotal,
        tax_rate=inv.tax_rate or 0.138,
        tax_amount=inv.tax_amount,
        discount=inv.discount or 0.0,
        total_amount=inv.total_amount,
        paid_amount=inv.paid_amount,
        balance_due=inv.balance_due,
        status=inv.status,
        due_date=inv.due_date,
        notes=inv.notes,
        items=_parse_invoice_items(inv),
        created_at=inv.created_at,
        updated_at=inv.updated_at
    )


# ================= FINANCIAL STATEMENTS / REPORTS =================
@router.get("/reports/pnl")
def get_profit_and_loss_statement(
    period: str = Query("year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Structured GAAP/Indian Accounting Standard Profit & Loss Statement
    """
    dt_start, dt_end = _parse_date_filter(period)
    orders_q = db.query(SalesOrder)
    expenses_q = db.query(ProjectExpense)

    if dt_start and dt_end:
        orders_q = orders_q.filter(func.date(SalesOrder.created_at) >= dt_start, func.date(SalesOrder.created_at) <= dt_end)
        expenses_q = expenses_q.filter(ProjectExpense.expense_date >= dt_start, ProjectExpense.expense_date <= dt_end)

    orders = orders_q.all()
    expenses = expenses_q.all()

    revenue_solar_systems = sum(o.total_amount for o in orders)
    hardware_cogs = sum(o.hardware_cost for o in orders)
    labour_cogs = sum(o.installation_cost for o in orders)
    transport_cogs = sum(e.amount for e in expenses if e.category == "TRANSPORTATION")

    total_cogs = hardware_cogs + labour_cogs + transport_cogs
    gross_profit = revenue_solar_systems - total_cogs

    # Categorize operating expenses
    opex_categories: Dict[str, float] = {}
    for e in expenses:
        if e.category != "TRANSPORTATION":
            c_label = e.category.replace("_", " ").title()
            opex_categories[c_label] = opex_categories.get(c_label, 0.0) + e.amount

    total_opex = sum(opex_categories.values())
    operating_income = gross_profit - total_opex
    net_income = operating_income

    return {
        "statement": "Profit and Loss Statement",
        "period": period,
        "as_of_date": str(date.today()),
        "trading_account": {
            "gross_revenue": round(revenue_solar_systems, 2),
            "cost_of_goods_sold": {
                "solar_hardware_and_inverters": round(hardware_cogs, 2),
                "direct_installation_labour": round(labour_cogs, 2),
                "freight_and_transportation": round(transport_cogs, 2),
                "total_cogs": round(total_cogs, 2)
            },
            "gross_profit": round(gross_profit, 2),
            "gross_profit_margin_pct": round((gross_profit / revenue_solar_systems * 100), 2) if revenue_solar_systems > 0 else 0.0
        },
        "operating_expenses": {
            "breakdown": [{"category": k, "amount": round(v, 2)} for k, v in opex_categories.items()],
            "total_operating_expenses": round(total_opex, 2)
        },
        "net_profit": {
            "operating_income": round(operating_income, 2),
            "net_income": round(net_income, 2),
            "net_profit_margin_pct": round((net_income / revenue_solar_systems * 100), 2) if revenue_solar_systems > 0 else 0.0
        }
    }
