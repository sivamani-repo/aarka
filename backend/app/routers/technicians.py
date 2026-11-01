from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.survey import Technician, SiteSurvey
from app.models.installation import InstallationJob
from app.schemas.schemas import (
    TechnicianAccountLink,
    TechnicianAvailabilityUpdate,
    TechnicianCreate,
    TechnicianOut,
)
from app.core.permissions import get_current_user
from app.core.rbac import canonical_role, has_permission
from app.models.user import AuditLog, User

router = APIRouter(prefix="/api/technicians", tags=["Technicians & Field Operations"])

ACTIVE_SURVEY_STATUSES = ("SCHEDULED", "IN_PROGRESS")
ACTIVE_INSTALLATION_STATUSES = ("ASSIGNED", "SCHEDULED", "IN_PROGRESS", "TESTING")


def _active_assignment_counts(db: Session, technician_id: int) -> tuple[int, int]:
    surveys = db.query(SiteSurvey).filter(
        SiteSurvey.technician_id == technician_id,
        SiteSurvey.status.in_(ACTIVE_SURVEY_STATUSES),
    ).count()
    installations = db.query(InstallationJob).filter(
        InstallationJob.technician_id == technician_id,
        InstallationJob.status.in_(ACTIVE_INSTALLATION_STATUSES),
    ).count()
    return surveys, installations


def _availability_status(db: Session, technician: Technician) -> str:
    surveys, installations = _active_assignment_counts(db, technician.id)
    if surveys + installations:
        return "BUSY"
    return technician.availability


@router.get("", response_model=List[TechnicianOut])
def list_technicians(
    availability: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Technician)
    technicians = query.order_by(Technician.id.asc()).all()
    results = []
    for t in technicians:
        surveys, installations = _active_assignment_counts(db, t.id)
        active_surveys = 0
        if has_permission(db, current_user, "surveys", "VIEW"):
            active_surveys = surveys
        active_installs = 0
        if has_permission(db, current_user, "installations", "VIEW"):
            active_installs = installations
        t_out = TechnicianOut.from_orm(t)
        t_out.availability = "BUSY" if surveys + installations else t.availability
        t_out.active_assignments = active_surveys + active_installs
        if not availability or availability == "ALL" or t_out.availability == availability:
            results.append(t_out)
    return results


@router.get("/eligible-users")
def list_eligible_technician_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users = db.query(User).filter(User.is_active.is_(True)).order_by(User.name.asc()).all()
    return [
        {"id": user.id, "name": user.name, "email": user.email}
        for user in users
        if canonical_role(user.role) == "Solar Technician"
    ]


@router.get("/me/availability")
def get_my_technician_availability(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if canonical_role(current_user.role) != "Solar Technician":
        raise HTTPException(status_code=403, detail="Only Solar Technicians can view their own availability.")
    technician = db.query(Technician).filter(Technician.user_id == current_user.id).first()
    if not technician:
        raise HTTPException(status_code=404, detail="No technician profile is linked to this account.")
    return {
        "technician_id": technician.id,
        "availability": _availability_status(db, technician),
        "preference": technician.availability,
        "updated_at": technician.availability_updated_at,
    }


@router.patch("/me/availability")
def update_my_technician_availability(
    payload: TechnicianAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if canonical_role(current_user.role) != "Solar Technician":
        raise HTTPException(status_code=403, detail="Only Solar Technicians can update their own availability.")
    technician = db.query(Technician).filter(
        Technician.user_id == current_user.id,
        Technician.status == "ACTIVE",
    ).with_for_update().first()
    if not technician:
        raise HTTPException(status_code=404, detail="No active technician profile is linked to this account.")

    previous_availability = technician.availability
    technician.availability = payload.availability
    technician.availability_updated_at = datetime.now(timezone.utc)
    db.add(AuditLog(
        user_id=current_user.id,
        action="TECHNICIAN_AVAILABILITY_UPDATED",
        entity_type="technician",
        entity_id=technician.id,
        details=f"Availability changed from {previous_availability} to {payload.availability}.",
    ))
    db.commit()
    db.refresh(technician)

    return {
        "technician_id": technician.id,
        "availability": _availability_status(db, technician),
        "preference": technician.availability,
        "updated_at": technician.availability_updated_at,
    }


@router.post("", response_model=TechnicianOut)
def create_technician(
    payload: TechnicianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    linked_user_id = payload.user_id
    if linked_user_id is None and payload.email:
        matching_user = db.query(User).filter(
            func.lower(User.email) == payload.email.strip().lower()
        ).first()
        if matching_user and canonical_role(matching_user.role) == "Solar Technician":
            linked_user_id = matching_user.id
    if linked_user_id is not None:
        linked_user = db.query(User).filter(
            User.id == linked_user_id,
            User.is_active.is_(True),
        ).first()
        if not linked_user or canonical_role(linked_user.role) != "Solar Technician":
            raise HTTPException(status_code=400, detail="Link only an active Solar Technician account.")
        if db.query(Technician).filter(Technician.user_id == linked_user_id).first():
            raise HTTPException(status_code=409, detail="This account is already linked to a technician profile.")

    tech = Technician(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        user_id=linked_user_id,
        skills=payload.skills,
        experience_years=payload.experience_years,
        availability=payload.availability,
        availability_updated_at=datetime.now(timezone.utc),
        status="ACTIVE",
        employment_status=payload.employment_status
    )
    db.add(tech)
    db.commit()
    db.refresh(tech)
    return tech


@router.patch("/{technician_id}/link-user", response_model=TechnicianOut)
def link_technician_user(
    technician_id: int,
    payload: TechnicianAccountLink,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    technician = db.query(Technician).filter(
        Technician.id == technician_id
    ).with_for_update().first()
    if not technician:
        raise HTTPException(status_code=404, detail="Technician not found.")

    linked_user = None
    if payload.user_id is not None:
        linked_user = db.query(User).filter(
            User.id == payload.user_id,
            User.is_active.is_(True),
        ).first()
        if not linked_user or canonical_role(linked_user.role) != "Solar Technician":
            raise HTTPException(status_code=400, detail="Select an active Solar Technician account.")
        duplicate = db.query(Technician).filter(
            Technician.user_id == linked_user.id,
            Technician.id != technician.id,
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="This account is already linked to another technician profile.")

    previous_user_id = technician.user_id
    technician.user_id = linked_user.id if linked_user else None
    db.add(AuditLog(
        user_id=current_user.id,
        action="TECHNICIAN_ACCOUNT_LINK_UPDATED",
        entity_type="technician",
        entity_id=technician.id,
        details=f"Linked user changed from {previous_user_id} to {technician.user_id}.",
    ))
    db.commit()
    db.refresh(technician)
    return technician


@router.get("/{technician_id}/schedule")
def get_technician_schedule(
    technician_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tech = db.query(Technician).filter(Technician.id == technician_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")

    surveys = []
    if has_permission(db, current_user, "surveys", "VIEW"):
        surveys = db.query(SiteSurvey).filter(SiteSurvey.technician_id == technician_id).all()
    installs = []
    if has_permission(db, current_user, "installations", "VIEW"):
        installs = db.query(InstallationJob).filter(
            InstallationJob.technician_id == technician_id
        ).all()

    return {
        "technician": TechnicianOut.from_orm(tech),
        "surveys": [
            {
                "id": s.id,
                "ref": s.survey_reference,
                "customer_name": s.customer.name if s.customer else "",
                "address": s.customer.address if s.customer else "",
                "scheduled_date": s.scheduled_date,
                "status": s.status
            }
            for s in surveys
        ],
        "installations": [
            {
                "id": i.id,
                "job_number": i.job_number,
                "customer_name": i.customer.name if i.customer else "",
                "address": i.customer.address if i.customer else "",
                "scheduled_date": i.scheduled_date,
                "status": i.status
            }
            for i in installs
        ]
    }
