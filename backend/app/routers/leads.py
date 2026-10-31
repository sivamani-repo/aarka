import random
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.customer import Customer, Lead
from app.schemas.schemas import LeadCreate, LeadUpdate, LeadQualify, LeadOut
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/leads", tags=["Leads"])


@router.get("", response_model=List[LeadOut])
def list_leads(
    search: Optional[str] = None,
    stage: Optional[str] = None,
    source: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Lead)
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Lead.customer_name.ilike(search_filter),
                Lead.phone.ilike(search_filter),
                Lead.lead_reference.ilike(search_filter),
                Lead.city.ilike(search_filter)
            )
        )
    if stage and stage != "ALL":
        query = query.filter(Lead.stage == stage)
    if source and source != "ALL":
        query = query.filter(Lead.lead_source == source)

    leads = query.order_by(Lead.id.desc()).all()
    return leads


@router.post("", response_model=LeadOut)
def create_lead(
    payload: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clean_phone = payload.phone.strip()
    customer = db.query(Customer).filter(Customer.phone == clean_phone).first()
    if not customer:
        customer = Customer(
            name=payload.customer_name.strip(),
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
            status="ACTIVE"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    lead_ref = f"LEAD-{random.randint(1000, 9999)}"
    while db.query(Lead).filter(Lead.lead_reference == lead_ref).first():
        lead_ref = f"LEAD-{random.randint(1000, 9999)}"

    est_value = payload.estimated_value or (payload.required_capacity_kw * 65000.0)

    lead = Lead(
        lead_reference=lead_ref,
        customer_id=customer.id,
        customer_name=payload.customer_name.strip(),
        phone=clean_phone,
        email=payload.email.strip() if payload.email else None,
        address=payload.address.strip(),
        city=payload.city.strip() if payload.city else "Hyderabad",
        customer_type=payload.customer_type,
        lead_source=payload.lead_source,
        preferred_contact_method=payload.preferred_contact_method,
        required_capacity_kw=payload.required_capacity_kw,
        solar_requirement=payload.solar_requirement,
        monthly_bill=payload.monthly_bill,
        subsidy_required=payload.subsidy_required,
        roof_availability=payload.roof_availability,
        grid_suitable=payload.grid_suitable,
        estimated_value=est_value,
        assigned_sales_rep=payload.assigned_sales_rep or current_user.name,
        stage="NEW",
        status="OPEN",
        notes=payload.notes
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/{lead_id}", response_model=LeadOut)
def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if payload.customer_name is not None:
        lead.customer_name = payload.customer_name
    if payload.phone is not None:
        lead.phone = payload.phone
    if payload.email is not None:
        lead.email = payload.email
    if payload.address is not None:
        lead.address = payload.address
    if payload.city is not None:
        lead.city = payload.city
    if payload.required_capacity_kw is not None:
        lead.required_capacity_kw = payload.required_capacity_kw
    if payload.solar_requirement is not None:
        lead.solar_requirement = payload.solar_requirement
    if payload.monthly_bill is not None:
        lead.monthly_bill = payload.monthly_bill
    if payload.assigned_sales_rep is not None:
        lead.assigned_sales_rep = payload.assigned_sales_rep
    if payload.follow_up_date is not None:
        lead.follow_up_date = payload.follow_up_date
    if payload.stage is not None:
        lead.stage = payload.stage
    if payload.status is not None:
        lead.status = payload.status
    if payload.notes is not None:
        lead.notes = payload.notes
    if payload.roof_availability is not None:
        lead.roof_availability = payload.roof_availability
    if payload.grid_suitable is not None:
        lead.grid_suitable = payload.grid_suitable
    if payload.estimated_value is not None:
        lead.estimated_value = payload.estimated_value

    db.commit()
    db.refresh(lead)
    return lead


@router.post("/{lead_id}/qualify", response_model=LeadOut)
def qualify_lead(
    lead_id: int,
    payload: LeadQualify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.stage = "QUALIFIED"
    lead.roof_availability = payload.shadow_free_roof_space
    lead.monthly_bill = payload.monthly_electricity_bill
    lead.grid_suitable = payload.grid_suitability
    lead.estimated_value = payload.estimated_opportunity_value

    qualify_note = f"Lead qualified by {current_user.name}. Roof space: {payload.shadow_free_roof_space}. Customer interest: {payload.customer_interest}. {payload.notes or ''}"
    lead.notes = f"{lead.notes or ''}\n\n[QUALIFICATION] {qualify_note}".strip()

    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}")
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()
    return {"success": True, "message": "Lead deleted"}

