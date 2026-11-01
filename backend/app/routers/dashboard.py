from typing import Optional, Dict, Any, List
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

from app.database import get_db
from app.models.customer import Customer, Lead
from app.models.survey import SiteSurvey
from app.models.commercial import Quotation, SalesOrder, Payment
from app.models.inventory import InventoryItem, Dispatch
from app.models.installation import InstallationJob
from app.models.service import ServiceTicket, WarrantyRecord
from app.models.finance import ProjectExpense
from app.models.subsidy import SubsidyApplication
from app.core.permissions import get_current_user
from app.core.rbac import canonical_role, has_permission
from app.models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["Operational Dashboard"])
BUSINESS_TIMEZONE = ZoneInfo("Asia/Kolkata")


def _scope_dashboard_query(db, query, model, current_user: User):
    role = canonical_role(current_user.role)
    if role == "Sales Executive":
        assigned_leads = db.query(Lead.id).filter(Lead.assigned_user_id == current_user.id)
        if model is Lead:
            legacy_owner = and_(
                Lead.assigned_user_id.is_(None),
                or_(
                    func.lower(Lead.assigned_sales_rep) == current_user.name.lower(),
                    func.lower(Lead.assigned_sales_rep) == current_user.email.lower(),
                ),
            )
            return query.filter(or_(Lead.assigned_user_id == current_user.id, legacy_owner))
        if model is Customer:
            return query.filter(or_(
                Customer.assigned_user_id == current_user.id,
                Customer.id.in_(
                    db.query(Lead.customer_id).filter(Lead.assigned_user_id == current_user.id)
                ),
            ))
        if model is SiteSurvey:
            customer_ids = db.query(Customer.id).filter(or_(
                Customer.assigned_user_id == current_user.id,
                Customer.id.in_(
                    db.query(Lead.customer_id).filter(Lead.assigned_user_id == current_user.id)
                ),
            ))
            return query.filter(or_(
                SiteSurvey.assigned_user_id == current_user.id,
                SiteSurvey.customer_id.in_(customer_ids),
            ))
        if model is Quotation:
            customer_ids = db.query(Customer.id).filter(or_(
                Customer.assigned_user_id == current_user.id,
                Customer.id.in_(
                    db.query(Lead.customer_id).filter(Lead.assigned_user_id == current_user.id)
                ),
            ))
            return query.filter(or_(
                Quotation.customer_id.in_(customer_ids),
                Quotation.lead_id.in_(assigned_leads),
            ))
        if model is SalesOrder:
            customer_ids = db.query(Customer.id).filter(or_(
                Customer.assigned_user_id == current_user.id,
                Customer.id.in_(
                    db.query(Lead.customer_id).filter(Lead.assigned_user_id == current_user.id)
                ),
            ))
            return query.filter(or_(
                SalesOrder.customer_id.in_(customer_ids),
                SalesOrder.quotation_id.in_(
                    db.query(Quotation.id).filter(Quotation.lead_id.in_(assigned_leads))
                ),
            ))
    elif role == "Site Survey Engineer":
        if model is SiteSurvey:
            return query.filter(SiteSurvey.assigned_user_id == current_user.id)
        if model is Customer:
            return query.filter(Customer.id.in_(
                db.query(SiteSurvey.customer_id).filter(SiteSurvey.assigned_user_id == current_user.id)
            ))
    elif role == "Solar Technician":
        if model is InstallationJob:
            return query.filter(InstallationJob.assigned_user_id == current_user.id)
        if model is Customer:
            return query.filter(Customer.id.in_(
                db.query(InstallationJob.customer_id).filter(InstallationJob.assigned_user_id == current_user.id)
            ))
    elif role == "Dispatch Staff":
        if model is Dispatch:
            return query.filter(Dispatch.assigned_user_id == current_user.id)
        if model is Customer:
            return query.filter(Customer.id.in_(
                db.query(SalesOrder.customer_id).join(
                    Dispatch, Dispatch.order_id == SalesOrder.id
                ).filter(Dispatch.assigned_user_id == current_user.id)
            ))
    elif role == "Support Executive":
        if model is ServiceTicket:
            return query.filter(ServiceTicket.assigned_user_id == current_user.id)
        if model is Customer:
            return query.filter(Customer.id.in_(
                db.query(ServiceTicket.customer_id).filter(ServiceTicket.assigned_user_id == current_user.id)
            ))
        if model is WarrantyRecord:
            return query.filter(WarrantyRecord.customer_id.in_(
                db.query(ServiceTicket.customer_id).filter(ServiceTicket.assigned_user_id == current_user.id)
            ))
    return query


def _filter_period(
    query,
    model,
    filter_start,
    db=None,
    current_user: Optional[User] = None,
    filter_end=None,
):
    if db is not None and current_user is not None:
        query = _scope_dashboard_query(db, query, model, current_user)
    if filter_start is not None:
        query = query.filter(model.created_at >= filter_start)
    if filter_end is not None:
        query = query.filter(model.created_at < filter_end)
    return query


def _count_period(
    db,
    model,
    filter_start,
    *conditions,
    current_user: User,
    filter_end=None,
):
    query = _filter_period(
        db.query(func.count(model.id)),
        model,
        filter_start,
        db,
        current_user,
        filter_end,
    )
    if conditions:
        query = query.filter(*conditions)
    return query.scalar() or 0


@router.get("/summary")
def get_dashboard_summary(
    period: str = Query("month", pattern="^(today|week|month|all)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = datetime.now(BUSINESS_TIMEZONE).date()
    if period == "today":
        start_date = today
        end_date = today + timedelta(days=1)
    elif period == "week":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
    elif period == "month":
        start_date = today.replace(day=1)
        end_date = (
            start_date.replace(year=start_date.year + 1, month=1)
            if start_date.month == 12
            else start_date.replace(month=start_date.month + 1)
        )
    else:
        start_date = None
        end_date = None

    filter_start = (
        datetime.combine(start_date, time.min, tzinfo=BUSINESS_TIMEZONE)
        if start_date
        else None
    )
    filter_end = (
        datetime.combine(end_date, time.min, tzinfo=BUSINESS_TIMEZONE)
        if end_date
        else None
    )

    def count_period(model, *conditions):
        return _count_period(
            db,
            model,
            filter_start,
            *conditions,
            current_user=current_user,
            filter_end=filter_end,
        )

    # 1. Business Metrics
    total_customers = count_period(Customer)
    leads_query = _filter_period(
        db.query(Lead), Lead, filter_start, db, current_user, filter_end
    )
    total_enquiries = count_period(Lead)
    new_leads = count_period(Lead, Lead.stage == "NEW")
    qualified_leads = count_period(Lead, Lead.stage == "QUALIFIED")

    surveys_query = _filter_period(
        db.query(SiteSurvey), SiteSurvey, filter_start, db, current_user, filter_end
    )
    pending_surveys = count_period(
        SiteSurvey,
        SiteSurvey.status.in_(["SCHEDULED", "IN_PROGRESS", "SUBMITTED"]),
        SiteSurvey.approval_status != "APPROVED",
    )

    quotations_query = _filter_period(
        db.query(Quotation), Quotation, filter_start, db, current_user, filter_end
    )
    approved_quotations = count_period(
        Quotation, Quotation.status.in_(["APPROVED", "ACCEPTED"])
    )
    orders_query = _filter_period(
        db.query(SalesOrder), SalesOrder, filter_start, db, current_user, filter_end
    )
    confirmed_orders = count_period(SalesOrder, SalesOrder.status != "CANCELLED")

    installations_query = _filter_period(
        db.query(InstallationJob),
        InstallationJob,
        filter_start,
        db,
        current_user,
        filter_end,
    )
    active_installations = count_period(
        InstallationJob,
        InstallationJob.status.in_(["ASSIGNED", "SCHEDULED", "IN_PROGRESS", "TESTING"]),
    )

    completed_installations = count_period(
        InstallationJob,
        InstallationJob.status.in_(["COMPLETED", "CUSTOMER_ACCEPTED"]),
    )

    # Financial & Receivables
    orders = orders_query.all()
    total_revenue = sum(o.total_amount for o in orders)
    payments_query = db.query(Payment).filter(
        Payment.status == "COMPLETED",
        Payment.verified_status == "VERIFIED",
    )
    if start_date is not None:
        payments_query = payments_query.filter(Payment.payment_date >= start_date)
    if end_date is not None:
        payments_query = payments_query.filter(Payment.payment_date < end_date)
    if canonical_role(current_user.role) == "Sales Executive":
        assigned_orders = _scope_dashboard_query(
            db, db.query(SalesOrder.id), SalesOrder, current_user
        )
        payments_query = payments_query.filter(
            Payment.order_id.in_(assigned_orders)
        )
    cash_received = sum(payment.amount or 0 for payment in payments_query.all())
    outstanding_receivables = sum(o.balance_due for o in orders)
    hardware_cost = sum(o.hardware_cost for o in orders)
    labour_cost = sum(o.installation_cost for o in orders)

    expense_amounts = _filter_period(
        db.query(ProjectExpense.amount),
        ProjectExpense,
        filter_start,
        filter_end=filter_end,
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
    tickets_query = _filter_period(
        db.query(ServiceTicket),
        ServiceTicket,
        filter_start,
        db,
        current_user,
        filter_end,
    )
    open_service_tickets = count_period(
        ServiceTicket,
        ServiceTicket.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS", "WAITING_FOR_PARTS"]),
    )
    active_warranties = count_period(
        WarrantyRecord, WarrantyRecord.status == "COVERED"
    )
    pending_subsidies = count_period(
        SubsidyApplication,
        SubsidyApplication.approval_status.in_(["UNDER_REVIEW", "SUBMITTED", "DOCUMENTS_PENDING"]),
    )

    # Charts Data
    # 1. Lead Conversion Funnel
    funnel = [
        {"stage": "Enquiry Received", "count": total_enquiries},
        {"stage": "Qualified", "count": count_period(
            Lead, Lead.stage.in_(["QUALIFIED", "SURVEY_SCHEDULED", "SURVEY_APPROVED", "QUOTATION", "CONVERTED"])
        )},
        {"stage": "Survey Done", "count": count_period(
            SiteSurvey, SiteSurvey.approval_status == "APPROVED"
        )},
        {"stage": "Quotation Sent", "count": count_period(
            Quotation, Quotation.status.in_(["SENT", "ACCEPTED"])
        )},
        {"stage": "Orders Won", "count": confirmed_orders},
        {"stage": "Installed", "count": completed_installations}
    ]

    # 2. Revenue and installation activity from records in the selected period.
    filtered_installations = installations_query.all()
    revenue_by_bucket = {}
    installs_by_bucket = {}

    def period_bucket(created_at):
        created_at = (
            created_at.replace(tzinfo=BUSINESS_TIMEZONE)
            if created_at.tzinfo is None
            else created_at.astimezone(BUSINESS_TIMEZONE)
        )
        created_date = created_at.date()
        if period == "all":
            return created_date.replace(day=1)
        return created_date

    for order in orders:
        if order.created_at is None:
            continue
        bucket = period_bucket(order.created_at)
        revenue_by_bucket[bucket] = revenue_by_bucket.get(bucket, 0) + (order.total_amount or 0)
    for installation in filtered_installations:
        if installation.created_at is None:
            continue
        bucket = period_bucket(installation.created_at)
        installs_by_bucket[bucket] = installs_by_bucket.get(bucket, 0) + 1

    if period == "today":
        trend_buckets = [today]
    elif period == "week":
        trend_buckets = [start_date + timedelta(days=offset) for offset in range(7)]
    elif period == "month":
        trend_buckets = [
            start_date + timedelta(days=offset)
            for offset in range((end_date - start_date).days)
        ]
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
    pending_dispatches = _filter_period(
        db.query(Dispatch), Dispatch, filter_start, db, current_user, filter_end
    ).filter(Dispatch.status == "DISPATCHED", Dispatch.customer_confirmed == False).order_by(Dispatch.id.desc()).limit(5).all()
    recent_payments_query = db.query(Payment)
    if start_date is not None:
        recent_payments_query = recent_payments_query.filter(
            Payment.payment_date >= start_date
        )
    if end_date is not None:
        recent_payments_query = recent_payments_query.filter(
            Payment.payment_date < end_date
        )
    if canonical_role(current_user.role) == "Sales Executive":
        recent_payments_query = recent_payments_query.filter(
            Payment.order_id.in_(
                _scope_dashboard_query(
                    db, db.query(SalesOrder.id), SalesOrder, current_user
                )
            )
        )
    recent_payments = (
        recent_payments_query.order_by(Payment.id.desc()).limit(5).all()
    )
    low_stock_items = db.query(InventoryItem).filter(InventoryItem.quantity <= InventoryItem.reorder_level).limit(5).all()

    response = {
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
    can_view_finance = (
        has_permission(db, current_user, "payments", "VIEW")
        or has_permission(db, current_user, "finance", "VIEW")
    )
    if not can_view_finance:
        response["financials"] = None
        response["metrics"].pop("pending_customer_payments", None)
        response["charts"].pop("revenue_trend", None)
        response["operational"].pop("recent_payments", None)
    if not has_permission(db, current_user, "customers", "VIEW"):
        response["metrics"].pop("total_customers", None)
        response["operational"].pop("upcoming_surveys", None)
    if not has_permission(db, current_user, "leads", "VIEW"):
        for key in ("total_enquiries", "new_leads", "qualified_leads"):
            response["metrics"].pop(key, None)
        response["charts"].pop("funnel", None)
        response["operational"].pop("recent_leads", None)
    if not has_permission(db, current_user, "surveys", "VIEW"):
        response["metrics"].pop("pending_site_surveys", None)
        response["operational"].pop("upcoming_surveys", None)
    if not has_permission(db, current_user, "orders", "VIEW"):
        response["metrics"].pop("approved_quotations", None)
        response["metrics"].pop("confirmed_orders", None)
        response["charts"].pop("project_status_dist", None)
    if not has_permission(db, current_user, "installations", "VIEW"):
        response["metrics"].pop("active_installations", None)
        response["metrics"].pop("completed_installations", None)
        response["operational"].pop("today_installations", None)
    if not has_permission(db, current_user, "inventory", "VIEW"):
        response["metrics"].pop("inventory_valuation", None)
        response["metrics"].pop("low_stock_count", None)
        response["operational"].pop("low_stock_items", None)
    if not has_permission(db, current_user, "service", "VIEW"):
        response["metrics"].pop("open_service_tickets", None)
        response["charts"].pop("ticket_priority_dist", None)
    if not has_permission(db, current_user, "warranties", "VIEW"):
        response["metrics"].pop("active_warranties", None)
    if not has_permission(db, current_user, "subsidies", "VIEW"):
        response["metrics"].pop("pending_subsidies", None)
    if not has_permission(db, current_user, "dispatches", "VIEW"):
        response["operational"].pop("pending_dispatches", None)
    return response
