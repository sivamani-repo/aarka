from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.survey import Technician, SiteSurvey
from app.models.installation import InstallationJob
from app.schemas.schemas import TechnicianCreate, TechnicianOut
from app.core.permissions import get_current_user
from app.core.rbac import has_permission
from app.models.user import User

router = APIRouter(prefix="/api/technicians", tags=["Technicians & Field Operations"])


@router.get("", response_model=List[TechnicianOut])
def list_technicians(
    availability: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Technician)
    if availability and availability != "ALL":
        query = query.filter(Technician.availability == availability)

    technicians = query.order_by(Technician.id.asc()).all()
    results = []
    for t in technicians:
        active_surveys = 0
        if has_permission(db, current_user, "surveys", "VIEW"):
            active_surveys = db.query(SiteSurvey).filter(
                SiteSurvey.technician_id == t.id,
                SiteSurvey.status.in_(["SCHEDULED", "IN_PROGRESS"])
            ).count()
        active_installs = 0
        if has_permission(db, current_user, "installations", "VIEW"):
            active_installs = db.query(InstallationJob).filter(
                InstallationJob.technician_id == t.id,
                InstallationJob.status.in_(["ASSIGNED", "SCHEDULED", "IN_PROGRESS", "TESTING"])
            ).count()
        t_out = TechnicianOut.from_orm(t)
        t_out.active_assignments = active_surveys + active_installs
        results.append(t_out)
    return results


@router.post("", response_model=TechnicianOut)
def create_technician(
    payload: TechnicianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tech = Technician(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        skills=payload.skills,
        experience_years=payload.experience_years,
        availability=payload.availability,
        status="ACTIVE",
        employment_status=payload.employment_status
    )
    db.add(tech)
    db.commit()
    db.refresh(tech)
    return tech


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
