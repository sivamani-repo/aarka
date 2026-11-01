import json
import random
from collections import Counter
from typing import List, Optional
from datetime import date, timedelta
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory import Dispatch, SerializedEquipment, InventoryItem, StockMovement
from app.models.commercial import SalesOrder
from app.models.installation import InstallationJob
from app.models.service import WarrantyRecord
from app.schemas.schemas import DispatchCreate, DispatchConfirmDelivery, DispatchOut
from app.core.permissions import get_current_user
from app.core.rbac import ASSIGN, canonical_role, has_permission
from app.core.warranty_service import add_calendar_months
from app.models.user import User

router = APIRouter(prefix="/api/dispatches", tags=["Warehouse Dispatch & Delivery"])


def _dispatch_stock_lines(db: Session, delivery_reference: str) -> list:
    movements = (
        db.query(StockMovement)
        .filter(
            StockMovement.reference_type == "DISPATCH",
            StockMovement.reference_id == delivery_reference,
        )
        .order_by(StockMovement.id.asc())
        .all()
    )
    return [
        {
            "product_id": movement.product_id,
            "product_name": movement.product.name if movement.product else "Unknown product",
            "previous_stock": movement.quantity_before,
            "dispatched_quantity": abs(movement.quantity),
            "remaining_stock": movement.quantity_after,
        }
        for movement in movements
    ]


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
            stock_lines=_dispatch_stock_lines(db, d.delivery_reference),
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
    order = (
        db.query(SalesOrder)
        .filter(SalesOrder.id == payload.order_id)
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "READY_FOR_DISPATCH":
        raise HTTPException(status_code=409, detail="Order is not ready for dispatch.")
    if db.query(Dispatch.id).filter(Dispatch.order_id == order.id).first():
        raise HTTPException(status_code=409, detail="This order already has a dispatch.")

    assigned_user_id = _resolve_dispatch_assignee(db, current_user, payload.assigned_user_id)

    requested_serials = [serial.strip().upper() for serial in payload.serial_numbers]
    if any(not serial for serial in requested_serials):
        raise HTTPException(status_code=400, detail="Serial numbers cannot be empty.")
    if len(set(requested_serials)) != len(requested_serials):
        raise HTTPException(status_code=400, detail="A serial number cannot be dispatched more than once.")

    required_quantities = Counter()
    required_serial_quantities = Counter()
    if not order.items:
        raise HTTPException(status_code=409, detail="Order has no inventory line items.")
    for item in order.items:
        if not item.product_id:
            raise HTTPException(
                status_code=409,
                detail=f"Order item {item.product_name} is not linked to an inventory product.",
            )
        quantity = float(item.quantity)
        if quantity <= 0 or not quantity.is_integer():
            raise HTTPException(
                status_code=400,
                detail=f"Order item {item.product_name} must have a positive whole-number quantity.",
            )
        required_quantities[item.product_id] += int(quantity)
        if item.is_serialized:
            required_serial_quantities[item.product_id] += int(quantity)

    inventory_by_product = {}
    for product_id, requested_quantity in sorted(required_quantities.items()):
        inventory = (
            db.query(InventoryItem)
            .filter(InventoryItem.product_id == product_id)
            .with_for_update()
            .first()
        )
        if inventory is None:
            raise HTTPException(
                status_code=409,
                detail=f"Inventory is not configured for product {product_id}.",
            )
        available_quantity = inventory.quantity - inventory.reserved_quantity
        if requested_quantity > available_quantity:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Insufficient stock for product {product_id}: "
                    f"{available_quantity} available, {requested_quantity} required."
                ),
            )
        inventory_by_product[product_id] = inventory

    serials_by_product = Counter()
    validated_serials = []
    for serial_number in sorted(requested_serials):
        serial = (
            db.query(SerializedEquipment)
            .filter(SerializedEquipment.serial_number == serial_number)
            .with_for_update()
            .first()
        )
        if serial is None:
            raise HTTPException(
                status_code=400,
                detail=f"Serial number {serial_number} was not found in inventory.",
            )
        if serial.status not in {"AVAILABLE", "IN_STOCK"}:
            raise HTTPException(
                status_code=409,
                detail=f"Serial number {serial_number} is not available for dispatch.",
            )
        if serial.product_id not in required_serial_quantities:
            raise HTTPException(
                status_code=400,
                detail=f"Serial number {serial_number} does not match a serialized order item.",
            )
        if serial.order_id not in (None, order.id):
            raise HTTPException(
                status_code=409,
                detail=f"Serial number {serial_number} is assigned to another order.",
            )
        serials_by_product[serial.product_id] += 1
        validated_serials.append(serial)

    if serials_by_product != required_serial_quantities:
        raise HTTPException(
            status_code=400,
            detail="The scanned serial numbers must match each serialized order line quantity.",
        )

    deliv_ref = payload.delivery_reference or f"DISP-{date.today().year}-{uuid4().hex[:8].upper()}"
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
    db.flush()

    for ser in validated_serials:
        ser.status = "DISPATCHED"
        ser.order_id = order.id
        ser.customer_id = order.customer_id
        ser.dispatch_id = dispatch.id
        ser.dispatch_date = dispatch.dispatch_date
        ser.current_location = "In Transit to Customer Site"

    for product_id, quantity in sorted(required_quantities.items()):
        inventory = inventory_by_product[product_id]
        previous_quantity = inventory.quantity
        remaining_quantity = previous_quantity - quantity
        inventory.quantity = remaining_quantity
        db.add(
            StockMovement(
                product_id=product_id,
                movement_type="DISPATCHED",
                quantity=-quantity,
                quantity_before=previous_quantity,
                quantity_after=remaining_quantity,
                reference_type="DISPATCH",
                reference_id=deliv_ref,
                notes=f"Dispatched for order {order.order_number}",
            )
        )

    order.status = "DISPATCHED"
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Dispatch could not be saved because its reference already exists.",
        ) from exc
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
        stock_lines=_dispatch_stock_lines(db, dispatch.delivery_reference),
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
    dispatch = (
        _scope_dispatches(db.query(Dispatch), current_user)
        .filter(Dispatch.id == dispatch_id)
        .with_for_update()
        .first()
    )
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    if dispatch.status != "DISPATCHED":
        raise HTTPException(status_code=409, detail="Only dispatched orders can be confirmed.")
    if dispatch.dispatch_date and payload.delivery_date < dispatch.dispatch_date:
        raise HTTPException(
            status_code=400,
            detail="Delivery date cannot be earlier than the dispatch date.",
        )

    order = dispatch.order
    if not order:
        raise HTTPException(status_code=409, detail="Dispatch order is unavailable.")

    try:
        serials_list = json.loads(dispatch.serial_numbers or "[]")
    except (json.JSONDecodeError, TypeError) as exc:
        raise HTTPException(
            status_code=500,
            detail="Stored dispatch serial data is invalid.",
        ) from exc
    if not isinstance(serials_list, list) or not all(isinstance(sn, str) for sn in serials_list):
        raise HTTPException(status_code=500, detail="Stored dispatch serial data is invalid.")

    serials = []
    for serial_number in serials_list:
        serial = (
            db.query(SerializedEquipment)
            .filter(SerializedEquipment.serial_number == serial_number)
            .with_for_update()
            .first()
        )
        if serial is None or serial.product is None:
            raise HTTPException(
                status_code=409,
                detail=f"Product details for serial number {serial_number} are unavailable.",
            )
        if not serial.product.warranty_months or serial.product.warranty_months <= 0:
            raise HTTPException(
                status_code=409,
                detail=f"Verified warranty duration is missing for serial number {serial_number}.",
            )
        serials.append(serial)

    dispatch.status = "DELIVERED"
    dispatch.delivery_date = payload.delivery_date
    dispatch.customer_confirmed = payload.customer_confirmed
    if payload.delivery_proof_url:
        dispatch.delivery_proof_url = payload.delivery_proof_url
    if payload.notes:
        dispatch.notes = f"{dispatch.notes or ''}\n{payload.notes}".strip()
    order.status = "INSTALLATION"

    pending_warranties = []
    for serial in serials:
        serial.current_location = (
            f"Customer Site - {order.customer.address}"
            if order.customer and order.customer.address
            else "Customer Site"
        )
        warranty_start = payload.delivery_date
        warranty_end = add_calendar_months(warranty_start, serial.product.warranty_months)
        serial.warranty_start = warranty_start
        serial.warranty_end = warranty_end

        existing_warranty = (
            db.query(WarrantyRecord)
            .filter(WarrantyRecord.serial_number == serial.serial_number)
            .first()
        )
        if existing_warranty is None:
            warranty_number = (
                f"WAR-{date.today().year}-{uuid4().hex[:8].upper()}"
            )
            db.add(
                WarrantyRecord(
                    warranty_number=warranty_number,
                    serial_number=serial.serial_number,
                    product_id=serial.product_id,
                    customer_id=order.customer_id,
                    order_id=order.id,
                    delivery_date=warranty_start,
                    warranty_start=warranty_start,
                    warranty_end=warranty_end,
                    duration_months=serial.product.warranty_months,
                    manufacturer=serial.product.manufacturer,
                    status="PENDING_ACTIVATION",
                    coverage_terms=(
                        "Manufacturer coverage terms require verification against "
                        "the product documentation."
                    ),
                )
            )
            pending_warranties.append(warranty_number)

    # Automatically create an Installation Job if not already created
    existing_job = db.query(InstallationJob).filter(InstallationJob.order_id == order.id).first() if order else None
    if not existing_job and order:
        job_num = f"INST-{date.today().year}-{random.randint(1000, 9999)}"
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
        "warranties_pending_activation": pending_warranties,
    }
