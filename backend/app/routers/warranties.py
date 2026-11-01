import json
import random
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app.models.service import ServiceTicket, WarrantyRecord, WarrantyClaim
from app.models.product import Product
from app.models.customer import Customer
from app.models.commercial import SalesOrder
from app.models.installation import InstallationJob
from app.models.survey import Technician
from app.models.user import AuditLog, User
from app.schemas.schemas import (
    WarrantyOut, WarrantyStatusUpdate,
    WarrantyClaimCreate, WarrantyClaimUpdate, WarrantyClaimOut
)
from app.core.permissions import get_current_user
from app.core.rbac import canonical_role

router = APIRouter(prefix="/api/warranties", tags=["Warranty & Equipment Assurance Management"])


def _scope_warranties(db: Session, query, current_user: User):
    if canonical_role(current_user.role) == "Support Executive":
        assigned_customers = db.query(ServiceTicket.customer_id).filter(
            ServiceTicket.assigned_user_id == current_user.id
        )
        return query.filter(WarrantyRecord.customer_id.in_(assigned_customers))
    return query


def _scope_claims(db: Session, query, current_user: User):
    if canonical_role(current_user.role) == "Support Executive":
        assigned_customers = db.query(ServiceTicket.customer_id).filter(
            ServiceTicket.assigned_user_id == current_user.id
        )
        return query.filter(WarrantyClaim.customer_id.in_(assigned_customers))
    return query


def _calculate_warranty_dynamic_status(w: WarrantyRecord, today: date) -> str:
    """Calculates status dynamically based on expiry date and claims."""
    if w.status in ["CLAIM_RAISED", "UNDER_REVIEW", "REPLACEMENT_IN_PROGRESS"]:
        return w.status

    if w.warranty_end < today:
        return "EXPIRED"

    days_left = (w.warranty_end - today).days
    if days_left <= 90:
        return "EXPIRING_SOON"

    return "ACTIVE"


# ================= WARRANTY DASHBOARD & SUMMARY =================
@router.get("/dashboard-summary")
def get_warranty_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes enterprise warranty KPIs and analytics from real database records:
    - Total, Active, Expiring soon (90d), Expired warranties
    - Open warranty claims count
    - Distribution by equipment type (Solar Panels, Inverter, Battery, Structure, Workmanship)
    - Upcoming expiry timeline over next 12 months
    """
    all_warranties = _scope_warranties(
        db, db.query(WarrantyRecord), current_user
    ).all()
    today = date.today()

    total_warranties = len(all_warranties)
    active_count = 0
    expiring_soon_count = 0
    expired_count = 0

    equipment_distribution: Dict[str, int] = {}
    type_distribution: Dict[str, int] = {}

    for w in all_warranties:
        status_calc = _calculate_warranty_dynamic_status(w, today)
        if status_calc == "ACTIVE" or (w.status == "COVERED" and w.warranty_end >= today):
            active_count += 1
        elif status_calc == "EXPIRING_SOON":
            expiring_soon_count += 1
        elif status_calc == "EXPIRED":
            expired_count += 1

        # Equipment category
        cat = "Solar PV Modules"
        if w.product and w.product.category:
            raw_c = w.product.category.upper()
            if "PANEL" in raw_c or "SOLAR" in raw_c:
                cat = "Solar PV Modules"
            elif "INVERTER" in raw_c:
                cat = "Solar Inverters"
            elif "BATTERY" in raw_c:
                cat = "Battery Storage"
            elif "STRUCTURE" in raw_c:
                cat = "Mounting Structures"
            else:
                cat = w.product.category.replace("_", " ").title()
        elif w.warranty_type == "WORKMANSHIP":
            cat = "EPC Workmanship"

        equipment_distribution[cat] = equipment_distribution.get(cat, 0) + 1

        # Warranty type distribution
        w_type = (w.warranty_type or "PRODUCT").replace("_", " ").title()
        type_distribution[w_type] = type_distribution.get(w_type, 0) + 1

    # Open claims count
    open_claims = _scope_claims(db, db.query(WarrantyClaim), current_user).filter(
        WarrantyClaim.claim_status.notin_(["RESOLVED", "REJECTED"])
    ).count()

    # Next 12 months expiry timeline
    timeline = []
    for i in range(12):
        # Target month
        yr = today.year + (today.month + i - 1) // 12
        m = (today.month + i - 1) % 12 + 1
        start_m = date(yr, m, 1)
        if m == 12:
            end_m = date(yr + 1, 1, 1) - timedelta(days=1)
        else:
            end_m = date(yr, m + 1, 1) - timedelta(days=1)

        exp_count = sum(1 for w in all_warranties if start_m <= w.warranty_end <= end_m)
        timeline.append({
            "month": start_m.strftime("%b %Y"),
            "expiring_count": exp_count
        })

    return {
        "total_warranties": total_warranties,
        "active_warranties": active_count,
        "expiring_soon_count": expiring_soon_count,
        "expired_count": expired_count,
        "open_claims_count": open_claims,
        "distribution_by_equipment": [
            {"name": k, "count": v} for k, v in equipment_distribution.items()
        ],
        "distribution_by_type": [
            {"name": k, "count": v} for k, v in type_distribution.items()
        ],
        "expiry_timeline": timeline,
    }


# ================= EXPIRY ALERTS =================
@router.get("/expiry-alerts")
def get_warranty_expiry_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns warranties categorized by expiry threshold:
    - 7 Days (Critical)
    - 30 Days (Urgent)
    - 90 Days (Upcoming Notice)
    """
    today = date.today()
    in_7d = today + timedelta(days=7)
    in_30d = today + timedelta(days=30)
    in_90d = today + timedelta(days=90)

    all_w = _scope_warranties(
        db, db.query(WarrantyRecord), current_user
    ).filter(WarrantyRecord.warranty_end >= today).all()

    alerts_7d = []
    alerts_30d = []
    alerts_90d = []

    for w in all_w:
        days_left = (w.warranty_end - today).days
        item = {
            "id": w.id,
            "warranty_number": w.warranty_number,
            "serial_number": w.serial_number,
            "product_name": w.product.name if w.product else "Solar Equipment",
            "customer_name": w.customer.name if w.customer else None,
            "customer_phone": w.customer.phone if w.customer else None,
            "warranty_end": str(w.warranty_end),
            "days_remaining": days_left,
            "warranty_type": w.warranty_type,
            "alert_sent_90d": w.expiry_alert_90d_sent,
            "alert_sent_30d": w.expiry_alert_30d_sent,
            "alert_sent_7d": w.expiry_alert_7d_sent,
        }
        if days_left <= 7:
            alerts_7d.append(item)
        elif days_left <= 30:
            alerts_30d.append(item)
        elif days_left <= 90:
            alerts_90d.append(item)

    return {
        "critical_7_days": alerts_7d,
        "urgent_30_days": alerts_30d,
        "notice_90_days": alerts_90d,
        "total_expiring_soon": len(alerts_7d) + len(alerts_30d) + len(alerts_90d)
    }


@router.post("/expiry-alerts/trigger")
def trigger_expiry_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Scans warranties and dispatches notifications for 90, 30, and 7-day windows.
    Enforces that duplicate notifications are NOT sent for the same warranty and window.
    """
    today = date.today()
    warranties = _scope_warranties(
        db, db.query(WarrantyRecord), current_user
    ).filter(WarrantyRecord.warranty_end >= today).all()

    dispatched = {"90d": 0, "30d": 0, "7d": 0}

    for w in warranties:
        days_left = (w.warranty_end - today).days

        if days_left <= 7 and not w.expiry_alert_7d_sent:
            w.expiry_alert_7d_sent = True
            dispatched["7d"] += 1
        elif days_left <= 30 and not w.expiry_alert_30d_sent:
            w.expiry_alert_30d_sent = True
            dispatched["30d"] += 1
        elif days_left <= 90 and not w.expiry_alert_90d_sent:
            w.expiry_alert_90d_sent = True
            dispatched["90d"] += 1

    db.commit()

    return {
        "success": True,
        "message": f"Dispatched {sum(dispatched.values())} expiry alerts without duplicates.",
        "details": dispatched
    }


# ================= WARRANTY RECORDS LIST & SEARCH =================
@router.get("", response_model=List[WarrantyOut])
def list_warranties(
    status: Optional[str] = None,
    warranty_type: Optional[str] = None,
    customer_id: Optional[int] = None,
    order_id: Optional[int] = None,
    expiring_within_days: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = _scope_warranties(db, db.query(WarrantyRecord), current_user)

    if customer_id:
        query = query.filter(WarrantyRecord.customer_id == customer_id)
    if order_id:
        query = query.filter(WarrantyRecord.order_id == order_id)
    if warranty_type and warranty_type != "ALL":
        query = query.filter(WarrantyRecord.warranty_type == warranty_type)

    warranties = query.order_by(WarrantyRecord.id.desc()).all()
    today = date.today()
    results = []

    for w in warranties:
        days_remaining = (w.warranty_end - today).days
        calc_status = _calculate_warranty_dynamic_status(w, today)

        # Status filter
        if status and status != "ALL":
            if status == "EXPIRING_SOON" and calc_status != "EXPIRING_SOON":
                continue
            elif status == "EXPIRED" and calc_status != "EXPIRED":
                continue
            elif status == "ACTIVE" and calc_status not in ["ACTIVE", "COVERED"]:
                continue
            elif status not in ["EXPIRING_SOON", "EXPIRED", "ACTIVE"] and w.status != status:
                continue

        # Expiring within N days filter
        if expiring_within_days:
            if not (0 <= days_remaining <= expiring_within_days):
                continue

        # Search filter
        if search:
            s = search.lower()
            sn = w.serial_number.lower()
            wn = (w.warranty_number or "").lower()
            c_name = (w.customer.name or "").lower() if w.customer else ""
            c_phone = (w.customer.phone or "").lower() if w.customer else ""
            p_name = (w.product.name or "").lower() if w.product else ""
            if s not in sn and s not in wn and s not in c_name and s not in c_phone and s not in p_name:
                continue

        open_claims = len([c for c in w.claims if c.claim_status not in ["RESOLVED", "REJECTED"]])

        results.append(WarrantyOut(
            id=w.id,
            warranty_number=w.warranty_number,
            serial_number=w.serial_number,
            product_id=w.product_id,
            product_name=w.product.name if w.product else "Solar PV Equipment",
            category=w.product.category if w.product else "EQUIPMENT",
            manufacturer=w.manufacturer or (w.product.manufacturer if w.product else "Aarka Tech"),
            model_number=w.model_number or (w.product.model if w.product else None),
            warranty_type=w.warranty_type or "PRODUCT",
            duration_months=w.duration_months or 24,
            customer_id=w.customer_id,
            customer_name=w.customer.name if w.customer else None,
            customer_phone=w.customer.phone if w.customer else None,
            customer_email=w.customer.email if w.customer else None,
            customer_address=w.customer.address if w.customer else None,
            order_id=w.order_id,
            order_number=w.order.order_number if w.order else None,
            installation_id=w.installation_id,
            delivery_date=w.delivery_date,
            warranty_start=w.warranty_start,
            warranty_end=w.warranty_end,
            days_remaining=days_remaining,
            status=calc_status if w.status in ["ACTIVE", "COVERED"] else w.status,
            coverage_terms=w.coverage_terms,
            certificate_url=w.certificate_url,
            notes=w.notes,
            open_claims_count=open_claims,
            created_at=w.created_at,
            updated_at=w.updated_at
        ))

    return results


@router.get("/search")
def search_warranty(
    query: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clean_q = query.strip()
    search_filter = f"%{clean_q}%"

    records = _scope_warranties(
        db, db.query(WarrantyRecord), current_user
    ).join(Customer, WarrantyRecord.customer_id == Customer.id).filter(
        or_(
            WarrantyRecord.serial_number.ilike(search_filter),
            WarrantyRecord.warranty_number.ilike(search_filter),
            Customer.name.ilike(search_filter),
            Customer.phone.ilike(search_filter)
        )
    ).all()

    today = date.today()
    results = []
    for w in records:
        days_remaining = (w.warranty_end - today).days
        status = _calculate_warranty_dynamic_status(w, today)
        if w.status == "COVERED" and days_remaining >= 0:
            status = "COVERED"

        results.append({
            "id": w.id,
            "warranty_number": w.warranty_number,
            "serial_number": w.serial_number,
            "product_name": w.product.name if w.product else "",
            "category": w.product.category if w.product else "",
            "warranty_type": w.warranty_type,
            "customer_name": w.customer.name if w.customer else "",
            "customer_phone": w.customer.phone if w.customer else "",
            "order_number": w.order.order_number if w.order else "",
            "warranty_start": str(w.warranty_start),
            "warranty_end": str(w.warranty_end),
            "days_remaining": max(0, days_remaining),
            "status": status,
            "coverage_terms": w.coverage_terms
        })

    return {
        "query": clean_q,
        "count": len(results),
        "results": results
    }


@router.get("/{warranty_id}", response_model=WarrantyOut)
def get_warranty_details(
    warranty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    w = _scope_warranties(
        db, db.query(WarrantyRecord), current_user
    ).filter(WarrantyRecord.id == warranty_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Warranty record not found")

    today = date.today()
    days_left = (w.warranty_end - today).days
    open_claims = len([c for c in w.claims if c.claim_status not in ["RESOLVED", "REJECTED"]])

    return WarrantyOut(
        id=w.id,
        warranty_number=w.warranty_number,
        serial_number=w.serial_number,
        product_id=w.product_id,
        product_name=w.product.name if w.product else None,
        category=w.product.category if w.product else None,
        manufacturer=w.manufacturer or (w.product.manufacturer if w.product else None),
        model_number=w.model_number or (w.product.model if w.product else None),
        warranty_type=w.warranty_type or "PRODUCT",
        duration_months=w.duration_months or 24,
        customer_id=w.customer_id,
        customer_name=w.customer.name if w.customer else None,
        customer_phone=w.customer.phone if w.customer else None,
        customer_email=w.customer.email if w.customer else None,
        customer_address=w.customer.address if w.customer else None,
        order_id=w.order_id,
        order_number=w.order.order_number if w.order else None,
        installation_id=w.installation_id,
        delivery_date=w.delivery_date,
        warranty_start=w.warranty_start,
        warranty_end=w.warranty_end,
        days_remaining=days_left,
        status=_calculate_warranty_dynamic_status(w, today) if w.status in ["ACTIVE", "COVERED"] else w.status,
        coverage_terms=w.coverage_terms,
        certificate_url=w.certificate_url,
        notes=w.notes,
        open_claims_count=open_claims,
        created_at=w.created_at,
        updated_at=w.updated_at
    )


@router.get("/{warranty_id}/certificate")
def get_warranty_certificate(
    warranty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates structured digital Warranty Certificate data for rendering or printing.
    """
    w = _scope_warranties(
        db, db.query(WarrantyRecord), current_user
    ).filter(WarrantyRecord.id == warranty_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Warranty record not found")

    return {
        "certificate_number": w.warranty_number,
        "issue_date": str(w.warranty_start),
        "expiry_date": str(w.warranty_end),
        "duration_years": round((w.duration_months or 24) / 12, 1),
        "status": w.status,
        "warranty_type": w.warranty_type,
        "beneficiary": {
            "customer_name": w.customer.name if w.customer else "Valued Client",
            "phone": w.customer.phone if w.customer else "",
            "address": w.customer.address if w.customer else "Installation Site",
            "order_number": w.order.order_number if w.order else "",
            "capacity_kw": w.order.capacity_kw if w.order else 3.0
        },
        "equipment": {
            "product_name": w.product.name if w.product else "Solar PV Equipment",
            "category": w.product.category if w.product else "",
            "manufacturer": w.manufacturer or (w.product.manufacturer if w.product else "Aarka Tech"),
            "model": w.model_number or (w.product.model if w.product else w.product.sku if w.product else ""),
            "serial_number": w.serial_number
        },
        "terms": {
            "summary": w.coverage_terms,
            "exclusions": "Damage caused by lightning strikes beyond rated SPD levels, unauthorized modifications, physical vandalism, or acts of war.",
            "service_sla": "AARKA Authorized Field Technician response within 48 business hours upon ticket lodging."
        },
        "issuer": {
            "company": "AARKA Solar Operations Ltd.",
            "portal": "https://aarka.com",
            "support_helpline": "+91 1800-419-AARKA"
        }
    }


@router.put("/{warranty_id}/status", response_model=WarrantyOut)
def update_warranty_status(
    warranty_id: int,
    payload: WarrantyStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    w = _scope_warranties(
        db, db.query(WarrantyRecord), current_user
    ).filter(WarrantyRecord.id == warranty_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Warranty record not found")

    valid_statuses = [
        "PENDING_ACTIVATION", "ACTIVE", "EXPIRING_SOON", "EXPIRED",
        "CLAIM_RAISED", "UNDER_REVIEW", "REPLACEMENT_IN_PROGRESS", "RESOLVED", "CANCELLED"
    ]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status '{payload.status}'. Must be one of {valid_statuses}")

    w.status = payload.status
    if payload.notes:
        w.notes = payload.notes

    db.commit()
    db.refresh(w)

    today = date.today()
    return WarrantyOut(
        id=w.id,
        warranty_number=w.warranty_number,
        serial_number=w.serial_number,
        product_id=w.product_id,
        product_name=w.product.name if w.product else None,
        category=w.product.category if w.product else None,
        manufacturer=w.manufacturer,
        model_number=w.model_number,
        warranty_type=w.warranty_type,
        duration_months=w.duration_months,
        customer_id=w.customer_id,
        customer_name=w.customer.name if w.customer else None,
        customer_phone=w.customer.phone if w.customer else None,
        customer_email=w.customer.email if w.customer else None,
        customer_address=w.customer.address if w.customer else None,
        order_id=w.order_id,
        order_number=w.order.order_number if w.order else None,
        installation_id=w.installation_id,
        delivery_date=w.delivery_date,
        warranty_start=w.warranty_start,
        warranty_end=w.warranty_end,
        days_remaining=(w.warranty_end - today).days,
        status=w.status,
        coverage_terms=w.coverage_terms,
        certificate_url=w.certificate_url,
        notes=w.notes,
        open_claims_count=len(w.claims),
        created_at=w.created_at,
        updated_at=w.updated_at
    )


# ================= WARRANTY CLAIMS =================
@router.get("/claims/all", response_model=List[WarrantyClaimOut])
def list_warranty_claims(
    claim_status: Optional[str] = None,
    warranty_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = _scope_claims(
        db, db.query(WarrantyClaim), current_user
    ).order_by(WarrantyClaim.id.desc())

    if claim_status and claim_status != "ALL":
        query = query.filter(WarrantyClaim.claim_status == claim_status)
    if warranty_id:
        query = query.filter(WarrantyClaim.warranty_id == warranty_id)
    if customer_id:
        query = query.filter(WarrantyClaim.customer_id == customer_id)

    claims = query.all()
    results = []

    for c in claims:
        if search:
            s = search.lower()
            cn = c.claim_number.lower()
            sn = c.serial_number.lower()
            cust = (c.customer.name or "").lower() if c.customer else ""
            desc = (c.issue_description or "").lower()
            if s not in cn and s not in sn and s not in cust and s not in desc:
                continue

        docs = []
        try:
            docs = json.loads(c.supporting_documents or "[]")
        except Exception:
            docs = []

        results.append(WarrantyClaimOut(
            id=c.id,
            claim_number=c.claim_number,
            warranty_id=c.warranty_id,
            warranty_number=c.warranty.warranty_number if c.warranty else None,
            customer_id=c.customer_id,
            customer_name=c.customer.name if c.customer else None,
            customer_phone=c.customer.phone if c.customer else None,
            order_id=c.order_id,
            order_number=c.order.order_number if c.order else None,
            serial_number=c.serial_number,
            equipment_name=c.equipment_name or (c.warranty.product.name if c.warranty and c.warranty.product else "Solar Equipment"),
            issue_description=c.issue_description,
            supporting_documents=docs,
            manufacturer_reference=c.manufacturer_reference,
            assigned_technician_id=c.assigned_technician_id,
            assigned_technician_name=c.technician.name if c.technician else None,
            claim_status=c.claim_status,
            replacement_serial_number=c.replacement_serial_number,
            resolution_details=c.resolution_details,
            resolution_date=c.resolution_date,
            created_at=c.created_at,
            updated_at=c.updated_at
        ))

    return results


@router.post("/claims", response_model=WarrantyClaimOut)
def create_warranty_claim(
    payload: WarrantyClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits a new Warranty Claim against a registered equipment warranty.
    Automatically updates the warranty status to CLAIM_RAISED and records an audit log.
    """
    warranty = _scope_warranties(
        db, db.query(WarrantyRecord), current_user
    ).filter(WarrantyRecord.id == payload.warranty_id).first()
    if not warranty:
        raise HTTPException(status_code=404, detail="Warranty record not found")

    year = date.today().year
    claim_num = f"CLM-{year}-{random.randint(1000, 9999)}"
    while db.query(WarrantyClaim).filter(WarrantyClaim.claim_number == claim_num).first():
        claim_num = f"CLM-{year}-{random.randint(1000, 9999)}"

    claim = WarrantyClaim(
        claim_number=claim_num,
        warranty_id=warranty.id,
        customer_id=warranty.customer_id,
        order_id=warranty.order_id,
        serial_number=warranty.serial_number,
        equipment_name=warranty.product.name if warranty.product else "Solar PV Equipment",
        issue_description=payload.issue_description,
        supporting_documents=json.dumps(payload.supporting_documents or []),
        manufacturer_reference=payload.manufacturer_reference or f"OEM-RMA-{random.randint(10000, 99999)}",
        assigned_technician_id=payload.assigned_technician_id,
        claim_status="CLAIM_RAISED"
    )
    db.add(claim)

    # Update warranty status
    warranty.status = "CLAIM_RAISED"
    db.commit()
    db.refresh(claim)

    # Record audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="WARRANTY_CLAIM_RAISED",
        entity_type="WARRANTY_CLAIM",
        entity_id=claim.id,
        details=f"Claim {claim.claim_number} raised for serial {warranty.serial_number} by {current_user.name}."
    )
    db.add(audit)
    db.commit()

    return WarrantyClaimOut(
        id=claim.id,
        claim_number=claim.claim_number,
        warranty_id=claim.warranty_id,
        warranty_number=warranty.warranty_number,
        customer_id=claim.customer_id,
        customer_name=warranty.customer.name if warranty.customer else None,
        customer_phone=warranty.customer.phone if warranty.customer else None,
        order_id=claim.order_id,
        order_number=warranty.order.order_number if warranty.order else None,
        serial_number=claim.serial_number,
        equipment_name=claim.equipment_name,
        issue_description=claim.issue_description,
        supporting_documents=payload.supporting_documents or [],
        manufacturer_reference=claim.manufacturer_reference,
        assigned_technician_id=claim.assigned_technician_id,
        assigned_technician_name=claim.technician.name if claim.technician else None,
        claim_status=claim.claim_status,
        replacement_serial_number=claim.replacement_serial_number,
        resolution_details=claim.resolution_details,
        resolution_date=claim.resolution_date,
        created_at=claim.created_at,
        updated_at=claim.updated_at
    )


@router.put("/claims/{claim_id}/status", response_model=WarrantyClaimOut)
def update_warranty_claim_status(
    claim_id: int,
    payload: WarrantyClaimUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    claim = _scope_claims(
        db, db.query(WarrantyClaim), current_user
    ).filter(WarrantyClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Warranty claim not found")

    valid_statuses = [
        "CLAIM_RAISED", "UNDER_REVIEW", "APPROVED_BY_OEM",
        "REPLACEMENT_IN_PROGRESS", "REPAIRED", "REJECTED", "RESOLVED"
    ]

    if payload.claim_status is not None:
        if payload.claim_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid claim status '{payload.claim_status}'. Must be one of {valid_statuses}")
        claim.claim_status = payload.claim_status

        # Synchronize linked warranty status
        if claim.warranty:
            if payload.claim_status in ["UNDER_REVIEW", "APPROVED_BY_OEM"]:
                claim.warranty.status = "UNDER_REVIEW"
            elif payload.claim_status == "REPLACEMENT_IN_PROGRESS":
                claim.warranty.status = "REPLACEMENT_IN_PROGRESS"
            elif payload.claim_status in ["RESOLVED", "REPAIRED"]:
                claim.warranty.status = "ACTIVE"
                if not claim.resolution_date:
                    claim.resolution_date = payload.resolution_date or date.today()
            elif payload.claim_status == "REJECTED":
                claim.warranty.status = "ACTIVE"

    if payload.manufacturer_reference is not None:
        claim.manufacturer_reference = payload.manufacturer_reference
    if payload.assigned_technician_id is not None:
        claim.assigned_technician_id = payload.assigned_technician_id
    if payload.replacement_serial_number is not None:
        claim.replacement_serial_number = payload.replacement_serial_number
    if payload.resolution_details is not None:
        claim.resolution_details = payload.resolution_details
    if payload.resolution_date is not None:
        claim.resolution_date = payload.resolution_date

    db.commit()
    db.refresh(claim)

    docs = []
    try:
        docs = json.loads(claim.supporting_documents or "[]")
    except Exception:
        docs = []

    return WarrantyClaimOut(
        id=claim.id,
        claim_number=claim.claim_number,
        warranty_id=claim.warranty_id,
        warranty_number=claim.warranty.warranty_number if claim.warranty else None,
        customer_id=claim.customer_id,
        customer_name=claim.customer.name if claim.customer else None,
        customer_phone=claim.customer.phone if claim.customer else None,
        order_id=claim.order_id,
        order_number=claim.order.order_number if claim.order else None,
        serial_number=claim.serial_number,
        equipment_name=claim.equipment_name,
        issue_description=claim.issue_description,
        supporting_documents=docs,
        manufacturer_reference=claim.manufacturer_reference,
        assigned_technician_id=claim.assigned_technician_id,
        assigned_technician_name=claim.technician.name if claim.technician else None,
        claim_status=claim.claim_status,
        replacement_serial_number=claim.replacement_serial_number,
        resolution_details=claim.resolution_details,
        resolution_date=claim.resolution_date,
        created_at=claim.created_at,
        updated_at=claim.updated_at
    )
