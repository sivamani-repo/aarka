from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.customer import Customer, Lead
from app.models.survey import SiteSurvey
from app.models.commercial import Quotation, SalesOrder, Payment
from app.models.inventory import Dispatch
from app.models.installation import InstallationJob
from app.models.service import WarrantyRecord, ServiceTicket
from app.schemas.schemas import CustomerCreate, CustomerUpdate, CustomerOut
from app.core.permissions import get_current_user
from app.core.rbac import ASSIGN, canonical_role, has_permission
from app.models.user import User

router = APIRouter(prefix="/api/customers", tags=["Customers"])


def _scope_customers(db: Session, query, current_user: User):
    role = canonical_role(current_user.role)
    if role == "Sales Executive":
        lead_customers = db.query(Lead.customer_id).filter(
            Lead.assigned_user_id == current_user.id
        )
        return query.filter(or_(
            Customer.assigned_user_id == current_user.id,
            Customer.id.in_(lead_customers),
        ))
    if role == "Site Survey Engineer":
        survey_customers = db.query(SiteSurvey.customer_id).filter(
            SiteSurvey.assigned_user_id == current_user.id
        )
        return query.filter(Customer.id.in_(survey_customers))
    if role == "Solar Technician":
        installation_customers = db.query(InstallationJob.customer_id).filter(
            InstallationJob.assigned_user_id == current_user.id
        )
        return query.filter(Customer.id.in_(installation_customers))
    if role == "Dispatch Staff":
        dispatch_customers = db.query(SalesOrder.customer_id).join(
            Dispatch, Dispatch.order_id == SalesOrder.id
        ).filter(Dispatch.assigned_user_id == current_user.id)
        return query.filter(Customer.id.in_(dispatch_customers))
    if role == "Support Executive":
        service_customers = db.query(ServiceTicket.customer_id).filter(
            ServiceTicket.assigned_user_id == current_user.id
        )
        return query.filter(Customer.id.in_(service_customers))
    return query


def _resolve_customer_assignee(db: Session, current_user: User, requested_id: Optional[int]):
    if canonical_role(current_user.role) == "Sales Executive":
        if requested_id not in (None, current_user.id):
            raise HTTPException(status_code=403, detail="Sales executives can only assign customers to themselves.")
        return current_user.id
    if requested_id is None:
        return None
    if not has_permission(db, current_user, "customers", ASSIGN):
        raise HTTPException(status_code=403, detail="Customer assignment permission is required.")
    assigned_user = db.query(User).filter(User.id == requested_id, User.is_active.is_(True)).first()
    if not assigned_user or canonical_role(assigned_user.role) not in {"Sales Executive", "Sales Manager"}:
        raise HTTPException(status_code=400, detail="Select an active employee in the Sales department.")
    return assigned_user.id


@router.get("", response_model=List[CustomerOut])
def list_customers(
    search: Optional[str] = None,
    customer_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = _scope_customers(db, db.query(Customer), current_user)
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Customer.name.ilike(search_filter),
                Customer.phone.ilike(search_filter),
                Customer.email.ilike(search_filter),
                Customer.city.ilike(search_filter)
            )
        )
    if customer_type and customer_type != "ALL":
        query = query.filter(Customer.customer_type == customer_type)

    customers = query.order_by(Customer.id.desc()).all()
    return customers


@router.post("", response_model=CustomerOut)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clean_phone = payload.phone.strip()
    existing = db.query(Customer).filter(Customer.phone == clean_phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Customer with this phone number already exists")

    assigned_user_id = _resolve_customer_assignee(db, current_user, payload.assigned_user_id)
    customer = Customer(
        name=payload.name.strip(),
        phone=clean_phone,
        email=payload.email.strip() if payload.email else None,
        address=payload.address.strip(),
        city=payload.city.strip() if payload.city else "Hyderabad",
        customer_type=payload.customer_type,
        lead_source=payload.lead_source,
        required_capacity_kw=payload.required_capacity_kw,
        solar_requirement=payload.solar_requirement,
        monthly_bill=payload.monthly_bill,
        subsidy_required=payload.subsidy_required,
        status="ACTIVE",
        assigned_user_id=assigned_user_id,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}")
def get_customer_details(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = _scope_customers(db, db.query(Customer), current_user).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    leads = db.query(Lead).filter(Lead.customer_id == customer_id).order_by(Lead.id.desc()).all() if has_permission(db, current_user, "leads") else []
    surveys = db.query(SiteSurvey).filter(SiteSurvey.customer_id == customer_id).order_by(SiteSurvey.id.desc()).all() if has_permission(db, current_user, "surveys") else []
    quotations = db.query(Quotation).filter(Quotation.customer_id == customer_id).order_by(Quotation.id.desc()).all() if has_permission(db, current_user, "quotations") else []
    orders = db.query(SalesOrder).filter(SalesOrder.customer_id == customer_id).order_by(SalesOrder.id.desc()).all() if has_permission(db, current_user, "orders") else []
    installations = db.query(InstallationJob).filter(InstallationJob.customer_id == customer_id).order_by(InstallationJob.id.desc()).all() if has_permission(db, current_user, "installations") else []
    warranties = db.query(WarrantyRecord).filter(WarrantyRecord.customer_id == customer_id).order_by(WarrantyRecord.id.desc()).all() if has_permission(db, current_user, "warranties") else []
    tickets = db.query(ServiceTicket).filter(ServiceTicket.customer_id == customer_id).order_by(ServiceTicket.id.desc()).all() if has_permission(db, current_user, "service") else []

    if canonical_role(current_user.role) == "Sales Executive":
        leads = [lead for lead in leads if lead.assigned_user_id == current_user.id]
        lead_ids = [lead.id for lead in leads]
        quotations = [quote for quote in quotations if quote.lead_id in lead_ids]
        if lead_ids:
            quote_ids = db.query(Quotation.id).filter(Quotation.lead_id.in_(lead_ids))
            orders = [order for order in orders if order.quotation_id in quote_ids]
        else:
            orders = []
    if canonical_role(current_user.role) == "Site Survey Engineer":
        surveys = [survey for survey in surveys if survey.assigned_user_id == current_user.id]
    if canonical_role(current_user.role) == "Solar Technician":
        installations = [job for job in installations if job.assigned_user_id == current_user.id]
    if canonical_role(current_user.role) == "Support Executive":
        tickets = [ticket for ticket in tickets if ticket.assigned_user_id == current_user.id]

    return {
        "customer": CustomerOut.from_orm(customer),
        "history": {
            "leads": [
                {"id": l.id, "ref": l.lead_reference, "stage": l.stage, "status": l.status, "capacity": l.required_capacity_kw, "date": l.created_at}
                for l in leads
            ],
            "surveys": [
                {"id": s.id, "ref": s.survey_reference, "status": s.status, "approval": s.approval_status, "date": s.scheduled_date}
                for s in surveys
            ],
            "quotations": [
                {"id": q.id, "ref": q.quotation_number, "status": q.status, "amount": q.total_amount, "capacity": q.capacity_kw, "date": q.created_at}
                for q in quotations
            ],
            "orders": [
                {"id": o.id, "ref": o.order_number, "status": o.status, "amount": o.total_amount, "advance": o.advance_paid, "balance": o.balance_due, "date": o.created_at}
                for o in orders
            ],
            "installations": [
                {"id": i.id, "job_number": i.job_number, "status": i.status, "date": i.scheduled_date}
                for i in installations
            ],
            "warranties": [
                {"id": w.id, "serial": w.serial_number, "status": w.status, "start": w.warranty_start, "end": w.warranty_end}
                for w in warranties
            ],
            "service_tickets": [
                {"id": t.id, "ref": t.ticket_number, "status": t.status, "fault": t.fault_description, "priority": t.priority, "date": t.created_at}
                for t in tickets
            ]
        }
    }


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = _scope_customers(db, db.query(Customer), current_user).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if payload.name is not None:
        customer.name = payload.name
    if payload.phone is not None:
        customer.phone = payload.phone
    if payload.email is not None:
        customer.email = payload.email
    if payload.address is not None:
        customer.address = payload.address
    if payload.city is not None:
        customer.city = payload.city
    if payload.customer_type is not None:
        customer.customer_type = payload.customer_type
    if payload.status is not None:
        customer.status = payload.status
    if payload.monthly_bill is not None:
        customer.monthly_bill = payload.monthly_bill
    if payload.required_capacity_kw is not None:
        customer.required_capacity_kw = payload.required_capacity_kw
    if "assigned_user_id" in payload.model_fields_set:
        customer.assigned_user_id = _resolve_customer_assignee(
            db, current_user, payload.assigned_user_id
        )

    db.commit()
    db.refresh(customer)
    return customer
