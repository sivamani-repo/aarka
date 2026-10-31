import random
from typing import List, Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commercial import Quotation, QuotationItem, SalesOrder, SalesOrderItem
from app.models.customer import Customer, Lead
from app.models.survey import SiteSurvey
from app.models.product import Product
from app.schemas.schemas import QuotationCreate, QuotationOut, OrderOut
from app.routers.bom import calculate_bom
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/quotations", tags=["Quotations & Sales"])


@router.get("", response_model=List[QuotationOut])
def list_quotations(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Quotation)
    if status and status != "ALL":
        query = query.filter(Quotation.status == status)
    if customer_id:
        query = query.filter(Quotation.customer_id == customer_id)

    quotations = query.order_by(Quotation.id.desc()).all()
    results = []
    for q in quotations:
        items = [
            {
                "id": it.id,
                "product_id": it.product_id,
                "product_name": it.product_name,
                "category": it.category,
                "sku": it.sku,
                "quantity": it.quantity,
                "unit": it.unit,
                "unit_price": it.unit_price,
                "total_price": it.total_price,
                "is_serialized": it.is_serialized
            }
            for it in q.items
        ]
        q_out = QuotationOut(
            id=q.id,
            quotation_number=q.quotation_number,
            customer_id=q.customer_id,
            lead_id=q.lead_id,
            survey_id=q.survey_id,
            package_type=q.package_type,
            capacity_kw=q.capacity_kw,
            system_type=q.system_type,
            hardware_cost=q.hardware_cost,
            installation_cost=q.installation_cost,
            additional_expenses=q.additional_expenses,
            subtotal=q.subtotal,
            discount=q.discount,
            tax_rate=q.tax_rate,
            tax_amount=q.tax_amount,
            total_amount=q.total_amount,
            advance_amount=q.advance_amount,
            balance_amount=q.balance_amount,
            valid_until=q.valid_until,
            terms_conditions=q.terms_conditions,
            notes=q.notes,
            status=q.status,
            customer_name=q.customer.name if q.customer else None,
            customer_phone=q.customer.phone if q.customer else None,
            customer_address=q.customer.address if q.customer else None,
            items=items,
            created_at=q.created_at
        )
        results.append(q_out)
    return results


@router.post("", response_model=QuotationOut)
def create_quotation(
    payload: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # CRITICAL BUSINESS RULE #1: A required survey must be approved before quotation finalization
    if payload.survey_id:
        survey = db.query(SiteSurvey).filter(SiteSurvey.id == payload.survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Site survey not found")
        if survey.approval_status != "APPROVED":
            raise HTTPException(
                status_code=400,
                detail=f"Business Rule Violation: Site survey {survey.survey_reference} has status '{survey.approval_status}'. A required survey must be approved before quotation finalization."
            )

    # CRITICAL BUSINESS RULE #2: Calculate BOM from configured recipes
    bom_res = calculate_bom(
        package_type=payload.package_type,
        capacity_kw=payload.capacity_kw,
        include_installation=True,
        db=db,
        current_user=current_user
    )

    hardware_cost = bom_res.hardware_cost
    installation_cost = bom_res.installation_cost
    subtotal = hardware_cost + installation_cost
    discount = payload.discount or 0.0
    discounted_subtotal = max(0.0, subtotal - discount)
    tax_rate = 0.18
    tax_amount = round(discounted_subtotal * tax_rate, 2)
    grand_total = round(discounted_subtotal + tax_amount, 2)

    adv_pct = payload.advance_percentage if payload.advance_percentage else 20.0
    advance_amount = round(grand_total * (adv_pct / 100.0), 2)
    balance_amount = round(grand_total - advance_amount, 2)

    quotation_num = f"QT-2026-{random.randint(1000, 9999)}"
    while db.query(Quotation).filter(Quotation.quotation_number == quotation_num).first():
        quotation_num = f"QT-2026-{random.randint(1000, 9999)}"

    terms = payload.terms_conditions or (
        "1. 20% advance upon quotation acceptance.\n"
        "2. 70% before warehouse dispatch of equipment.\n"
        "3. 10% after successful installation, commissioning, and customer acceptance.\n"
        "4. Inverter warranty: 2 years. Solar panel warranty: 20 years. Battery: 2 years.\n"
        "5. Price includes net-metering liaison and subsidy documentation support."
    )

    quotation = Quotation(
        quotation_number=quotation_num,
        customer_id=customer.id,
        lead_id=payload.lead_id,
        survey_id=payload.survey_id,
        package_type=payload.package_type,
        capacity_kw=payload.capacity_kw,
        system_type="Off-Grid" if "Off-Grid" in payload.package_type else "On-Grid",
        hardware_cost=hardware_cost,
        installation_cost=installation_cost,
        additional_expenses=0.0,
        subtotal=subtotal,
        discount=discount,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total_amount=grand_total,
        advance_amount=advance_amount,
        balance_amount=balance_amount,
        valid_until=date.today() + timedelta(days=30),
        terms_conditions=terms,
        notes=f"Generated by {current_user.name} for {customer.name}",
        status="DRAFT"
    )
    db.add(quotation)
    db.commit()
    db.refresh(quotation)

    # Snapshot BOM components into QuotationItem records
    for comp in bom_res.components:
        q_item = QuotationItem(
            quotation_id=quotation.id,
            product_id=comp.product_id,
            product_name=comp.product_name,
            category=comp.category,
            sku=comp.sku,
            quantity=comp.quantity,
            unit=comp.unit,
            unit_price=comp.unit_price,
            total_price=comp.total_price,
            is_serialized=comp.is_serialized
        )
        db.add(q_item)

    if payload.lead_id:
        lead = db.query(Lead).filter(Lead.id == payload.lead_id).first()
        if lead:
            lead.stage = "QUOTATION"
            lead.estimated_value = grand_total

    db.commit()
    db.refresh(quotation)

    return get_quotation(quotation.id, db, current_user)


@router.get("/{quotation_id}", response_model=QuotationOut)
def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quotation not found")

    items = [
        {
            "id": it.id,
            "product_id": it.product_id,
            "product_name": it.product_name,
            "category": it.category,
            "sku": it.sku,
            "quantity": it.quantity,
            "unit": it.unit,
            "unit_price": it.unit_price,
            "total_price": it.total_price,
            "is_serialized": it.is_serialized
        }
        for it in q.items
    ]

    return QuotationOut(
        id=q.id,
        quotation_number=q.quotation_number,
        customer_id=q.customer_id,
        lead_id=q.lead_id,
        survey_id=q.survey_id,
        package_type=q.package_type,
        capacity_kw=q.capacity_kw,
        system_type=q.system_type,
        hardware_cost=q.hardware_cost,
        installation_cost=q.installation_cost,
        additional_expenses=q.additional_expenses,
        subtotal=q.subtotal,
        discount=q.discount,
        tax_rate=q.tax_rate,
        tax_amount=q.tax_amount,
        total_amount=q.total_amount,
        advance_amount=q.advance_amount,
        balance_amount=q.balance_amount,
        valid_until=q.valid_until,
        terms_conditions=q.terms_conditions,
        notes=q.notes,
        status=q.status,
        customer_name=q.customer.name if q.customer else None,
        customer_phone=q.customer.phone if q.customer else None,
        customer_address=q.customer.address if q.customer else None,
        items=items,
        created_at=q.created_at
    )


@router.post("/{quotation_id}/send")
def send_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quotation not found")
    q.status = "SENT"
    db.commit()
    return {"success": True, "message": f"Quotation {q.quotation_number} marked as SENT"}


@router.post("/{quotation_id}/accept", response_model=OrderOut)
def accept_quotation_and_create_order(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quotation not found")

    # Mark quotation as ACCEPTED
    q.status = "ACCEPTED"

    # If lead exists, mark CONVERTED
    if q.lead_id:
        lead = db.query(Lead).filter(Lead.id == q.lead_id).first()
        if lead:
            lead.stage = "CONVERTED"
            lead.status = "CLOSED_WON"
            lead.notes = f"{lead.notes or ''}\nQuotation accepted! Converted to order.".strip()

    # CRITICAL BUSINESS RULE #3 & #4: Generate Sales Order and snapshot agreed items and prices
    order_num = f"SO-2026-{random.randint(1000, 9999)}"
    while db.query(SalesOrder).filter(SalesOrder.order_number == order_num).first():
        order_num = f"SO-2026-{random.randint(1000, 9999)}"

    order = SalesOrder(
        order_number=order_num,
        quotation_id=q.id,
        customer_id=q.customer_id,
        package_type=q.package_type,
        capacity_kw=q.capacity_kw,
        hardware_cost=q.hardware_cost,
        installation_cost=q.installation_cost,
        total_amount=q.total_amount,
        advance_paid=0.0,
        balance_due=q.total_amount,
        delivery_address=q.customer.address if q.customer else "Site Address",
        status="CONFIRMED",
        picklist_generated=True
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Snapshot quotation items into order items (Picklist)
    for q_item in q.items:
        o_item = SalesOrderItem(
            order_id=order.id,
            product_id=q_item.product_id,
            product_name=q_item.product_name,
            category=q_item.category,
            quantity=q_item.quantity,
            unit_price=q_item.unit_price,
            total_price=q_item.total_price,
            is_serialized=q_item.is_serialized
        )
        db.add(o_item)

    db.commit()
    db.refresh(order)

    # Return order out
    items = [
        {
            "id": it.id,
            "product_id": it.product_id,
            "product_name": it.product_name,
            "category": it.category,
            "quantity": it.quantity,
            "unit_price": it.unit_price,
            "total_price": it.total_price,
            "is_serialized": it.is_serialized
        }
        for it in order.items
    ]

    return OrderOut(
        id=order.id,
        order_number=order.order_number,
        quotation_id=order.quotation_id,
        customer_id=order.customer_id,
        package_type=order.package_type,
        capacity_kw=order.capacity_kw,
        hardware_cost=order.hardware_cost,
        installation_cost=order.installation_cost,
        total_amount=order.total_amount,
        advance_paid=order.advance_paid,
        balance_due=order.balance_due,
        delivery_address=order.delivery_address,
        status=order.status,
        picklist_generated=order.picklist_generated,
        customer_name=order.customer.name if order.customer else None,
        customer_phone=order.customer.phone if order.customer else None,
        items=items,
        payments=[],
        created_at=order.created_at
    )

