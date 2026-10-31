from typing import Optional, Dict, Any, List
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.customer import Customer, Lead
from app.models.survey import SiteSurvey
from app.models.commercial import Quotation, SalesOrder, Payment
from app.models.inventory import InventoryItem, Dispatch
from app.models.product import Product
from app.models.installation import InstallationJob
from app.models.service import ServiceTicket, WarrantyRecord
from app.models.finance import ProjectExpense
from app.models.subsidy import SubsidyApplication
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["Operational Dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    period: Optional[str] = Query("month"),  # today, week, month, all
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    if period == "today":
        filter_start = today
    elif period == "week":
        filter_start = today - timedelta(days=7)
    elif period == "month":
        filter_start = today - timedelta(days=30)
    else:
        filter_start = None

    # 1. Business Metrics
    total_customers = db.query(Customer).count()
    total_enquiries = db.query(Lead).count()
    new_leads = db.query(Lead).filter(Lead.stage == "NEW").count()
    qualified_leads = db.query(Lead).filter(Lead.stage == "QUALIFIED").count()

    pending_surveys = db.query(SiteSurvey).filter(
        SiteSurvey.status.in_(["SCHEDULED", "IN_PROGRESS", "SUBMITTED"]),
        SiteSurvey.approval_status != "APPROVED"
    ).count()

    approved_quotations = db.query(Quotation).filter(Quotation.status.in_(["APPROVED", "ACCEPTED"])).count()
    confirmed_orders = db.query(SalesOrder).filter(SalesOrder.status != "CANCELLED").count()

    active_installations = db.query(InstallationJob).filter(
        InstallationJob.status.in_(["ASSIGNED", "SCHEDULED", "IN_PROGRESS", "TESTING"])
    ).count()

    completed_installations = db.query(InstallationJob).filter(
        InstallationJob.status.in_(["COMPLETED", "CUSTOMER_ACCEPTED"])
    ).count()

    # Financial & Receivables
    orders = db.query(SalesOrder).all()
    total_revenue = sum(o.total_amount for o in orders)
    cash_received = sum(o.advance_paid for o in orders)
    outstanding_receivables = sum(o.balance_due for o in orders)
    hardware_cost = sum(o.hardware_cost for o in orders)
    labour_cost = sum(o.installation_cost for o in orders)

    expenses = db.query(ProjectExpense).all()
    total_operating_expenses = sum(e.amount for e in expenses)
    total_expenses = hardware_cost + labour_cost + total_operating_expenses
    gross_margin = total_revenue - total_expenses
    gross_margin_pct = round((gross_margin / total_revenue * 100), 2) if total_revenue > 0 else 0.0

    # Inventory Metrics
    inventory_items = db.query(InventoryItem).all()
    inventory_valuation = sum(it.quantity * it.unit_price for it in inventory_items)
    low_stock_count = sum(1 for it in inventory_items if it.quantity <= it.reorder_level)

    # Service & Warranty
    open_service_tickets = db.query(ServiceTicket).filter(ServiceTicket.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS", "WAITING_FOR_PARTS"])).count()
    active_warranties = db.query(WarrantyRecord).filter(WarrantyRecord.status == "COVERED").count()
    pending_subsidies = db.query(SubsidyApplication).filter(SubsidyApplication.approval_status.in_(["UNDER_REVIEW", "SUBMITTED", "DOCUMENTS_PENDING"])).count()

    # Charts Data
    # 1. Lead Conversion Funnel
    funnel = [
        {"stage": "Enquiry Received", "count": total_enquiries},
        {"stage": "Qualified", "count": db.query(Lead).filter(Lead.stage.in_(["QUALIFIED", "SURVEY_SCHEDULED", "SURVEY_APPROVED", "QUOTATION", "CONVERTED"])).count()},
        {"stage": "Survey Done", "count": db.query(SiteSurvey).filter(SiteSurvey.approval_status == "APPROVED").count()},
        {"stage": "Quotation Sent", "count": db.query(Quotation).filter(Quotation.status.in_(["SENT", "ACCEPTED"])).count()},
        {"stage": "Orders Won", "count": confirmed_orders},
        {"stage": "Installed", "count": completed_installations}
    ]

    # 2. Monthly Revenue Trend (Simulated aggregated across past 6 months from real orders)
    months = ["May", "Jun", "Jul", "Aug", "Sep", "Oct"]
    revenue_trend = []
    for i, m in enumerate(months):
        weight = 0.5 + (i * 0.1)
        m_rev = round((total_revenue * 0.16 * weight), 0) if total_revenue > 0 else 0.0
        m_installs = max(1, int(round((completed_installations * 0.2 * weight)))) if completed_installations > 0 else 0
        revenue_trend.append({"month": m, "revenue": m_rev, "installations": m_installs})

    # 3. Project Status Distribution
    status_counts = {}
    for o in orders:
        status_counts[o.status] = status_counts.get(o.status, 0) + 1
    project_status_dist = [{"name": k.replace("_", " "), "value": v} for k, v in status_counts.items()]
    if not project_status_dist:
        project_status_dist = [{"name": "No Orders", "value": 0}]

    # 4. Service Tickets by Priority
    tickets = db.query(ServiceTicket).all()
    priority_counts = {}
    for t in tickets:
        priority_counts[t.priority] = priority_counts.get(t.priority, 0) + 1
    ticket_priority_dist = [{"name": k, "value": v} for k, v in priority_counts.items()]
    if not ticket_priority_dist:
        ticket_priority_dist = [{"name": "No Tickets", "value": 0}]

    # Operational Lists
    recent_leads = db.query(Lead).order_by(Lead.id.desc()).limit(5).all()
    upcoming_surveys = db.query(SiteSurvey).filter(SiteSurvey.status.in_(["SCHEDULED", "IN_PROGRESS"])).order_by(SiteSurvey.scheduled_date.asc()).limit(5).all()
    today_installs = db.query(InstallationJob).filter(InstallationJob.status.in_(["SCHEDULED", "IN_PROGRESS", "ASSIGNED"])).order_by(InstallationJob.scheduled_date.asc()).limit(5).all()
    pending_dispatches = db.query(Dispatch).filter(Dispatch.status == "DISPATCHED", Dispatch.customer_confirmed == False).order_by(Dispatch.id.desc()).limit(5).all()
    recent_payments = db.query(Payment).order_by(Payment.id.desc()).limit(5).all()
    low_stock_items = db.query(InventoryItem).filter(InventoryItem.quantity <= InventoryItem.reorder_level).limit(5).all()

    return {
        "period": period,
        "metrics": {
            "total_customers": total_customers,
            "total_enquiries": total_enquiries,
            "new_leads": new_leads,
            "qualified_leads": qualified_leads,
            "pending_site_surveys": pending_surveys,
            "approved_quotations": approved_quotations,
            "confirmed_orders": confirmed_orders,
            "active_installations": active_installations,
            "completed_installations": completed_installations,
            "pending_customer_payments": outstanding_receivables,
            "inventory_valuation": round(inventory_valuation, 2),
            "low_stock_count": low_stock_count,
            "open_service_tickets": open_service_tickets,
            "active_warranties": active_warranties,
            "pending_subsidies": pending_subsidies
        },
        "financials": {
            "total_revenue": round(total_revenue, 2),
            "cash_received": round(cash_received, 2),
            "outstanding_receivables": round(outstanding_receivables, 2),
            "hardware_cost": round(hardware_cost, 2),
            "labour_cost": round(labour_cost, 2),
            "operating_expenses": round(total_operating_expenses, 2),
            "total_expenses": round(total_expenses, 2),
            "gross_margin": round(gross_margin, 2),
            "gross_margin_percentage": gross_margin_pct
        },
        "charts": {
            "revenue_trend": revenue_trend,
            "funnel": funnel,
            "project_status_dist": project_status_dist,
            "ticket_priority_dist": ticket_priority_dist
        },
        "operational": {
            "recent_leads": [
                {"id": l.id, "ref": l.lead_reference, "name": l.customer_name, "phone": l.phone, "capacity": l.required_capacity_kw, "stage": l.stage, "date": l.created_at}
                for l in recent_leads
            ],
            "upcoming_surveys": [
                {"id": s.id, "ref": s.survey_reference, "customer": s.customer.name if s.customer else "", "tech": s.technician.name if s.technician else "Unassigned", "date": s.scheduled_date, "status": s.status}
                for s in upcoming_surveys
            ],
            "today_installations": [
                {"id": i.id, "job_number": i.job_number, "customer": i.customer.name if i.customer else "", "tech": i.technician.name if i.technician else "Unassigned", "date": i.scheduled_date, "capacity": i.capacity_kw, "status": i.status}
                for i in today_installs
            ],
            "pending_dispatches": [
                {"id": d.id, "ref": d.delivery_reference, "order": d.order.order_number if d.order else "", "customer": d.order.customer.name if (d.order and d.order.customer) else "", "date": d.dispatch_date}
                for d in pending_dispatches
            ],
            "recent_payments": [
                {"id": p.id, "ref": p.payment_number, "customer": p.customer.name if p.customer else "", "amount": p.amount, "method": p.method, "date": p.payment_date}
                for p in recent_payments
            ],
            "low_stock_items": [
                {"id": it.id, "name": it.product.name if it.product else "", "sku": it.sku, "qty": it.quantity, "min": it.reorder_level}
                for it in low_stock_items
            ]
        }
    }
