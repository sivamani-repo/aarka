import random
from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer, Lead
from app.models.product import Package
from app.schemas.schemas import PublicEnquiryRequest, PackageOut

router = APIRouter(prefix="/api/public", tags=["Public Portal"])


@router.post("/enquiry")
def submit_public_enquiry(payload: PublicEnquiryRequest, db: Session = Depends(get_db)):
    # 1. Customer deduplication check by phone number
    clean_phone = payload.phone.strip()
    customer = db.query(Customer).filter(Customer.phone == clean_phone).first()

    if not customer:
        customer = Customer(
            name=payload.customer_name.strip(),
            phone=clean_phone,
            email=payload.email.strip() if payload.email else None,
            address=payload.address.strip(),
            city=payload.city.strip() if payload.city else "Hyderabad",
            customer_type=payload.customer_category,
            lead_source=payload.lead_source,
            required_capacity_kw=payload.required_capacity,
            solar_requirement=payload.solar_requirement,
            monthly_bill=payload.monthly_electricity_bill,
            subsidy_required=payload.subsidy_requirement,
            status="ACTIVE"
        )
        db.add(customer)
        db.flush()
    else:
        customer.monthly_bill = payload.monthly_electricity_bill
        customer.required_capacity_kw = payload.required_capacity
        customer.solar_requirement = payload.solar_requirement

    # 2. Generate unique lead reference
    rand_suffix = random.randint(1000, 9999)
    lead_ref = f"LEAD-{rand_suffix}"
    # Verify uniqueness
    while db.query(Lead).filter(Lead.lead_reference == lead_ref).first():
        lead_ref = f"LEAD-{random.randint(1000, 9999)}"

    # 3. Create Lead
    lead = Lead(
        lead_reference=lead_ref,
        customer_id=customer.id,
        customer_name=customer.name,
        phone=clean_phone,
        email=customer.email,
        address=customer.address,
        city=customer.city,
        customer_type=customer.customer_type,
        lead_source=payload.lead_source,
        preferred_contact_method=payload.preferred_contact_method,
        required_capacity_kw=payload.required_capacity,
        solar_requirement=payload.solar_requirement,
        monthly_bill=payload.monthly_electricity_bill,
        subsidy_required=payload.subsidy_requirement,
        privacy_consent_at=datetime.now(timezone.utc),
        estimated_value=payload.required_capacity * 65000.0,
        stage="NEW",
        status="OPEN",
        notes=payload.additional_requirements or "Inquiry received from public solar inquiry portal."
    )
    db.add(lead)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="The enquiry could not be saved due to a conflicting record. Please try again.",
        ) from exc
    db.refresh(lead)

    return {
        "success": True,
        "message": "Thank you! Your solar inquiry has been received. Our sales engineer will contact you shortly.",
        "lead_reference": lead.lead_reference,
    }


@router.get("/packages", response_model=List[PackageOut])
def list_public_packages(db: Session = Depends(get_db)):
    packages = db.query(Package).order_by(Package.capacity_kw.asc(), Package.package_type.asc()).all()
    return packages
