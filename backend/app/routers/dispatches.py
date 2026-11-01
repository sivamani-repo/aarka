import json
import random
from typing import List, Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory import Dispatch, SerializedEquipment, InventoryItem, StockMovement
from app.models.commercial import SalesOrder
from app.models.installation import InstallationJob
from app.models.service import WarrantyRecord
from app.schemas.schemas import DispatchCreate, DispatchConfirmDelivery, DispatchOut
from app.core.permissions import get_current_user
from app.core.rbac import ASSIGN, canonical_role, has_permission
from app.models.user import User

router = APIRouter(prefix="/api/dispatches", tags=["Warehouse Dispatch & Delivery"])


def _scope_dispatches(query, current_user: User):
    if canonical_role(current_user.role) == "Dispatch Staff":
        return query.filter(Dispatch.assigned_user_id == current_user.id)
    return query


def _resolve_dispatch_assignee(db: Session, current_user: User, requested_id: Optional[int]):
    if requested_id is None:
        return None
    if not has_permission(db, current_user, "dispatches", ASSIGN):
        raise HTTPException(status_code=403, detail="Dispatch assignment permission is required.")
    assignee = db.query(User).filter(User.id == requested_id, User.is_active.is_(True)).first()
    if not assignee or canonical_role(assignee.role) != "Dispatch Staff":
        raise HTTPException(status_code=400, detail="Select an active Dispatch Staff employee.")
    return assignee.id


@router.get("", response_model=List[DispatchOut])
def list_dispatches(
    order_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = _scope_dispatches(db.query(Dispatch), current_user)
    if order_id:
        query = query.filter(Dispatch.order_id == order_id)
    if status and status != "ALL":
        query = query.filter(Dispatch.status == status)

    dispatches = query.order_by(Dispatch.id.desc()).all()
    results = []
    for d in dispatches:
        results.append(DispatchOut(
            id=d.id,
            order_id=d.order_id,
            assigned_user_id=d.assigned_user_id,
            order_number=d.order.order_number if d.order else None,
            customer_id=d.order.customer_id if d.order else None,
            customer_name=d.order.customer.name if (d.order and d.order.customer) else None,
            delivery_reference=d.delivery_reference,
            dispatch_date=d.dispatch_date,
            delivery_date=d.delivery_date,
            status=d.status,
            customer_confirmed=d.customer_confirmed,
            delivery_proof_url=d.delivery_proof_url,
            dispatched_by=d.dispatched_by,
            serial_numbers=d.serial_numbers,
            notes=d.notes,
            created_at=d.created_at
        ))
    return results


@router.post("", response_model=DispatchOut)
def create_dispatch(
    payload: DispatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(SalesOrder).filter(SalesOrder.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    assigned_user_id = _resolve_dispatch_assignee(db, current_user, payload.assigned_user_id)

    # CRITICAL BUSINESS RULE #7: Mandatory materials & serialized items must not be missing
    serialized_order_items = [it for it in order.items if it.is_serialized]
    if serialized_order_items and not payload.serial_numbers:
        raise HTTPException(
            status_code=400,
            detail="Business Rule Violation: This order contains serialized equipment (Inverter / Battery). All serialized units must be scanned before dispatch can be completed."
        )

    # Validate each serial number
    validated_serials = []
    for sn in payload.serial_numbers:
        clean_sn = sn.strip().upper()
        ser = db.query(SerializedEquipment).filter(SerializedEquipment.serial_number == clean_sn).first()
        if not ser:
            raise HTTPException(status_code=400, detail=f"Serial Number '{clean_sn}' not found in inventory.")
        if ser.status == "DISPATCHED" and ser.order_id != order.id:
            raise HTTPException(status_code=400, detail=f"Serial Number '{clean_sn}' is already dispatched to another order.")
        validated_serials.append(ser)

    deliv_ref = payload.delivery_reference or f"DISP-2026-{random.randint(1000, 9999)}"
    dispatch = Dispatch(
        order_id=order.id,
        assigned_user_id=assigned_user_id,
        delivery_reference=deliv_ref,
        dispatch_date=payload.dispatch_date or date.today(),
        status="DISPATCHED",
        customer_confirmed=False,
        dispatched_by=payload.dispatched_by or current_user.name,
        serial_numbers=json.dumps([s.serial_number for s in validated_serials]),
        notes=payload.notes
    )
    db.add(dispatch)
    db.commit()
    db.refresh(dispatch)

    # Transactionally update serial records
    for ser in validated_serials:
        ser.status = "DISPATCHED"
        ser.order_id = order.id
        ser.customer_id = order.customer_id
        ser.dispatch_id = dispatch.id
        ser.dispatch_date = dispatch.dispatch_date
        ser.current_location = "In Transit to Customer Site"

    # Transactionally deduct stock from Inventory and record StockMovement
    for item in order.items:
        if item.product_id:
            inv = db.query(InventoryItem).filter(InventoryItem.product_id == item.product_id).first()
            if inv:
                # Deduct inventory, ensuring no negative stock
                qty_to_deduct = int(item.quantity)
                inv.quantity = max(0, inv.quantity - qty_to_deduct)
                
            movement = StockMovement(
                product_id=item.product_id,
                movement_type="DISPATCHED",
                quantity=-int(item.quantity),
                reference_type="DISPATCH",
                reference_id=deliv_ref,
                notes=f"Dispatched for order {order.order_number}"
            )
            db.add(movement)

    order.status = "DISPATCHED"
    db.commit()
    db.refresh(dispatch)

    return DispatchOut(
        id=dispatch.id,
        order_id=dispatch.order_id,
        assigned_user_id=dispatch.assigned_user_id,
        order_number=order.order_number,
        customer_id=order.customer_id,
        customer_name=order.customer.name if order.customer else None,
        delivery_reference=dispatch.delivery_reference,
        dispatch_date=dispatch.dispatch_date,
        delivery_date=dispatch.delivery_date,
        status=dispatch.status,
        customer_confirmed=dispatch.customer_confirmed,
        delivery_proof_url=dispatch.delivery_proof_url,
        dispatched_by=dispatch.dispatched_by,
        serial_numbers=dispatch.serial_numbers,
        notes=dispatch.notes,
        created_at=dispatch.created_at
    )


@router.post("/{dispatch_id}/confirm-delivery")
def confirm_delivery(
    dispatch_id: int,
    payload: DispatchConfirmDelivery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dispatch = _scope_dispatches(db.query(Dispatch), current_user).filter(Dispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")

    dispatch.status = "DELIVERED"
    dispatch.delivery_date = payload.delivery_date
    dispatch.customer_confirmed = payload.customer_confirmed
    if payload.delivery_proof_url:
        dispatch.delivery_proof_url = payload.delivery_proof_url
    if payload.notes:
        dispatch.notes = f"{dispatch.notes or ''}\n{payload.notes}".strip()

    order = dispatch.order
    if order:
        order.status = "INSTALLATION"

    # CRITICAL BUSINESS RULES #8 & #9: Delivery confirmation activates eligible warranties automatically!
    # Warranty starts automatically on recorded delivery date!
    activated_warranties = []
    try:
        serials_list = json.loads(dispatch.serial_numbers or "[]")
    except Exception:
        serials_list = []

    for sn in serials_list:
        ser = db.query(SerializedEquipment).filter(SerializedEquipment.serial_number == sn).first()
        if ser:
            ser.current_location = f"Customer Site - {order.customer.address if order and order.customer else 'Delivered'}"
            # Calculate warranty duration based on category
            # Inverter: 2 years (730 days)
            # Battery: 2 years (730 days)
            # Panels: 20 years (7300 days)
            cat = ser.product.category if ser.product else ""
            if cat == "solar_panel":
                dur_days = 7300
            elif cat in ["inverter", "battery", "charge_controller"]:
                dur_days = 730
            else:
                dur_days = (ser.product.warranty_months * 30) if ser.product else 730

            start_d = payload.delivery_date
            end_d = start_d + timedelta(days=dur_days)

            ser.warranty_start = start_d
            ser.warranty_end = end_d

            war_num = f"WAR-2026-{random.randint(1000, 9999)}"
            while db.query(WarrantyRecord).filter(WarrantyRecord.warranty_number == war_num).first():
                war_num = f"WAR-2026-{random.randint(1000, 9999)}"

            # Create or update WarrantyRecord
            existing_war = db.query(WarrantyRecord).filter(WarrantyRecord.serial_number == sn).first()
            if not existing_war:
                war = WarrantyRecord(
                    warranty_number=war_num,
                    serial_number=sn,
                    product_id=ser.product_id,
                    customer_id=order.customer_id if order else ser.customer_id,
                    order_id=order.id if order else None,
                    delivery_date=start_d,
                    warranty_start=start_d,
                    warranty_end=end_d,
                    status="COVERED",
                    coverage_terms="100% parts & labor covered under manufacturer warranty policy."
                )
                db.add(war)
                activated_warranties.append(war_num)

    # Automatically create an Installation Job if not already created
    existing_job = db.query(InstallationJob).filter(InstallationJob.order_id == order.id).first() if order else None
    if not existing_job and order:
        job_num = f"INST-2026-{random.randint(1000, 9999)}"
        job = InstallationJob(
            job_number=job_num,
            order_id=order.id,
            customer_id=order.customer_id,
            scheduled_date=payload.delivery_date + timedelta(days=1),
            status="SCHEDULED",
            capacity_kw=order.capacity_kw,
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
            testing_results="Pending Installation",
            labour_hours=6.0
        )
        db.add(job)

    db.commit()

    return {
        "success": True,
        "message": f"Delivery confirmed! Order {order.order_number if order else ''} moved to Installation.",
        "delivery_date": payload.delivery_date,
        "activated_warranties": activated_warranties
    }
