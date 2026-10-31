import os
import json
import random
import shutil
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.subsidy import SubsidyApplication
from app.models.customer import Customer
from app.models.installation import InstallationJob
from app.schemas.schemas import SubsidyCreate, SubsidyUpdate, SubsidyOut
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/subsidies", tags=["Government Subsidies (PM Surya Ghar)"])


@router.get("", response_model=List[SubsidyOut])
def list_subsidies(
    approval_status: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(SubsidyApplication)
    if approval_status and approval_status != "ALL":
        query = query.filter(SubsidyApplication.approval_status == approval_status)
    if customer_id:
        query = query.filter(SubsidyApplication.customer_id == customer_id)

    subsidies = query.order_by(SubsidyApplication.id.desc()).all()
    results = []
    for s in subsidies:
        results.append(SubsidyOut(
            id=s.id,
            application_number=s.application_number,
            customer_id=s.customer_id,
            customer_name=s.customer.name if s.customer else None,
            customer_phone=s.customer.phone if s.customer else None,
            scheme_name=s.scheme_name,
            installation_id=s.installation_id,
            capacity_kw=s.capacity_kw,
            submission_date=s.submission_date,
            verification_status=s.verification_status,
            approval_status=s.approval_status,
            subsidy_amount=s.subsidy_amount,
            payment_status=s.payment_status,
            documents=s.documents or "[]",
            remarks=s.remarks,
            created_at=s.created_at
        ))
    return results


@router.post("", response_model=SubsidyOut)
def create_subsidy_application(
    payload: SubsidyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    app_num = f"SUB-2026-{random.randint(10000, 99999)}"
    while db.query(SubsidyApplication).filter(SubsidyApplication.application_number == app_num).first():
        app_num = f"SUB-2026-{random.randint(10000, 99999)}"

    # Default subsidy calculation for PM Surya Ghar:
    # 1 kW: ₹30,000; 2 kW: ₹60,000; 3 kW+: ₹78,000
    if payload.capacity_kw <= 1.0:
        default_sub = 30000.0
    elif payload.capacity_kw <= 2.0:
        default_sub = 60000.0
    else:
        default_sub = 78000.0

    subsidy = SubsidyApplication(
        application_number=app_num,
        customer_id=customer.id,
        scheme_name=payload.scheme_name or "PM Surya Ghar Muft Bijli Yojana",
        installation_id=payload.installation_id,
        capacity_kw=payload.capacity_kw,
        submission_date=date.today(),
        verification_status="PENDING",
        approval_status="UNDER_REVIEW",
        subsidy_amount=payload.subsidy_amount or default_sub,
        payment_status="PENDING",
        documents="[]",
        remarks=payload.remarks or f"Submitted by {current_user.name}"
    )
    db.add(subsidy)
    db.commit()
    db.refresh(subsidy)

    return SubsidyOut(
        id=subsidy.id,
        application_number=subsidy.application_number,
        customer_id=subsidy.customer_id,
        customer_name=customer.name,
        customer_phone=customer.phone,
        scheme_name=subsidy.scheme_name,
        installation_id=subsidy.installation_id,
        capacity_kw=subsidy.capacity_kw,
        submission_date=subsidy.submission_date,
        verification_status=subsidy.verification_status,
        approval_status=subsidy.approval_status,
        subsidy_amount=subsidy.subsidy_amount,
        payment_status=subsidy.payment_status,
        documents=subsidy.documents or "[]",
        remarks=subsidy.remarks,
        created_at=subsidy.created_at
    )


@router.put("/{subsidy_id}", response_model=SubsidyOut)
def update_subsidy_status(
    subsidy_id: int,
    payload: SubsidyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(SubsidyApplication).filter(SubsidyApplication.id == subsidy_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subsidy application not found")

    if payload.verification_status is not None:
        sub.verification_status = payload.verification_status
    if payload.approval_status is not None:
        sub.approval_status = payload.approval_status
        if payload.approval_status == "APPROVED":
            sub.verification_status = "VERIFIED"
    if payload.subsidy_amount is not None:
        sub.subsidy_amount = payload.subsidy_amount
    if payload.payment_status is not None:
        sub.payment_status = payload.payment_status
    if payload.remarks is not None:
        sub.remarks = payload.remarks

    db.commit()
    db.refresh(sub)

    return SubsidyOut(
        id=sub.id,
        application_number=sub.application_number,
        customer_id=sub.customer_id,
        customer_name=sub.customer.name if sub.customer else None,
        customer_phone=sub.customer.phone if sub.customer else None,
        scheme_name=sub.scheme_name,
        installation_id=sub.installation_id,
        capacity_kw=sub.capacity_kw,
        submission_date=sub.submission_date,
        verification_status=sub.verification_status,
        approval_status=sub.approval_status,
        subsidy_amount=sub.subsidy_amount,
        payment_status=sub.payment_status,
        documents=sub.documents or "[]",
        remarks=sub.remarks,
        created_at=sub.created_at
    )


@router.post("/{subsidy_id}/upload-doc")
async def upload_subsidy_document(
    subsidy_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(SubsidyApplication).filter(SubsidyApplication.id == subsidy_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subsidy application not found")

    upload_dir = "backend/uploads/subsidies"
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"subsidy_{sub.id}_{random.randint(1000, 9999)}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    rel_url = f"/api/uploads/subsidies/{filename}"
    docs = []
    try:
        docs = json.loads(sub.documents or "[]")
    except Exception:
        docs = []
    docs.append({"name": file.filename, "url": rel_url, "date": str(date.today())})
    sub.documents = json.dumps(docs)
    db.commit()

    return {"success": True, "url": rel_url, "all_documents": docs}

