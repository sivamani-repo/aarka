import os
import json
import random
import shutil
from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.installation import InstallationJob
from app.models.commercial import SalesOrder
from app.models.survey import Technician
from app.models.inventory import SerializedEquipment
from app.schemas.schemas import InstallationCreate, InstallationChecklistUpdate, InstallationComplete, InstallationOut
from app.core.permissions import get_current_user
from app.core.rbac import ASSIGN, canonical_role, has_permission
from app.models.user import User

router = APIRouter(prefix="/api/installations", tags=["Installation Operations"])


def _scope_installations(query, current_user: User):
    if canonical_role(current_user.role) == "Solar Technician":
        return query.filter(InstallationJob.assigned_user_id == current_user.id)
    return query


def _resolve_install_assignee(db: Session, current_user: User, requested_id: Optional[int], technician: Technician):
    if canonical_role(current_user.role) == "Solar Technician":
        if requested_id not in (None, current_user.id):
            raise HTTPException(status_code=403, detail="Technicians can only update their own installation assignments.")
        return current_user.id
    assigned_id = requested_id
    if assigned_id is None and technician.email:
        employee = db.query(User).filter(User.email.ilike(technician.email)).first()
        if employee and canonical_role(employee.role) == "Solar Technician":
            assigned_id = employee.id
    if assigned_id is None:
        return None
    if not has_permission(db, current_user, "installations", ASSIGN):
        raise HTTPException(status_code=403, detail="Installation assignment permission is required.")
    employee = db.query(User).filter(User.id == assigned_id, User.is_active.is_(True)).first()
    if not employee or canonical_role(employee.role) != "Solar Technician":
        raise HTTPException(status_code=400, detail="Select an active Solar Technician.")
    return employee.id


@router.get("", response_model=List[InstallationOut])
def list_installations(
    technician_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = _scope_installations(db.query(InstallationJob), current_user)
    if technician_id:
        query = query.filter(InstallationJob.technician_id == technician_id)
    if status and status != "ALL":
        query = query.filter(InstallationJob.status == status)

    jobs = query.order_by(InstallationJob.id.desc()).all()
    results = []
    for j in jobs:
        results.append(InstallationOut(
            id=j.id,
            job_number=j.job_number,
            order_id=j.order_id,
            order_number=j.order.order_number if j.order else None,
            customer_id=j.customer_id,
            customer_name=j.customer.name if j.customer else None,
            customer_phone=j.customer.phone if j.customer else None,
            customer_address=j.customer.address if j.customer else None,
            technician_id=j.technician_id,
            technician_name=j.technician.name if j.technician else None,
            assigned_at=j.assigned_at,
            scheduled_date=j.scheduled_date,
            start_time=j.start_time,
            end_time=j.end_time,
            status=j.status,
            capacity_kw=j.capacity_kw,
            checklist_state=j.checklist_state or "{}",
            installed_equipment=j.installed_equipment,
            technical_observations=j.technical_observations,
            customer_signature=j.customer_signature,
            photo_urls=j.photo_urls or "[]",
            testing_results=j.testing_results,
            labour_hours=j.labour_hours,
            created_at=j.created_at
        ))
    return results


@router.post("", response_model=InstallationOut)
def schedule_installation(
    payload: InstallationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(SalesOrder).filter(SalesOrder.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    tech = db.query(Technician).filter(Technician.id == payload.technician_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")
    assigned_user_id = _resolve_install_assignee(db, current_user, payload.assigned_user_id, tech)

    job_num = f"INST-2026-{random.randint(1000, 9999)}"
    while db.query(InstallationJob).filter(InstallationJob.job_number == job_num).first():
        job_num = f"INST-2026-{random.randint(1000, 9999)}"

    job = InstallationJob(
        job_number=job_num,
        order_id=order.id,
        customer_id=order.customer_id,
        technician_id=tech.id,
        assigned_user_id=assigned_user_id,
        scheduled_date=payload.scheduled_date,
        status="SCHEDULED",
        capacity_kw=payload.capacity_kw or order.capacity_kw,
        checklist_state=json.dumps({
            "mounting_inspected": False,
            "panels_installed": False,
            "inverter_installed": False,
            "wiring_completed": False,
            "earthing_completed": False,
            "safety_checked": False,
            "system_tested": False,
            "power_verified": False,
            "customer_handover": False
        }),
        photo_urls="[]",
        testing_results="Pending Installation",
        labour_hours=6.0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return get_installation(job.id, db, current_user)


@router.get("/{job_id}", response_model=InstallationOut)
def get_installation(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    j = _scope_installations(db.query(InstallationJob), current_user).filter(InstallationJob.id == job_id).first()
    if not j:
        raise HTTPException(status_code=404, detail="Installation Job not found")

    return InstallationOut(
        id=j.id,
        job_number=j.job_number,
        order_id=j.order_id,
        order_number=j.order.order_number if j.order else None,
        customer_id=j.customer_id,
        customer_name=j.customer.name if j.customer else None,
        customer_phone=j.customer.phone if j.customer else None,
        customer_address=j.customer.address if j.customer else None,
        technician_id=j.technician_id,
        assigned_user_id=j.assigned_user_id,
        technician_name=j.technician.name if j.technician else None,
        assigned_at=j.assigned_at,
        scheduled_date=j.scheduled_date,
        start_time=j.start_time,
        end_time=j.end_time,
        status=j.status,
        capacity_kw=j.capacity_kw,
        checklist_state=j.checklist_state or "{}",
        installed_equipment=j.installed_equipment,
        technical_observations=j.technical_observations,
        customer_signature=j.customer_signature,
        photo_urls=j.photo_urls or "[]",
        testing_results=j.testing_results,
        labour_hours=j.labour_hours,
        created_at=j.created_at
    )


@router.put("/{job_id}/checklist")
def update_checklist(
    job_id: int,
    payload: InstallationChecklistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = _scope_installations(db.query(InstallationJob), current_user).filter(InstallationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Installation job not found")

    job.checklist_state = json.dumps(payload.checklist_state)
    if payload.technical_observations:
        job.technical_observations = payload.technical_observations
    if payload.testing_results:
        job.testing_results = payload.testing_results

    if job.status == "SCHEDULED":
        job.status = "IN_PROGRESS"
        job.start_time = datetime.now()

    db.commit()
    return {"success": True, "message": "Checklist updated", "status": job.status}


@router.post("/{job_id}/upload-photo")
async def upload_installation_photo(
    job_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = _scope_installations(db.query(InstallationJob), current_user).filter(InstallationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Installation job not found")

    upload_dir = "backend/uploads/installations"
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"install_{job.id}_{random.randint(1000, 9999)}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    rel_url = f"/api/uploads/installations/{filename}"
    current_photos = []
    try:
        current_photos = json.loads(job.photo_urls or "[]")
    except Exception:
        current_photos = []
    current_photos.append(rel_url)
    job.photo_urls = json.dumps(current_photos)
    db.commit()

    return {"success": True, "url": rel_url, "all_photos": current_photos}


@router.post("/{job_id}/complete")
def complete_installation(
    job_id: int,
    payload: InstallationComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = _scope_installations(db.query(InstallationJob), current_user).filter(InstallationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Installation job not found")

    # CRITICAL BUSINESS RULES #13 & #14:
    # 1. Verify all 9 checklist points are checked
    required_points = [
        "mounting_inspected", "panels_installed", "inverter_installed",
        "wiring_completed", "earthing_completed", "safety_checked",
        "system_tested", "power_verified", "customer_handover"
    ]
    missing_points = [p for p in required_points if not payload.checklist_state.get(p, False)]
    if missing_points:
        raise HTTPException(
            status_code=400,
            detail=f"Business Rule Violation: Installation cannot be completed until all 9 checklist items are checked. Incomplete items: {', '.join(missing_points)}"
        )

    # 2. Verify customer signature canvas is captured
    if not payload.customer_signature or len(payload.customer_signature.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Business Rule Violation: Customer signature is mandatory for customer handover and completion."
        )

    job.checklist_state = json.dumps(payload.checklist_state)
    job.technical_observations = payload.technical_observations
    job.testing_results = payload.testing_results
    job.customer_signature = payload.customer_signature
    job.labour_hours = payload.labour_hours or 6.0
    job.status = "CUSTOMER_ACCEPTED"
    job.end_time = datetime.now()

    # Update order status
    order = job.order
    if order:
        order.status = "COMPLETED"

    # Update SerializedEquipment status to INSTALLED
    if order:
        serials = db.query(SerializedEquipment).filter(SerializedEquipment.order_id == order.id).all()
        for s in serials:
            s.status = "INSTALLED"
            s.installation_id = job.id

    db.commit()

    # PRIMARY BUSINESS REQUIREMENT: Automatically activate warranties for all installed equipment
    activated_count = 0
    try:
        from app.core.warranty_service import activate_warranties_for_installation
        warranties = activate_warranties_for_installation(
            db=db,
            job=job,
            completion_date=job.end_time.date() if job.end_time else date.today(),
            user_name=current_user.name
        )
        activated_count = len(warranties)
    except Exception as e:
        print(f"Warning: Warranty auto-activation encountered error: {e}")

    return {
        "success": True,
        "message": f"Installation {job.job_number} successfully completed and accepted by customer! {activated_count} equipment warranty certificate(s) activated.",
        "status": job.status,
        "activated_warranties_count": activated_count
    }
