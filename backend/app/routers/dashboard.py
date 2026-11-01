from typing import Optional, Literal
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

from app.database import get_db
from app.models.customer import Customer, Lead
from app.models.survey import SiteSurvey
from app.models.commercial import Quotation, SalesOrder, Payment
from app.models.finance import Invoice
from app.models.inventory import InventoryItem, Dispatch
from app.models.installation import InstallationJob
from app.models.service import ServiceTicket, WarrantyRecord
from app.models.finance import ProjectExpense
from app.models.subsidy import SubsidyApplication
from app.core.permissions import get_current_user
from app.core.rbac import DIRECTOR_ROLES, canonical_role, has_permission
from app.models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["Operational Dashboard"])
DASHBOARD_TIMEZONE = ZoneInfo("Asia/Kolkata")


def _dashboard_period_window(
    period: str,
    now: Optional[datetime] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    today = (now or datetime.now(DASHBOARD_TIMEZONE)).astimezone(DASHBOARD_TIMEZONE).date()
    if period == "custom":
        if start_date is None or end_date is None or start_date > end_date:
            raise HTTPException(
                status_code=422,
                detail="Custom reporting requires a valid start_date and end_date.",
            )
        if (end_date - start_date).days > 365:
            raise HTTPException(
                status_code=422,
                detail="Custom reporting ranges cannot exceed 366 days.",
            )
        period_start = start_date
        period_end = end_date + timedelta(days=1)
    elif period == "today":
        period_start = today
        period_end = today + timedelta(days=1)
    elif period == "week":
        period_start = today - timedelta(days=today.weekday())
        period_end = today + timedelta(days=1)
    elif period == "month":
        period_start = today.replace(day=1)
        period_end = today + timedelta(days=1)
    else:
        return today, None, None

    start = datetime.combine(period_start, time.min, tzinfo=DASHBOARD_TIMEZONE)
    end = datetime.combine(period_end, time.min, tzinfo=DASHBOARD_TIMEZONE)
    return today, start, end


def _dashboard_local_date(value: datetime) -> date:
    return value.astimezone(DASHBOARD_TIMEZONE).date()


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
    period: Literal["today", "week", "month", "all", "custom"] = Query("all"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today, filter_start, filter_end = _dashboard_period_window(
        period, start_date=start_date, end_date=end_date
    )

    # 1. Business Metrics
    total_customers = _count_period(
        db, Customer, filter_start, current_user=current_user, filter_end=filter_end
    )
    leads_query = _filter_period(
        db.query(Lead), Lead, filter_start, db, current_user, filter_end
    )
    total_enquiries = _count_period(
        db, Lead, filter_start, current_user=current_user, filter_end=filter_end
    )
    new_leads = _count_period(
        db, Lead, filter_start, Lead.stage == "NEW",
        current_user=current_user, filter_end=filter_end,
    )
    qualified_leads = _count_period(
        db, Lead, filter_start, Lead.stage == "QUALIFIED",
        current_user=current_user, filter_end=filter_end,
    )

    surveys_query = _filter_period(
        db.query(SiteSurvey), SiteSurvey, filter_start, db, current_user, filter_end
    )
    pending_surveys = _count_period(db, SiteSurvey, None,
        SiteSurvey.status.in_(["SCHEDULED", "IN_PROGRESS", "SUBMITTED"]),
        SiteSurvey.approval_status != "APPROVED",
        current_user=current_user,
    )

    quotations_query = _filter_period(
        db.query(Quotation), Quotation, filter_start, db, current_user, filter_end
    )
    approved_quotations = _count_period(
        db, Quotation, filter_start, Quotation.status.in_(["APPROVED", "ACCEPTED"]),
        current_user=current_user, filter_end=filter_end,
    )
    orders_query = _filter_period(
        db.query(SalesOrder), SalesOrder, filter_start, db, current_user, filter_end
    )
    confirmed_orders = _count_period(
        db, SalesOrder, filter_start, SalesOrder.status != "CANCELLED",
        current_user=current_user, filter_end=filter_end,
    )

    installations_query = _filter_period(
        db.query(InstallationJob), InstallationJob, filter_start, db, current_user, filter_end
    )
    active_installations = _count_period(
        db, InstallationJob, None,
        InstallationJob.status.in_(["ASSIGNED", "SCHEDULED", "IN_PROGRESS", "TESTING"]),
        current_user=current_user,
    )

    completed_installations = _count_period(
        db, InstallationJob, filter_start,
        InstallationJob.status.in_(["COMPLETED", "CUSTOMER_ACCEPTED"]),
        current_user=current_user, filter_end=filter_end,
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
        db.query(ServiceTicket), ServiceTicket, filter_start, db, current_user, filter_end
    )
    open_service_tickets = _count_period(
        db, ServiceTicket, None,
        ServiceTicket.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS", "WAITING_FOR_PARTS"]),
        current_user=current_user,
    )
    active_warranties = _count_period(
        db, WarrantyRecord, None, WarrantyRecord.status == "COVERED",
        current_user=current_user,
    )
    pending_subsidies = _count_period(
        db, SubsidyApplication, None,
        SubsidyApplication.approval_status.in_(["UNDER_REVIEW", "SUBMITTED", "DOCUMENTS_PENDING"]),
        current_user=current_user,
    )

    # Charts Data
    # 1. Lead Conversion Funnel
    funnel = [
        {"stage": "Enquiry Received", "count": total_enquiries},
        {"stage": "Qualified", "count": _count_period(
            db, Lead, filter_start,
            Lead.stage.in_(["QUALIFIED", "SURVEY_SCHEDULED", "SURVEY_APPROVED", "QUOTATION", "CONVERTED"]),
                current_user=current_user, filter_end=filter_end,
        )},
        {"stage": "Survey Done", "count": _count_period(
            db, SiteSurvey, filter_start, SiteSurvey.approval_status == "APPROVED",
            current_user=current_user, filter_end=filter_end,
        )},
        {"stage": "Quotation Sent", "count": _count_period(
            db, Quotation, filter_start, Quotation.status.in_(["SENT", "ACCEPTED"]),
            current_user=current_user, filter_end=filter_end,
        )},
        {"stage": "Orders Won", "count": confirmed_orders},
        {"stage": "Installed", "count": completed_installations}
    ]

    # 2. Revenue and installation activity from records in the selected period.
    filtered_installations = installations_query.all()
    revenue_by_bucket = {}
    installs_by_bucket = {}

    def period_bucket(created_at):
        created_date = _dashboard_local_date(created_at)
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
        period_start = filter_start.date()
        trend_buckets = [
            period_start + timedelta(days=offset)
            for offset in range((today - period_start).days + 1)
        ]
    elif period == "month":
        period_start = filter_start.date()
        trend_buckets = [
            period_start + timedelta(days=offset)
            for offset in range((today - period_start).days + 1)
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
    upcoming_surveys = _scope_dashboard_query(
        db, db.query(SiteSurvey), SiteSurvey, current_user
    ).filter(
        SiteSurvey.status.in_(["SCHEDULED", "IN_PROGRESS"]),
        SiteSurvey.scheduled_date >= today,
    ).order_by(SiteSurvey.scheduled_date.asc()).limit(5).all()
    today_installs = _scope_dashboard_query(
        db, db.query(InstallationJob), InstallationJob, current_user
    ).filter(
        InstallationJob.status.in_(["SCHEDULED", "IN_PROGRESS", "ASSIGNED"]),
        InstallationJob.scheduled_date == today,
    ).order_by(InstallationJob.scheduled_date.asc()).limit(5).all()
    pending_dispatches = _scope_dashboard_query(
        db, db.query(Dispatch), Dispatch, current_user
    ).filter(
        Dispatch.status == "DISPATCHED",
        Dispatch.customer_confirmed.is_(False),
    ).order_by(Dispatch.id.desc()).limit(5).all()
    recent_payments = _filter_period(
        db.query(Payment), Payment, filter_start, filter_end=filter_end
    ).order_by(Payment.id.desc()).limit(5).all()
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


def _director_date_filter(query, column, start_date, end_date):
    if start_date is not None:
        query = query.filter(column >= start_date)
    if end_date is not None:
        query = query.filter(column < end_date)
    return query


@router.get("/director-summary")
def get_director_command_summary(
    period: Literal["today", "week", "month", "all", "custom"] = Query("month"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in DIRECTOR_ROLES:
        raise HTTPException(status_code=403, detail="Director access is required.")

    today, start_at, end_at = _dashboard_period_window(
        period, start_date=start_date, end_date=end_date
    )
    date_start = start_at.date() if start_at else None
    date_end = end_at.date() if end_at else None

    def period_orders(window_start, window_end):
        query = db.query(SalesOrder).filter(SalesOrder.status != "CANCELLED")
        if window_start is not None:
            query = query.filter(SalesOrder.created_at >= window_start)
        if window_end is not None:
            query = query.filter(SalesOrder.created_at < window_end)
        return query.all()

    def recognized_period_orders(window_start, window_end):
        installations = db.query(InstallationJob.order_id).filter(
            InstallationJob.status.in_(["COMPLETED", "CUSTOMER_ACCEPTED"]),
            InstallationJob.end_time.is_not(None),
        )
        if window_start is not None:
            installations = installations.filter(
                InstallationJob.end_time >= window_start
            )
        if window_end is not None:
            installations = installations.filter(
                InstallationJob.end_time < window_end
            )
        return db.query(SalesOrder).filter(
            SalesOrder.id.in_(installations),
            SalesOrder.status.in_(["COMPLETED", "CUSTOMER_ACCEPTED"]),
        ).all()

    def period_expenses(window_start, window_end):
        query = db.query(ProjectExpense)
        if window_start is not None:
            window_start_date = window_start.date()
            query = query.filter(or_(
                and_(
                    ProjectExpense.expense_date.is_not(None),
                    ProjectExpense.expense_date >= window_start_date,
                ),
                and_(
                    ProjectExpense.expense_date.is_(None),
                    ProjectExpense.created_at >= window_start,
                ),
            ))
        if window_end is not None:
            window_end_date = window_end.date()
            query = query.filter(or_(
                and_(
                    ProjectExpense.expense_date.is_not(None),
                    ProjectExpense.expense_date < window_end_date,
                ),
                and_(
                    ProjectExpense.expense_date.is_(None),
                    ProjectExpense.created_at < window_end,
                ),
            ))
        return query.all()

    orders = period_orders(start_at, end_at)
    expenses = period_expenses(start_at, end_at)
    recognized_orders = recognized_period_orders(start_at, end_at)
    revenue = sum(order.total_amount or 0 for order in recognized_orders)
    contract_value = sum(order.total_amount or 0 for order in orders)

    payments_query = db.query(Payment).filter(
        Payment.status == "COMPLETED",
        Payment.verified_status == "VERIFIED",
    )
    payments_query = _director_date_filter(
        payments_query, Payment.payment_date, date_start, date_end
    )
    cash_received = sum(payment.amount or 0 for payment in payments_query.all())

    direct_costs = sum(
        (order.hardware_cost or 0) + (order.installation_cost or 0)
        for order in recognized_orders
    )
    transportation_costs = sum(
        expense.amount or 0
        for expense in expenses
        if expense.category == "TRANSPORTATION"
        and expense.order_id in {order.id for order in recognized_orders}
    )
    operating_expenses = sum(
        (expense.amount or 0) + (expense.gst_amount or 0)
        for expense in expenses
        if expense.category not in {"TRANSPORTATION", "HARDWARE", "LABOUR"}
    )
    total_expenses = direct_costs + transportation_costs + operating_expenses
    gross_profit = revenue - direct_costs - transportation_costs
    net_profit = gross_profit - operating_expenses

    previous_start = previous_end = None
    if start_at is not None and end_at is not None:
        duration = end_at - start_at
        previous_start = start_at - duration
        previous_end = start_at
    previous_revenue = None
    previous_expenses_total = None
    previous_net_profit = None
    previous_cash_received = None
    if previous_start is not None and previous_end is not None:
        previous_recognized_orders = recognized_period_orders(
            previous_start, previous_end
        )
        previous_revenue = sum(
            order.total_amount or 0 for order in previous_recognized_orders
        )
        previous_expenses = period_expenses(previous_start, previous_end)
        previous_direct_costs = sum(
            (order.hardware_cost or 0) + (order.installation_cost or 0)
            for order in previous_recognized_orders
        )
        previous_transport_costs = sum(
            expense.amount or 0
            for expense in previous_expenses
            if expense.category == "TRANSPORTATION"
            and expense.order_id in {
                order.id for order in previous_recognized_orders
            }
        )
        previous_operating_expenses = sum(
            (expense.amount or 0) + (expense.gst_amount or 0)
            for expense in previous_expenses
            if expense.category not in {"TRANSPORTATION", "HARDWARE", "LABOUR"}
        )
        previous_expenses_total = (
            previous_direct_costs + previous_transport_costs
            + previous_operating_expenses
        )
        previous_net_profit = (
            previous_revenue
            - previous_direct_costs
            - previous_transport_costs
            - previous_operating_expenses
        )
        previous_payments = db.query(Payment).filter(
            Payment.status == "COMPLETED",
            Payment.verified_status == "VERIFIED",
            Payment.payment_date >= previous_start.date(),
            Payment.payment_date < previous_end.date(),
        ).all()
        previous_cash_received = sum(
            payment.amount or 0 for payment in previous_payments
        )

    inventory = db.query(InventoryItem).all()
    inventory_value = sum(
        (item.quantity or 0) * (item.unit_price or 0) for item in inventory
    )
    low_stock_items = [
        item for item in inventory
        if (item.quantity or 0) <= (item.reorder_level or 0)
    ][:8]
    active_installation_statuses = {
        "ASSIGNED", "SCHEDULED", "IN_PROGRESS", "TESTING"
    }
    unfinished_installations = db.query(InstallationJob).filter(
        InstallationJob.status.notin_(["COMPLETED", "CUSTOMER_ACCEPTED", "CANCELLED"])
    ).order_by(InstallationJob.scheduled_date.asc().nullslast()).all()
    delayed_installations = [
        installation
        for installation in unfinished_installations
        if installation.scheduled_date is not None
        and installation.scheduled_date < today
    ]
    open_tickets = db.query(ServiceTicket).filter(
        ServiceTicket.status.in_(
            ["OPEN", "ASSIGNED", "IN_PROGRESS", "WAITING_FOR_PARTS"]
        )
    ).count()
    pending_subsidies = db.query(func.count(SubsidyApplication.id)).filter(
        SubsidyApplication.approval_status.notin_(["APPROVED", "REJECTED", "DISBURSED"]),
    ).scalar() or 0

    invoices = db.query(
        Invoice.invoice_number,
        Invoice.balance_due,
        Invoice.due_date,
    ).all()
    pending_invoices = [
        {"number": number, "balance_due": balance_due or 0, "due_date": due_date}
        for number, balance_due, due_date in invoices
        if (balance_due or 0) > 0
    ]
    overdue_invoices = [
        invoice for invoice in pending_invoices
        if invoice["due_date"] is not None and invoice["due_date"] < today
    ]

    order_ids = [order.id for order in orders]
    linked_expenses = {}
    if order_ids:
        for expense in db.query(ProjectExpense).filter(
            ProjectExpense.order_id.in_(order_ids)
        ).all():
            linked_expenses.setdefault(expense.order_id, []).append(expense)

    installation_by_order = {
        installation.order_id: installation
        for installation in db.query(InstallationJob).filter(
            InstallationJob.order_id.in_(order_ids or [-1])
        ).all()
    }
    current_orders = db.query(SalesOrder).filter(
        SalesOrder.status != "CANCELLED"
    ).all()
    projects = []
    for order in sorted(
        orders,
        key=lambda item: item.created_at.timestamp() if item.created_at else 0,
        reverse=True,
    )[:12]:
        project_expenses = linked_expenses.get(order.id, [])
        transport = sum(
            expense.amount or 0
            for expense in project_expenses
            if expense.category == "TRANSPORTATION"
        )
        other = sum(
            (expense.amount or 0) + (expense.gst_amount or 0)
            for expense in project_expenses
            if expense.category not in {"TRANSPORTATION", "HARDWARE", "LABOUR"}
        )
        project_cost = (
            (order.hardware_cost or 0)
            + (order.installation_cost or 0)
            + transport
            + other
        )
        installation = installation_by_order.get(order.id)
        projects.append({
            "id": order.id,
            "reference": order.order_number,
            "customer": order.customer.name if order.customer else "Customer record unavailable",
            "capacity_kw": order.capacity_kw,
            "contract_value": round(order.total_amount or 0, 2),
            "recorded_cost": round(project_cost, 2),
            "contribution": round((order.total_amount or 0) - project_cost, 2),
            "advance_paid": round(order.advance_paid or 0, 2),
            "balance_due": round(order.balance_due or 0, 2),
            "cost_breakdown": {
                "panels_and_hardware": round(order.hardware_cost or 0, 2),
                "installation_labour": round(order.installation_cost or 0, 2),
                "transportation": round(transport, 2),
                "other_recorded_expenses": round(other, 2),
            },
            "margin_percentage": round(
                (((order.total_amount or 0) - project_cost) / order.total_amount * 100), 2
            ) if order.total_amount else None,
            "cost_data_available": bool(
                order.hardware_cost or order.installation_cost or project_expenses
            ),
            "status": order.status,
            "installation_status": installation.status if installation else None,
        })

    def percentage_change(current, previous):
        if previous == 0:
            return None
        return round((current - previous) / abs(previous) * 100, 2)

    alerts = []
    for project in projects:
        if project["cost_data_available"] and project["contribution"] < 0:
            alerts.append({
                "severity": "critical",
                "title": f"Loss-making project: {project['reference']}",
                "description": project["customer"],
                "href": "/finance",
            })
    for invoice in overdue_invoices[:5]:
        alerts.append({
            "severity": "high",
            "title": f"Overdue invoice: {invoice['number']}",
            "description": f"₹{round(invoice['balance_due']):,} outstanding",
            "href": "/payments",
        })
    if low_stock_items:
        alerts.append({
            "severity": "medium",
            "title": f"{len(low_stock_items)} low-stock item(s)",
            "description": "Review warehouse reorder levels.",
            "href": "/inventory",
        })
    for installation in delayed_installations[:5]:
        alerts.append({
            "severity": "high",
            "title": f"Delayed installation: {installation.job_number or f'JOB-{installation.id}'}",
            "description": (
                f"Scheduled for {installation.scheduled_date.isoformat()}."
            ),
            "href": "/installations",
        })
    if pending_subsidies:
        alerts.append({
            "severity": "medium",
            "title": f"{pending_subsidies} subsidy application(s) need attention",
            "description": "Review verification and official processing status.",
            "href": "/subsidies",
        })

    return {
        "period": period,
        "date_start": date_start,
        "date_end": (date_end - timedelta(days=1)) if date_end else None,
        "generated_at": datetime.now(DASHBOARD_TIMEZONE),
        "financials": {
            "recognized_revenue": round(revenue, 2),
            "contract_value": round(contract_value, 2),
            "cash_received": round(cash_received, 2),
            "advance_payments": round(
                sum(order.advance_paid or 0 for order in current_orders), 2
            ),
            "outstanding_receivables": round(
                sum(order.balance_due or 0 for order in current_orders), 2
            ),
            "recorded_expenses": round(total_expenses, 2),
            "gross_profit": round(gross_profit, 2),
            "net_profit": round(net_profit, 2),
            "revenue_change_percentage": (
                percentage_change(revenue, previous_revenue)
                if previous_revenue is not None else None
            ),
            "expenses_change_percentage": (
                percentage_change(total_expenses, previous_expenses_total)
                if previous_expenses_total is not None else None
            ),
            "profit_change_percentage": (
                percentage_change(net_profit, previous_net_profit)
                if previous_net_profit is not None else None
            ),
            "cash_change_percentage": (
                percentage_change(cash_received, previous_cash_received)
                if previous_cash_received is not None else None
            ),
            "previous_recognized_revenue": (
                round(previous_revenue, 2) if previous_revenue is not None else None
            ),
            "pending_supplier_payables": None,
            "pending_technician_payments": None,
        },
        "operations": {
            "active_installations": sum(
                1 for installation in unfinished_installations
                if installation.status in active_installation_statuses
            ),
            "unfinished_installations": len(unfinished_installations),
            "delayed_installations": len(delayed_installations),
            "open_service_tickets": open_tickets,
            "pending_subsidies": pending_subsidies,
            "pending_invoices": len(pending_invoices),
            "overdue_invoices": len(overdue_invoices),
            "inventory_value": round(inventory_value, 2),
            "low_stock_items": [
                {
                    "id": item.id,
                    "name": item.product.name if item.product else item.sku,
                    "quantity": item.quantity,
                    "reorder_level": item.reorder_level,
                }
                for item in low_stock_items
            ],
        },
        "projects": projects,
        "alerts": alerts,
        "data_gaps": [
            "Technician wage and payment records are not available in the current system.",
            "Supplier payable balances are not available in the current system.",
            "Project contribution uses recorded order costs and linked expense records only.",
        ],
    }
