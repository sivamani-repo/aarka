import json
import random
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.service import ServiceTicket, WarrantyRecord
from app.models.inventory import SerializedEquipment
from app.models.customer import Customer
from app.models.survey import Technician
from app.schemas.schemas import ServiceTicketCreate, ServiceTicketUpdate, ServiceTicketReplaceEquipment, ServiceTicketOut
from app.core.permissions import get_current_user
from app.core.rbac import ASSIGN, canonical_role, has_permission
from app.models.user import User

router = APIRouter(prefix="/api/service", tags=["After-Sales & Service Tickets"])


def _scope_tickets(query, current_user: User):
    if canonical_role(current_user.role) == "Support Executive":
        return query.filter(ServiceTicket.assigned_user_id == current_user.id)
    return query


def _resolve_support_assignee(db: Session, current_user: User, requested_id: Optional[int]):
    if canonical_role(current_user.role) == "Support Executive":
        if requested_id not in (None, current_user.id):
            raise HTTPException(status_code=403, detail="Support executives can only own their assigned tickets.")
        return current_user.id
    if requested_id is None:
        return None
    if not has_permission(db, current_user, "service", ASSIGN):
        raise HTTPException(status_code=403, detail="Service assignment permission is required.")
    assignee = db.query(User).filter(User.id == requested_id, User.is_active.is_(True)).first()
    if not assignee or canonical_role(assignee.role) != "Support Executive":
        raise HTTPException(status_code=400, detail="Select an active Support Executive.")
    return assignee.id


@router.get("/tickets", response_model=List[ServiceTicketOut])
def list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    technician_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = _scope_tickets(db.query(ServiceTicket), current_user)
    if status and status != "ALL":
        query = query.filter(ServiceTicket.status == status)
    if priority and priority != "ALL":
        query = query.filter(ServiceTicket.priority == priority)
    if technician_id:
        query = query.filter(ServiceTicket.technician_id == technician_id)

    tickets = query.order_by(ServiceTicket.id.desc()).all()
    results = []
    for t in tickets:
        results.append(ServiceTicketOut(
            id=t.id,
            ticket_number=t.ticket_number,
            customer_id=t.customer_id,
            assigned_user_id=t.assigned_user_id,
            customer_name=t.customer.name if t.customer else None,
            customer_phone=t.customer.phone if t.customer else None,
            customer_address=t.customer.address if t.customer else None,
            serial_number=t.serial_number,
            equipment_type=t.equipment_type,
            installation_id=t.installation_id,
            fault_code=t.fault_code,
            fault_description=t.fault_description,
            complaint_photos=t.complaint_photos or "[]",
            priority=t.priority,
            technician_id=t.technician_id,
            technician_name=t.technician.name if t.technician else None,
            warranty_eligible=t.warranty_eligible,
            warranty_status=t.warranty_status,
            diagnosis=t.diagnosis,
            repair_details=t.repair_details,
            parts_used=t.parts_used or "[]",
            labour_charges=t.labour_charges,
            parts_charges=t.parts_charges,
            total_charges=t.total_charges,
            customer_approved_estimate=t.customer_approved_estimate,
            replacement_serial_number=t.replacement_serial_number,
            status=t.status,
            reported_date=t.reported_date,
            resolution_date=t.resolution_date,
            customer_confirmed=t.customer_confirmed,
            created_at=t.created_at
        ))
    return results


@router.post("/tickets", response_model=ServiceTicketOut)
def create_service_ticket(
    payload: ServiceTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer_query = db.query(Customer).filter(Customer.id == payload.customer_id)
    if canonical_role(current_user.role) == "Support Executive":
        customer_query = customer_query.filter(Customer.assigned_user_id == current_user.id)
    customer = customer_query.first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    assigned_user_id = _resolve_support_assignee(db, current_user, payload.assigned_user_id)

    clean_sn = (payload.serial_number or payload.reported_serial_number or "").strip().upper()
    fault_desc = payload.fault_description or payload.description or payload.title or "Equipment fault reported"
    ser = db.query(SerializedEquipment).filter(SerializedEquipment.serial_number == clean_sn).first()

    # CRITICAL BUSINESS RULES #10 & #11: Look up warranty records and evaluate validity at complaint date
    today = date.today()
    warranty_records = db.query(WarrantyRecord).filter(
        WarrantyRecord.serial_number == clean_sn
    ).order_by(WarrantyRecord.id.desc()).all()
    war = next(
        (
            record for record in warranty_records
            if record.status in {"ACTIVE", "COVERED", "EXPIRING_SOON"}
            and record.certificate_url
            and record.activated_at
            and record.activated_by
            and record.warranty_start <= today <= record.warranty_end
        ),
        None,
    )
    is_covered = war is not None
    warranty_pending = any(
        record.status == "PENDING_ACTIVATION"
        or (
            record.status in {"ACTIVE", "COVERED", "EXPIRING_SOON"}
            and not (record.certificate_url and record.activated_at and record.activated_by)
        )
        for record in warranty_records
    )
    warranty_expired = any(
        (
            record.status in {"ACTIVE", "COVERED", "EXPIRING_SOON", "EXPIRED"}
            and record.certificate_url
            and record.activated_at
            and record.activated_by
            and record.warranty_end < today
        )
        for record in warranty_records
    )

    tkt_num = f"TKT-2026-{random.randint(1000, 9999)}"
    while db.query(ServiceTicket).filter(ServiceTicket.ticket_number == tkt_num).first():
        tkt_num = f"TKT-2026-{random.randint(1000, 9999)}"

    # Do not charge a customer while warranty coverage is pending or unverified.
    if is_covered:
        warranty_status = "COVERED"
        labour = 0.0
        parts = 0.0
        total = 0.0
        approved_estimate = True
    elif warranty_pending:
        warranty_status = "PENDING_ACTIVATION"
        labour = 0.0
        parts = 0.0
        total = 0.0
        approved_estimate = False
    elif warranty_expired:
        warranty_status = "EXPIRED"
        labour = 1500.0
        parts = 2500.0
        total = labour + parts
        approved_estimate = False  # requires customer approval before paid work
    else:
        warranty_status = "NOT_VERIFIED"
        labour = 0.0
        parts = 0.0
        total = 0.0
        approved_estimate = False

    ticket = ServiceTicket(
        ticket_number=tkt_num,
        customer_id=customer.id,
        assigned_user_id=assigned_user_id,
        serial_number=clean_sn,
        equipment_type=ser.product.name if (ser and ser.product) else "Solar Inverter",
        installation_id=payload.installation_id or (ser.installation_id if ser else None),
        fault_code=payload.fault_code or "ERR-04",
        fault_description=fault_desc,
        complaint_photos=json.dumps(payload.complaint_photos or []),
        priority=payload.priority or "MEDIUM",
        warranty_eligible=is_covered,
        warranty_status=warranty_status,
        labour_charges=labour,
        parts_charges=parts,
        total_charges=total,
        customer_approved_estimate=approved_estimate,
        status="OPEN",
        reported_date=today,
        customer_confirmed=False
    )
    db.add(ticket)

    db.commit()
    db.refresh(ticket)

    return ServiceTicketOut(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        customer_id=ticket.customer_id,
        assigned_user_id=ticket.assigned_user_id,
        customer_name=customer.name,
        customer_phone=customer.phone,
        customer_address=customer.address,
        serial_number=ticket.serial_number,
        equipment_type=ticket.equipment_type,
        installation_id=ticket.installation_id,
        fault_code=ticket.fault_code,
        fault_description=ticket.fault_description,
        complaint_photos=ticket.complaint_photos or "[]",
        priority=ticket.priority,
        technician_id=ticket.technician_id,
        technician_name=None,
        warranty_eligible=ticket.warranty_eligible,
        warranty_status=ticket.warranty_status,
        diagnosis=ticket.diagnosis,
        repair_details=ticket.repair_details,
        parts_used=ticket.parts_used or "[]",
        labour_charges=ticket.labour_charges,
        parts_charges=ticket.parts_charges,
        total_charges=ticket.total_charges,
        customer_approved_estimate=ticket.customer_approved_estimate,
        replacement_serial_number=ticket.replacement_serial_number,
        status=ticket.status,
        reported_date=ticket.reported_date,
        resolution_date=ticket.resolution_date,
        customer_confirmed=ticket.customer_confirmed,
        created_at=ticket.created_at
    )


@router.put("/tickets/{ticket_id}", response_model=ServiceTicketOut)
@router.put("/tickets/{ticket_id}/assign", response_model=ServiceTicketOut)
def update_service_ticket(
    ticket_id: int,
    payload: ServiceTicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = _scope_tickets(db.query(ServiceTicket), current_user).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Service ticket not found")

    if payload.technician_id is not None and not has_permission(db, current_user, "service", ASSIGN):
        raise HTTPException(status_code=403, detail="Service assignment permission is required.")
    if payload.technician_id is not None:
        technician = db.query(Technician).filter(
            Technician.id == payload.technician_id,
            Technician.status == "ACTIVE",
        ).first()
        if not technician:
            raise HTTPException(status_code=404, detail="Active technician not found.")
        if technician.availability == "UNAVAILABLE":
            raise HTTPException(status_code=409, detail="The selected technician is unavailable.")
        ticket.technician_id = payload.technician_id
    if "assigned_user_id" in payload.model_fields_set:
        ticket.assigned_user_id = _resolve_support_assignee(db, current_user, payload.assigned_user_id)
        if ticket.status == "OPEN":
            ticket.status = "ASSIGNED"
    if payload.diagnosis is not None:
        ticket.diagnosis = payload.diagnosis
    if payload.repair_details is not None:
        ticket.repair_details = payload.repair_details
    elif payload.resolution_notes is not None:
        ticket.repair_details = payload.resolution_notes
    if payload.parts_used is not None:
        ticket.parts_used = payload.parts_used
    if payload.labour_charges is not None:
        ticket.labour_charges = payload.labour_charges
    elif payload.labor_cost is not None:
        ticket.labour_charges = payload.labor_cost
    if payload.parts_charges is not None:
        ticket.parts_charges = payload.parts_charges
    elif payload.parts_cost is not None:
        ticket.parts_charges = payload.parts_cost
    if payload.customer_approved_estimate is not None:
        ticket.customer_approved_estimate = payload.customer_approved_estimate
    if payload.customer_signature is not None:
        ticket.customer_confirmed = True
    if payload.status is not None:
        ticket.status = payload.status

    ticket.total_charges = round(ticket.labour_charges + ticket.parts_charges, 2)
    db.commit()
    db.refresh(ticket)

    return ServiceTicketOut(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        customer_id=ticket.customer_id,
        assigned_user_id=ticket.assigned_user_id,
        customer_name=ticket.customer.name if ticket.customer else None,
        customer_phone=ticket.customer.phone if ticket.customer else None,
        customer_address=ticket.customer.address if ticket.customer else None,
        serial_number=ticket.serial_number,
        equipment_type=ticket.equipment_type,
        installation_id=ticket.installation_id,
        fault_code=ticket.fault_code,
        fault_description=ticket.fault_description,
        complaint_photos=ticket.complaint_photos or "[]",
        priority=ticket.priority,
        technician_id=ticket.technician_id,
        technician_name=ticket.technician.name if ticket.technician else None,
        warranty_eligible=ticket.warranty_eligible,
        warranty_status=ticket.warranty_status,
        diagnosis=ticket.diagnosis,
        repair_details=ticket.repair_details,
        parts_used=ticket.parts_used or "[]",
        labour_charges=ticket.labour_charges,
        parts_charges=ticket.parts_charges,
        total_charges=ticket.total_charges,
        customer_approved_estimate=ticket.customer_approved_estimate,
        replacement_serial_number=ticket.replacement_serial_number,
        status=ticket.status,
        reported_date=ticket.reported_date,
        resolution_date=ticket.resolution_date,
        customer_confirmed=ticket.customer_confirmed,
        created_at=ticket.created_at
    )


@router.post("/tickets/{ticket_id}/replace-equipment")
@router.post("/tickets/{ticket_id}/replacement")
def replace_defective_equipment(
    ticket_id: int,
    payload: ServiceTicketReplaceEquipment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = _scope_tickets(db.query(ServiceTicket), current_user).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Service ticket not found")

    new_sn = (payload.replacement_serial_number or payload.new_serial_number or "").strip().upper()
    if not new_sn:
        raise HTTPException(status_code=400, detail="Replacement serial number is required")

    new_ser = db.query(SerializedEquipment).filter(SerializedEquipment.serial_number == new_sn).first()
    if not new_ser:
        raise HTTPException(status_code=404, detail=f"Replacement serial {new_sn} not found in inventory")

    if new_ser.status not in ["AVAILABLE", "RECEIVED"]:
        raise HTTPException(status_code=400, detail=f"Replacement unit {new_sn} is not available (Current status: {new_ser.status})")

    # CRITICAL BUSINESS RULE #12:
    # 1. Update old serial status to RETURNED_DEFECTIVE
    old_ser = db.query(SerializedEquipment).filter(SerializedEquipment.serial_number == ticket.serial_number).first()
    if old_ser:
        old_ser.status = "RETURNED_DEFECTIVE"
        old_ser.current_location = "Service Center - Defective Quarantine"

    # 2. Allocate replacement serial to customer
    new_ser.status = "INSTALLED"
    new_ser.customer_id = ticket.customer_id
    new_ser.installation_id = ticket.installation_id
    new_ser.current_location = f"Customer Site - {ticket.customer.name if ticket.customer else 'Active'}"
    new_ser.warranty_start = date.today()
    # Apply warranty policy to replacement
    new_ser.warranty_end = date.today() + (old_ser.warranty_end - date.today() if (old_ser and old_ser.warranty_end and old_ser.warranty_end > date.today()) else (date.today() + 730))

    # 3. Update ticket
    ticket.replacement_serial_number = new_sn
    ticket.status = "RESOLVED"
    ticket.resolution_date = date.today()
    reason_txt = payload.reason or payload.replacement_reason or "In-warranty equipment replacement"
    ticket.repair_details = f"{ticket.repair_details or ''}\n[REPLACEMENT] Replaced defective unit ({ticket.serial_number}) with fresh unit ({new_sn}). Reason: {reason_txt}".strip()

    db.commit()

    return {
        "success": True,
        "message": f"Successfully replaced equipment! Defective unit {ticket.serial_number} archived. New unit {new_sn} installed.",
        "replacement_serial": new_sn,
        "ticket_status": ticket.status
    }


@router.post("/tickets/{ticket_id}/resolve")
def resolve_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = _scope_tickets(db.query(ServiceTicket), current_user).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Service ticket not found")

    ticket.status = "RESOLVED"
    ticket.resolution_date = date.today()
    db.commit()
    return {"success": True, "message": f"Ticket {ticket.ticket_number} marked as RESOLVED"}


@router.post("/tickets/{ticket_id}/confirm")
def confirm_and_close_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = _scope_tickets(db.query(ServiceTicket), current_user).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Service ticket not found")

    ticket.customer_confirmed = True
    ticket.status = "CLOSED"
    db.commit()
    return {"success": True, "message": f"Customer confirmation recorded. Ticket {ticket.ticket_number} is now CLOSED."}
