import os
import json
import random
import shutil
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.survey import SiteSurvey, Technician
from app.models.customer import Customer, Lead
from app.schemas.schemas import SurveyCreate, SurveyUpdate, SurveyApprove, SurveyOut
from app.core.permissions import get_current_user
from app.core.rbac import ASSIGN, canonical_role, has_permission
from app.models.user import User

router = APIRouter(prefix="/api/surveys", tags=["Site Surveys"])


def _scope_surveys(query, current_user: User):
    if canonical_role(current_user.role) == "Site Survey Engineer":
        return query.filter(SiteSurvey.assigned_user_id == current_user.id)
    return query


def _resolve_survey_assignee(db: Session, current_user: User, requested_id: Optional[int]):
    if canonical_role(current_user.role) == "Site Survey Engineer":
        if requested_id not in (None, current_user.id):
            raise HTTPException(status_code=403, detail="Survey engineers can only assign surveys to themselves.")
        return current_user.id
    if requested_id is None:
        return None
    if not has_permission(db, current_user, "surveys", ASSIGN):
        raise HTTPException(status_code=403, detail="Survey assignment permission is required.")
    assignee = db.query(User).filter(User.id == requested_id, User.is_active.is_(True)).first()
    if not assignee or canonical_role(assignee.role) != "Site Survey Engineer":
        raise HTTPException(status_code=400, detail="Select an active Site Survey Engineer.")
    return assignee.id


@router.get("", response_model=List[SurveyOut])
def list_surveys(
    status: Optional[str] = None,
    approval_status: Optional[str] = None,
    technician_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = _scope_surveys(db.query(SiteSurvey), current_user)
    if status and status != "ALL":
        query = query.filter(SiteSurvey.status == status)
    if approval_status and approval_status != "ALL":
        query = query.filter(SiteSurvey.approval_status == approval_status)
    if technician_id:
        query = query.filter(SiteSurvey.technician_id == technician_id)

    surveys = query.order_by(SiteSurvey.id.desc()).all()
    results = []
    for s in surveys:
        s_out = SurveyOut(
            id=s.id,
            survey_reference=s.survey_reference,
            lead_id=s.lead_id,
            customer_id=s.customer_id,
            technician_id=s.technician_id,
            assigned_user_id=s.assigned_user_id,
            scheduled_date=s.scheduled_date,
            actual_survey_date=s.actual_survey_date,
            roof_area=s.roof_area,
            shadow_free_area=s.shadow_free_area,
            roof_direction=s.roof_direction,
            roof_tilt=s.roof_tilt,
            cable_distance=s.cable_distance,
            structural_condition=s.structural_condition,
            grid_connection_suitable=s.grid_connection_suitable,
            monthly_bill=s.monthly_bill,
            required_capacity_kw=s.required_capacity_kw,
            observations=s.observations,
            technician_recommendation=s.technician_recommendation,
            rejection_reason=s.rejection_reason,
            photo_urls=s.photo_urls,
            status=s.status,
            approval_status=s.approval_status,
            approved_by=s.approved_by,
            customer_name=s.customer.name if s.customer else None,
            customer_phone=s.customer.phone if s.customer else None,
            customer_address=s.customer.address if s.customer else None,
            technician_name=s.technician.name if s.technician else None,
            created_at=s.created_at
        )
        results.append(s_out)
    return results


@router.post("", response_model=SurveyOut)
def schedule_survey(
    payload: SurveyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer_query = db.query(Customer).filter(Customer.id == payload.customer_id)
    if canonical_role(current_user.role) == "Site Survey Engineer":
        assigned_customers = db.query(SiteSurvey.customer_id).filter(
            SiteSurvey.assigned_user_id == current_user.id
        )
        customer_query = customer_query.filter(Customer.id.in_(assigned_customers))
    customer = customer_query.first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    lead = None
    if payload.lead_id:
        lead = db.query(Lead).filter(Lead.id == payload.lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        if lead.customer_id is not None and lead.customer_id != customer.id:
            raise HTTPException(status_code=400, detail="The selected lead does not belong to this customer.")
    assigned_user_id = _resolve_survey_assignee(db, current_user, payload.assigned_user_id)
    if payload.technician_id is not None:
        if not has_permission(db, current_user, "surveys", ASSIGN):
            raise HTTPException(status_code=403, detail="Survey assignment permission is required.")
        technician = db.query(Technician).filter(Technician.id == payload.technician_id).first()
        if not technician:
            raise HTTPException(status_code=404, detail="Technician not found")
        if technician.status != "ACTIVE":
            raise HTTPException(status_code=409, detail="The selected technician is inactive.")
        if technician.availability == "UNAVAILABLE":
            raise HTTPException(status_code=409, detail="The selected technician is unavailable.")

    survey_ref = f"SURV-2026-{random.randint(100, 999)}"
    while db.query(SiteSurvey).filter(SiteSurvey.survey_reference == survey_ref).first():
        survey_ref = f"SURV-2026-{random.randint(100, 999)}"

    survey = SiteSurvey(
        survey_reference=survey_ref,
        lead_id=payload.lead_id,
        customer_id=customer.id,
        technician_id=payload.technician_id,
        assigned_user_id=assigned_user_id,
        scheduled_date=payload.scheduled_date,
        required_capacity_kw=payload.required_capacity_kw,
        monthly_bill=payload.monthly_bill or customer.monthly_bill,
        observations=payload.observations,
        status="SCHEDULED",
        approval_status="PENDING",
        photo_urls="[]"
    )
    db.add(survey)

    if lead:
        lead.stage = "SURVEY_SCHEDULED"
        lead.notes = f"{lead.notes or ''}\nSurvey scheduled for {payload.scheduled_date} ({survey_ref})".strip()

    db.commit()
    db.refresh(survey)

    return SurveyOut(
        id=survey.id,
        survey_reference=survey.survey_reference,
        lead_id=survey.lead_id,
        customer_id=survey.customer_id,
        technician_id=survey.technician_id,
        assigned_user_id=survey.assigned_user_id,
        scheduled_date=survey.scheduled_date,
        actual_survey_date=survey.actual_survey_date,
        roof_area=survey.roof_area,
        shadow_free_area=survey.shadow_free_area,
        roof_direction=survey.roof_direction,
        roof_tilt=survey.roof_tilt,
        cable_distance=survey.cable_distance,
        structural_condition=survey.structural_condition,
        grid_connection_suitable=survey.grid_connection_suitable,
        monthly_bill=survey.monthly_bill,
        required_capacity_kw=survey.required_capacity_kw,
        observations=survey.observations,
        technician_recommendation=survey.technician_recommendation,
        rejection_reason=survey.rejection_reason,
        photo_urls=survey.photo_urls,
        status=survey.status,
        approval_status=survey.approval_status,
        approved_by=survey.approved_by,
        customer_name=customer.name,
        customer_phone=customer.phone,
        customer_address=customer.address,
        technician_name=survey.technician.name if survey.technician else None,
        created_at=survey.created_at
    )


@router.get("/{survey_id}", response_model=SurveyOut)
def get_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    s = _scope_surveys(db.query(SiteSurvey), current_user).filter(SiteSurvey.id == survey_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Survey not found")

    return SurveyOut(
        id=s.id,
        survey_reference=s.survey_reference,
        lead_id=s.lead_id,
        customer_id=s.customer_id,
        technician_id=s.technician_id,
        assigned_user_id=s.assigned_user_id,
        scheduled_date=s.scheduled_date,
        actual_survey_date=s.actual_survey_date,
        roof_area=s.roof_area,
        shadow_free_area=s.shadow_free_area,
        roof_direction=s.roof_direction,
        roof_tilt=s.roof_tilt,
        cable_distance=s.cable_distance,
        structural_condition=s.structural_condition,
        grid_connection_suitable=s.grid_connection_suitable,
        monthly_bill=s.monthly_bill,
        required_capacity_kw=s.required_capacity_kw,
        observations=s.observations,
        technician_recommendation=s.technician_recommendation,
        rejection_reason=s.rejection_reason,
        photo_urls=s.photo_urls,
        status=s.status,
        approval_status=s.approval_status,
        approved_by=s.approved_by,
        customer_name=s.customer.name if s.customer else None,
        customer_phone=s.customer.phone if s.customer else None,
        customer_address=s.customer.address if s.customer else None,
        technician_name=s.technician.name if s.technician else None,
        created_at=s.created_at
    )


@router.put("/{survey_id}", response_model=SurveyOut)
def update_survey(
    survey_id: int,
    payload: SurveyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    s = _scope_surveys(db.query(SiteSurvey), current_user).filter(SiteSurvey.id == survey_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Survey not found")

    if "assigned_user_id" in payload.model_fields_set:
        s.assigned_user_id = _resolve_survey_assignee(db, current_user, payload.assigned_user_id)
    if payload.technician_id is not None:
        if not has_permission(db, current_user, "surveys", ASSIGN):
            raise HTTPException(status_code=403, detail="Survey assignment permission is required.")
        technician = db.query(Technician).filter(Technician.id == payload.technician_id).first()
        if not technician:
            raise HTTPException(status_code=404, detail="Technician not found")
        if technician.status != "ACTIVE":
            raise HTTPException(status_code=409, detail="The selected technician is inactive.")
        if technician.availability == "UNAVAILABLE":
            raise HTTPException(status_code=409, detail="The selected technician is unavailable.")
    if payload.technician_id is not None:
        s.technician_id = payload.technician_id
    if payload.actual_survey_date is not None:
        s.actual_survey_date = payload.actual_survey_date
    if payload.roof_area is not None:
        s.roof_area = payload.roof_area
    if payload.shadow_free_area is not None:
        s.shadow_free_area = payload.shadow_free_area
    if payload.roof_direction is not None:
        s.roof_direction = payload.roof_direction
    if payload.roof_tilt is not None:
        s.roof_tilt = payload.roof_tilt
    if payload.cable_distance is not None:
        s.cable_distance = payload.cable_distance
    if payload.structural_condition is not None:
        s.structural_condition = payload.structural_condition
    if payload.grid_connection_suitable is not None:
        s.grid_connection_suitable = payload.grid_connection_suitable
    if payload.observations is not None:
        s.observations = payload.observations
    if payload.technician_recommendation is not None:
        s.technician_recommendation = payload.technician_recommendation
    if payload.photo_urls is not None:
        s.photo_urls = payload.photo_urls
    if payload.status is not None:
        s.status = payload.status

    db.commit()
    db.refresh(s)

    return SurveyOut(
        id=s.id,
        survey_reference=s.survey_reference,
        lead_id=s.lead_id,
        customer_id=s.customer_id,
        technician_id=s.technician_id,
        assigned_user_id=s.assigned_user_id,
        scheduled_date=s.scheduled_date,
        actual_survey_date=s.actual_survey_date,
        roof_area=s.roof_area,
        shadow_free_area=s.shadow_free_area,
        roof_direction=s.roof_direction,
        roof_tilt=s.roof_tilt,
        cable_distance=s.cable_distance,
        structural_condition=s.structural_condition,
        grid_connection_suitable=s.grid_connection_suitable,
        monthly_bill=s.monthly_bill,
        required_capacity_kw=s.required_capacity_kw,
        observations=s.observations,
        technician_recommendation=s.technician_recommendation,
        rejection_reason=s.rejection_reason,
        photo_urls=s.photo_urls,
        status=s.status,
        approval_status=s.approval_status,
        approved_by=s.approved_by,
        customer_name=s.customer.name if s.customer else None,
        customer_phone=s.customer.phone if s.customer else None,
        customer_address=s.customer.address if s.customer else None,
        technician_name=s.technician.name if s.technician else None,
        created_at=s.created_at
    )


@router.post("/{survey_id}/approve", response_model=SurveyOut)
def approve_or_reject_survey(
    survey_id: int,
    payload: SurveyApprove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    s = _scope_surveys(db.query(SiteSurvey), current_user).filter(SiteSurvey.id == survey_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Survey not found")

    if payload.action == "APPROVE":
        s.status = "APPROVED"
        s.approval_status = "APPROVED"
        s.approved_by = payload.approved_by or current_user.name
        s.rejection_reason = None
        if s.lead_id:
            lead = db.query(Lead).filter(Lead.id == s.lead_id).first()
            if lead:
                lead.stage = "SURVEY_APPROVED"
                lead.notes = f"{lead.notes or ''}\nSurvey {s.survey_reference} approved by {s.approved_by}.".strip()
    elif payload.action == "REJECT":
        if not payload.rejection_reason or not payload.rejection_reason.strip():
            raise HTTPException(status_code=400, detail="Rejection reason is required to reject a site survey")
        s.status = "REJECTED"
        s.approval_status = "REJECTED"
        s.rejection_reason = payload.rejection_reason
        s.approved_by = current_user.name
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be APPROVE or REJECT")

    db.commit()
    db.refresh(s)

    return SurveyOut(
        id=s.id,
        survey_reference=s.survey_reference,
        lead_id=s.lead_id,
        customer_id=s.customer_id,
        technician_id=s.technician_id,
        assigned_user_id=s.assigned_user_id,
        scheduled_date=s.scheduled_date,
        actual_survey_date=s.actual_survey_date,
        roof_area=s.roof_area,
        shadow_free_area=s.shadow_free_area,
        roof_direction=s.roof_direction,
        roof_tilt=s.roof_tilt,
        cable_distance=s.cable_distance,
        structural_condition=s.structural_condition,
        grid_connection_suitable=s.grid_connection_suitable,
        monthly_bill=s.monthly_bill,
        required_capacity_kw=s.required_capacity_kw,
        observations=s.observations,
        technician_recommendation=s.technician_recommendation,
        rejection_reason=s.rejection_reason,
        photo_urls=s.photo_urls,
        status=s.status,
        approval_status=s.approval_status,
        approved_by=s.approved_by,
        customer_name=s.customer.name if s.customer else None,
        customer_phone=s.customer.phone if s.customer else None,
        customer_address=s.customer.address if s.customer else None,
        technician_name=s.technician.name if s.technician else None,
        created_at=s.created_at
    )


@router.post("/{survey_id}/upload-photo")
async def upload_survey_photo(
    survey_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    s = _scope_surveys(db.query(SiteSurvey), current_user).filter(SiteSurvey.id == survey_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Survey not found")

    upload_dir = "backend/uploads/surveys"
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"survey_{s.id}_{random.randint(1000, 9999)}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    rel_url = f"/api/uploads/surveys/{filename}"
    current_photos = []
    try:
        current_photos = json.loads(s.photo_urls or "[]")
    except Exception:
        current_photos = []
    current_photos.append(rel_url)
    s.photo_urls = json.dumps(current_photos)
    db.commit()

    return {"success": True, "url": rel_url, "all_photos": current_photos}
