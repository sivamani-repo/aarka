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


def _filter_period(query, model, filter_start):
    if filter_start is not None:
        return query.filter(model.created_at >= filter_start)
    return query


def _count_period(db, model, filter_start, *conditions):
    query = _filter_period(db.query(func.count(model.id)), model, filter_start)
    if conditions:
        query = query.filter(*conditions)
    return query.scalar() or 0


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
        filter_start = today - timedelta(days=today.weekday())
    elif period == "month":
        filter_start = today.replace(day=1)
    else:
        filter_start = None

    # 1. Business Metrics
    total_customers = _count_period(db, Customer, filter_start)
    leads_query = _filter_period(db.query(Lead), Lead, filter_start)
    total_enquiries = _count_period(db, Lead, filter_start)
    new_leads = _count_period(db, Lead, filter_start, Lead.stage == "NEW")
    qualified_leads = _count_period(db, Lead, filter_start, Lead.stage == "QUALIFIED")

    surveys_query = _filter_period(db.query(SiteSurvey), SiteSurvey, filter_start)
    pending_surveys = _count_period(db, SiteSurvey, filter_start,
        SiteSurvey.status.in_(["SCHEDULED", "IN_PROGRESS", "SUBMITTED"]),
        SiteSurvey.approval_status != "APPROVED"
    )

    quotations_query = _filter_period(db.query(Quotation), Quotation, filter_start)
    approved_quotations = _count_period(
        db, Quotation, filter_start, Quotation.status.in_(["APPROVED", "ACCEPTED"])
    )
    orders_query = _filter_period(db.query(SalesOrder), SalesOrder, filter_start)
    confirmed_orders = _count_period(db, SalesOrder, filter_start, SalesOrder.status != "CANCELLED")

    installations_query = _filter_period(db.query(InstallationJob), InstallationJob, filter_start)
    active_installations = _count_period(
        db, InstallationJob, filter_start,
        InstallationJob.status.in_(["ASSIGNED", "SCHEDULED", "IN_PROGRESS", "TESTING"])
    )

    completed_installations = _count_period(
        db, InstallationJob, filter_start,
        InstallationJob.status.in_(["COMPLETED", "CUSTOMER_ACCEPTED"])
    )

    # Financial & Receivables
    orders = orders_query.all()
    total_revenue = sum(o.total_amount for o in orders)
    cash_received = sum(o.advance_paid for o in orders)
    outstanding_receivables = sum(o.balance_due for o in orders)
    hardware_cost = sum(o.hardware_cost for o in orders)
    labour_cost = sum(o.installation_cost for o in orders)

    expense_amounts = _filter_period(
        db.query(ProjectExpense.amount),
        ProjectExpense,
        filter_start
    ).all()
    total_operating_expenses = sum(amount or 0 for (amount,) in expense_amounts)
    total_expenses = hardware_cost + labour_cost + total_operating_expenses
    gross_margin = total_revenue - total_expenses
    gross_margin_pct = round((gross_margin / total_revenue * 100), 2) if total_revenue > 0 else 0.0

    # Inventory Metrics
    inventory_items = db.query(InventoryItem).all()
    inventory_valuation = sum(it.quantity * it.unit_price for it in inventory_items)
    low_stock_count = sum(1 for it in inventory_items if it.quantity <= it.reorder_level)

    # Service & Warranty
    tickets_query = _filter_period(db.query(ServiceTicket), ServiceTicket, filter_start)
    open_service_tickets = _count_period(
        db, ServiceTicket, filter_start,
        ServiceTicket.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS", "WAITING_FOR_PARTS"])
    )
    active_warranties = _count_period(
        db, WarrantyRecord, filter_start, WarrantyRecord.status == "COVERED"
    )
    pending_subsidies = _count_period(
        db, SubsidyApplication, filter_start,
        SubsidyApplication.approval_status.in_(["UNDER_REVIEW", "SUBMITTED", "DOCUMENTS_PENDING"])
    )

    # Charts Data
    # 1. Lead Conversion Funnel
    funnel = [
        {"stage": "Enquiry Received", "count": total_enquiries},
        {"stage": "Qualified", "count": _count_period(
            db, Lead, filter_start,
            Lead.stage.in_(["QUALIFIED", "SURVEY_SCHEDULED", "SURVEY_APPROVED", "QUOTATION", "CONVERTED"])
        )},
        {"stage": "Survey Done", "count": _count_period(
            db, SiteSurvey, filter_start, SiteSurvey.approval_status == "APPROVED"
        )},
        {"stage": "Quotation Sent", "count": _count_period(
            db, Quotation, filter_start, Quotation.status.in_(["SENT", "ACCEPTED"])
        )},
        {"stage": "Orders Won", "count": confirmed_orders},
        {"stage": "Installed", "count": completed_installations}
    ]

    # 2. Revenue and installation activity from records in the selected period.
    filtered_installations = installations_query.all()
    revenue_by_bucket = {}
    installs_by_bucket = {}

    def period_bucket(created_at):
        created_date = created_at.date()
        if period == "all":
            return created_date.replace(day=1)
        return created_date

    for order in orders:
        bucket = period_bucket(order.created_at)
        revenue_by_bucket[bucket] = revenue_by_bucket.get(bucket, 0) + (order.total_amount or 0)
    for installation in filtered_installations:
        bucket = period_bucket(installation.created_at)
        installs_by_bucket[bucket] = installs_by_bucket.get(bucket, 0) + 1

    if period == "today":
        trend_buckets = [today]
    elif period == "week":
        trend_buckets = [filter_start + timedelta(days=offset) for offset in range((today - filter_start).days + 1)]
    elif period == "month":
        trend_buckets = [filter_start + timedelta(days=offset) for offset in range((today - filter_start).days + 1)]
    else:
        trend_buckets = sorted(set(revenue_by_bucket) | set(installs_by_bucket))

    revenue_trend = [
        {
            "month": bucket.strftime("%b %Y") if period == "all" else (
                "Today" if period == "today" else bucket.strftime("%a" if period == "week" else "%d %b")
            ),
            "revenue": round(revenue_by_bucket.get(bucket, 0), 2),
            "installations": installs_by_bucket.get(bucket, 0),
        }
        for bucket in trend_buckets
    ]

    # 3. Project Status Distribution
    status_counts = {}
    for o in orders:
        status_counts[o.status] = status_counts.get(o.status, 0) + 1
    project_status_dist = [{"name": k.replace("_", " "), "value": v} for k, v in status_counts.items()]
    if not project_status_dist:
        project_status_dist = [{"name": "No Orders", "value": 0}]

    # 4. Service Tickets by Priority
    tickets = tickets_query.all()
    priority_counts = {}
    for t in tickets:
        priority_counts[t.priority] = priority_counts.get(t.priority, 0) + 1
    ticket_priority_dist = [{"name": k, "value": v} for k, v in priority_counts.items()]
    if not ticket_priority_dist:
        ticket_priority_dist = [{"name": "No Tickets", "value": 0}]

    # Operational Lists
    recent_leads = leads_query.order_by(Lead.id.desc()).limit(5).all()
    upcoming_surveys = surveys_query.filter(SiteSurvey.status.in_(["SCHEDULED", "IN_PROGRESS"])).order_by(SiteSurvey.scheduled_date.asc()).limit(5).all()
    today_installs = installations_query.filter(InstallationJob.status.in_(["SCHEDULED", "IN_PROGRESS", "ASSIGNED"])).order_by(InstallationJob.scheduled_date.asc()).limit(5).all()
    pending_dispatches = _filter_period(db.query(Dispatch), Dispatch, filter_start).filter(Dispatch.status == "DISPATCHED", Dispatch.customer_confirmed == False).order_by(Dispatch.id.desc()).limit(5).all()
    recent_payments = _filter_period(db.query(Payment), Payment, filter_start).order_by(Payment.id.desc()).limit(5).all()
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
