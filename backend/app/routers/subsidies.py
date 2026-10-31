import os
import json
import random
import shutil
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.database import get_db
from app.models.subsidy import SubsidyApplication
from app.models.customer import Customer
from app.models.commercial import SalesOrder
from app.models.installation import InstallationJob
from app.schemas.schemas import (
    SubsidyCreate, SubsidyUpdate, SubsidyOut,
    SubsidyEligibilityCheckRequest, SubsidyEligibilityCheckResponse,
    SubsidyCalculateResponse
)
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/subsidies", tags=["Government Subsidies & Governance (PM Surya Ghar)"])

# Lifecycle stages for official government subsidy tracking
LIFECYCLE_STAGES = [
    "DRAFT",
    "DOCUMENTS_PENDING",
    "READY_FOR_SUBMISSION",
    "SUBMITTED",
    "UNDER_REVIEW",
    "APPROVED",
    "REJECTED",
    "AWAITING_INSTALLATION",
    "INSTALLED",
    "INSPECTION_PENDING",
    "COMMISSIONED",
    "DISBURSEMENT_PENDING",
    "PARTIALLY_DISBURSED",
    "DISBURSED"
]


# ================= DASHBOARD METRICS & ANALYTICS =================
@router.get("/dashboard-metrics")
def get_subsidy_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes all government governance KPIs directly from database records:
    Applications submitted, review, approved, rejected, amounts estimated/approved/disbursed, and conversion funnel.
    """
    applications = db.query(SubsidyApplication).all()
    total_apps = len(applications)

    submitted_count = sum(1 for a in applications if a.approval_status in ["SUBMITTED", "DOCS_VERIFIED"])
    under_review_count = sum(1 for a in applications if a.approval_status in ["UNDER_REVIEW", "INSPECTION_SCHEDULED", "INSPECTION_PENDING"])
    approved_count = sum(1 for a in applications if a.approval_status in ["APPROVED", "INSPECTION_PASSED", "COMMISSIONED"])
    disbursed_count = sum(1 for a in applications if a.payment_status == "DISBURSED" or a.approval_status == "DISBURSED")
    rejected_count = sum(1 for a in applications if a.approval_status == "REJECTED")
    pending_docs_count = sum(1 for a in applications if a.verification_status in ["PENDING", "DOCUMENTS_PENDING"])

    # Estimated, approved, and disbursed amounts
    estimated_amount_total = sum(a.subsidy_amount for a in applications)
    approved_amount_total = sum(a.approved_amount or (a.subsidy_amount if a.approval_status in ["APPROVED", "DISBURSED"] else 0.0) for a in applications)
    disbursed_amount_total = sum(a.disbursed_amount or (a.subsidy_amount if a.payment_status == "DISBURSED" else 0.0) for a in applications)
    awaiting_disbursement_count = sum(1 for a in applications if a.approval_status == "APPROVED" and a.payment_status != "DISBURSED")

    # Potential eligible customers count (residential customers with active quotations or orders)
    eligible_customers_count = db.query(Customer).count()

    # Status distribution for charts
    status_counts: Dict[str, int] = {}
    for a in applications:
        st = a.approval_status.replace("_", " ").title()
        status_counts[st] = status_counts.get(st, 0) + 1

    status_distribution = [
        {"name": k, "value": v} for k, v in status_counts.items()
    ]

    # Application conversion funnel
    funnel = [
        {"stage": "Applications Drafted", "count": total_apps},
        {"stage": "Portal Submitted", "count": total_apps - sum(1 for a in applications if a.approval_status in ["DRAFT", "DOCUMENTS_PENDING"])},
        {"stage": "Under Review / Inspection", "count": under_review_count + approved_count + disbursed_count},
        {"stage": "Approved by DISCOM", "count": approved_count + disbursed_count},
        {"stage": "DBT Disbursed", "count": disbursed_count},
    ]

    # Estimated vs Approved vs Disbursed summary
    amounts_summary = [
        {"metric": "Estimated Total", "amount": round(estimated_amount_total, 2)},
        {"metric": "Sanctioned / Approved", "amount": round(approved_amount_total, 2)},
        {"metric": "DBT Disbursed", "amount": round(disbursed_amount_total, 2)},
    ]

    return {
        "total_applications": total_apps,
        "eligible_customers": eligible_customers_count,
        "submitted_applications": submitted_count,
        "under_review_applications": under_review_count,
        "approved_applications": approved_count,
        "rejected_applications": rejected_count,
        "pending_documentation": pending_docs_count,
        "awaiting_disbursement": awaiting_disbursement_count,
        "estimated_subsidy_total": round(estimated_amount_total, 2),
        "approved_subsidy_total": round(approved_amount_total, 2),
        "disbursed_subsidy_total": round(disbursed_amount_total, 2),
        "status_distribution": status_distribution,
        "amounts_summary": amounts_summary,
        "conversion_funnel": funnel,
    }


# ================= ELIGIBILITY ENGINE & CALCULATOR =================
@router.post("/check-eligibility", response_model=SubsidyEligibilityCheckResponse)
def check_subsidy_eligibility(
    payload: SubsidyEligibilityCheckRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Formal Government Scheme Eligibility Assessment Engine:
    Validates applicant conditions under PM Surya Ghar: Muft Bijli Yojana rules:
    - Commercial / Industrial connections are strictly INELIGIBLE for residential DBT.
    - Grid connectivity & net-metering readiness is required.
    - Capacity tiers:
      - 1-2 kW: ₹30,000 / kW
      - 2-3 kW: Additional ₹18,000
      - Max Central Subsidy Cap: ₹78,000 for Residential households.
      - GHS / RWA common facilities: ₹18,000 / kW up to 500 kW.
    """
    reasons = []
    conditions = []
    is_eligible = True
    status_str = "ELIGIBLE"

    category = payload.category.upper()
    cap = max(0.5, float(payload.capacity_kw))

    # Condition 1: Consumer category check
    if category in ["COMMERCIAL", "INDUSTRIAL", "INSTITUTIONAL"]:
        is_eligible = False
        status_str = "INELIGIBLE"
        reasons.append("Commercial, industrial, and institutional premises are ineligible for central subsidy under the PM Surya Ghar residential rooftop solar scheme.")
    else:
        reasons.append("Customer falls under a qualified category (Residential / Group Housing Society).")

    # Condition 2: Grid-connectivity
    if not payload.is_grid_connected:
        is_eligible = False
        status_str = "INELIGIBLE"
        reasons.append("Off-grid installations are not eligible. PM Surya Ghar requires a grid-connected system with two-way DISCOM net-metering.")
    else:
        conditions.append("Must install grid-tied bifacial/mono PERC modules with ALMM and BIS certification.")

    # Condition 3: Prior claim check
    if payload.prior_subsidy_claimed:
        is_eligible = False
        status_str = "INELIGIBLE"
        reasons.append("A central financial assistance (CFA) subsidy has already been disbursed against this electricity consumer account number.")
    else:
        conditions.append("Electricity connection must be active with no outstanding DISCOM utility defaults.")

    # Calculation
    central_sub = 0.0
    state_sub = 0.0
    eligible_cap = cap

    if is_eligible:
        if category == "RESIDENTIAL":
            eligible_cap = min(3.0, cap)
            if cap <= 1.0:
                central_sub = 30000.0
            elif cap <= 2.0:
                central_sub = 30000.0 * min(2.0, cap)
            else:
                central_sub = 60000.0 + (18000.0 * min(1.0, cap - 2.0))
            central_sub = min(78000.0, central_sub)
        elif category == "GHS_RWA":
            # Group Housing Society / Resident Welfare Association common facilities
            eligible_cap = min(500.0, cap)
            central_sub = round(18000.0 * eligible_cap, 2)

    # Benchmark solar EPC project cost in India (~₹55,000 - ₹62,000 / kW)
    benchmark_cost = 60000.0
    est_project_cost = round(cap * benchmark_cost, 2)
    est_customer_outlay = max(0.0, round(est_project_cost - central_sub - state_sub, 2))

    conditions.extend([
        "DISCOM technical feasibility approval and Net-Meter installation required.",
        "Bank account linking with Aadhaar mandatory for direct beneficiary transfer (DBT).",
        "Installation photographs and geo-tagging required before commissioning."
    ])

    return SubsidyEligibilityCheckResponse(
        is_eligible=is_eligible,
        scheme_name="PM Surya Ghar: Muft Bijli Yojana (MNRE)",
        category=category,
        capacity_kw=cap,
        eligible_capacity_kw=eligible_cap,
        estimated_subsidy=round(central_sub + state_sub, 2),
        central_subsidy=round(central_sub, 2),
        state_subsidy=round(state_sub, 2),
        benchmark_cost=benchmark_cost,
        estimated_project_cost=est_project_cost,
        estimated_customer_outlay=est_customer_outlay,
        status=status_str,
        reasons=reasons,
        conditions=conditions,
        disclaimer="Estimated subsidy is calculated per MNRE guidelines. Final sanction and DBT disbursement are strictly determined by the National Portal and DISCOM verification.",
        scheme_source="Ministry of New and Renewable Energy (MNRE), Govt. of India (Gazette Notification 2024)"
    )


@router.get("/calculate", response_model=SubsidyCalculateResponse)
def calculate_government_subsidy(
    capacity_kw: float = Query(3.0, ge=0.5, le=500.0),
    category: str = Query("RESIDENTIAL"),
    state: str = Query("Telangana")
):
    """
    Dedicated scheme subsidy calculator supporting configurable scheme parameters.
    """
    cat = category.upper()
    cap = float(capacity_kw)
    steps = []
    central_sub = 0.0
    max_limit = 78000.0 if cat == "RESIDENTIAL" else 9000000.0

    if cat == "RESIDENTIAL":
        if cap < 1.0:
            central_sub = cap * 30000.0
            steps.append(f"Capacity {cap:.2f} kW × ₹30,000 = ₹{central_sub:,.2f}")
        elif cap <= 2.0:
            central_sub = cap * 30000.0
            steps.append(f"First {cap:.2f} kW @ ₹30,000/kW = ₹{central_sub:,.2f}")
        else:
            addl_cap = min(1.0, cap - 2.0)
            central_sub = 60000.0 + (addl_cap * 18000.0)
            steps.append("First 2.0 kW @ ₹30,000/kW = ₹60,000.00")
            steps.append(f"Additional {addl_cap:.2f} kW @ ₹18,000/kW = ₹{addl_cap * 18000.0:,.2f}")
            if cap > 3.0:
                steps.append(f"Capacity above 3.0 kW ({cap - 3.0:.2f} kW) capped at maximum central subsidy limit of ₹78,000.00")
        central_sub = min(78000.0, central_sub)
    elif cat == "GHS_RWA":
        eligible_cap = min(500.0, cap)
        central_sub = round(18000.0 * eligible_cap, 2)
        steps.append(f"Common facility capacity {eligible_cap:.2f} kW × ₹18,000/kW = ₹{central_sub:,.2f}")
        if cap > 500.0:
            steps.append("Capacity above 500 kW capped at maximum scheme allowance.")
    else:
        steps.append("Selected customer category is ineligible for central rooftop DBT subsidy.")

    benchmark = 60000.0
    cost = round(cap * benchmark, 2)
    contrib = max(0.0, round(cost - central_sub, 2))

    return SubsidyCalculateResponse(
        scheme_name="PM Surya Ghar: Muft Bijli Yojana",
        category=cat,
        capacity_kw=cap,
        eligible_capacity_kw=min(3.0 if cat == "RESIDENTIAL" else 500.0, cap),
        central_subsidy=round(central_sub, 2),
        state_subsidy=0.0,
        total_subsidy=round(central_sub, 2),
        estimated_cost=cost,
        customer_contribution=contrib,
        calculation_steps=steps,
        max_subsidy_limit=max_limit,
        disclaimer="Actual subsidy amount is sanctioned directly to the consumer's bank account (DBT) by the central government following installation, joint inspection, and DISCOM net-meter commissioning."
    )


# ================= SUBSIDY APPLICATIONS CRUD =================
@router.get("", response_model=List[SubsidyOut])
def list_subsidies(
    approval_status: Optional[str] = None,
    customer_id: Optional[int] = None,
    order_id: Optional[int] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(SubsidyApplication)
    if approval_status and approval_status != "ALL":
        query = query.filter(SubsidyApplication.approval_status == approval_status)
    if customer_id:
        query = query.filter(SubsidyApplication.customer_id == customer_id)
    if order_id:
        query = query.filter(SubsidyApplication.order_id == order_id)
    if category and category != "ALL":
        query = query.filter(SubsidyApplication.category == category)

    subsidies = query.order_by(SubsidyApplication.id.desc()).all()
    results = []

    for s in subsidies:
        if search:
            q = search.lower()
            c_name = s.customer.name.lower() if s.customer else ""
            app_num = s.application_number.lower()
            ref_num = s.portal_application_ref.lower() if s.portal_application_ref else ""
            cons_num = s.consumer_number.lower() if s.consumer_number else ""
            if q not in c_name and q not in app_num and q not in ref_num and q not in cons_num:
                continue

        results.append(SubsidyOut(
            id=s.id,
            application_number=s.application_number,
            customer_id=s.customer_id,
            customer_name=s.customer.name if s.customer else None,
            customer_phone=s.customer.phone if s.customer else None,
            order_id=s.order_id,
            order_number=s.order.order_number if s.order else None,
            scheme_name=s.scheme_name,
            installation_id=s.installation_id,
            category=s.category or "RESIDENTIAL",
            state=s.state or "Telangana",
            discom_name=s.discom_name or "TSSPDCL",
            consumer_number=s.consumer_number,
            portal_application_ref=s.portal_application_ref,
            capacity_kw=s.capacity_kw,
            submission_date=s.submission_date,
            inspection_date=s.inspection_date,
            approval_date=s.approval_date,
            disbursement_date=s.disbursement_date,
            verification_status=s.verification_status,
            approval_status=s.approval_status,
            subsidy_amount=s.subsidy_amount,
            approved_amount=s.approved_amount or 0.0,
            disbursed_amount=s.disbursed_amount or 0.0,
            disbursement_reference=s.disbursement_reference,
            payment_status=s.payment_status,
            assigned_officer=s.assigned_officer,
            eligibility_notes=s.eligibility_notes,
            documents=s.documents or "[]",
            remarks=s.remarks,
            created_at=s.created_at,
            updated_at=s.updated_at
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

    year = date.today().year
    app_num = f"SUB-{year}-{random.randint(10000, 99999)}"
    while db.query(SubsidyApplication).filter(SubsidyApplication.application_number == app_num).first():
        app_num = f"SUB-{year}-{random.randint(10000, 99999)}"

    # Default calculation for PM Surya Ghar
    cap = float(payload.capacity_kw)
    cat = payload.category.upper() if payload.category else "RESIDENTIAL"
    if cat == "RESIDENTIAL":
        if cap <= 1.0:
            calc_sub = 30000.0
        elif cap <= 2.0:
            calc_sub = 60000.0
        else:
            calc_sub = 78000.0
    elif cat == "GHS_RWA":
        calc_sub = round(18000.0 * min(500.0, cap), 2)
    else:
        calc_sub = 0.0

    subsidy = SubsidyApplication(
        application_number=app_num,
        customer_id=customer.id,
        order_id=payload.order_id,
        scheme_name=payload.scheme_name or "PM Surya Ghar Muft Bijli Yojana",
        installation_id=payload.installation_id,
        category=cat,
        state=payload.state or "Telangana",
        discom_name=payload.discom_name or "TSSPDCL",
        consumer_number=payload.consumer_number,
        portal_application_ref=payload.portal_application_ref or f"PMSG-{year}-{random.randint(10000, 99999)}",
        capacity_kw=cap,
        submission_date=date.today(),
        verification_status="PENDING",
        approval_status="UNDER_REVIEW",
        subsidy_amount=payload.subsidy_amount if payload.subsidy_amount is not None else calc_sub,
        payment_status="PENDING",
        assigned_officer=payload.assigned_officer or current_user.name,
        documents="[]",
        remarks=payload.remarks or f"National Portal application initiated by {current_user.name}"
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
        order_id=subsidy.order_id,
        scheme_name=subsidy.scheme_name,
        installation_id=subsidy.installation_id,
        category=subsidy.category,
        state=subsidy.state,
        discom_name=subsidy.discom_name,
        consumer_number=subsidy.consumer_number,
        portal_application_ref=subsidy.portal_application_ref,
        capacity_kw=subsidy.capacity_kw,
        submission_date=subsidy.submission_date,
        verification_status=subsidy.verification_status,
        approval_status=subsidy.approval_status,
        subsidy_amount=subsidy.subsidy_amount,
        approved_amount=subsidy.approved_amount or 0.0,
        disbursed_amount=subsidy.disbursed_amount or 0.0,
        payment_status=subsidy.payment_status,
        assigned_officer=subsidy.assigned_officer,
        documents=subsidy.documents or "[]",
        remarks=subsidy.remarks,
        created_at=subsidy.created_at,
        updated_at=subsidy.updated_at
    )


@router.put("/{subsidy_id}/status", response_model=SubsidyOut)
@router.put("/{subsidy_id}", response_model=SubsidyOut)
def update_subsidy_lifecycle_status(
    subsidy_id: int,
    payload: SubsidyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates the lifecycle stage of a Government Subsidy Application.
    Enforces that invalid transitions are rejected.
    """
    sub = db.query(SubsidyApplication).filter(SubsidyApplication.id == subsidy_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subsidy application not found")

    if payload.approval_status is not None:
        if payload.approval_status not in LIFECYCLE_STAGES:
            raise HTTPException(status_code=400, detail=f"Invalid status '{payload.approval_status}'. Must be one of {LIFECYCLE_STAGES}")
        sub.approval_status = payload.approval_status

        # Synchronize linked fields
        if payload.approval_status in ["DOCS_VERIFIED", "APPROVED", "DISBURSED", "INSPECTION_PASSED"]:
            sub.verification_status = "VERIFIED"
        if payload.approval_status == "APPROVED":
            if not sub.approval_date:
                sub.approval_date = payload.approval_date or date.today()
            if payload.approved_amount:
                sub.approved_amount = payload.approved_amount
            else:
                sub.approved_amount = sub.subsidy_amount
        if payload.approval_status == "DISBURSED":
            sub.payment_status = "DISBURSED"
            if not sub.disbursement_date:
                sub.disbursement_date = payload.disbursement_date or date.today()
            if payload.disbursed_amount:
                sub.disbursed_amount = payload.disbursed_amount
            else:
                sub.disbursed_amount = sub.approved_amount or sub.subsidy_amount

    if payload.verification_status is not None:
        sub.verification_status = payload.verification_status
    if payload.portal_application_ref is not None:
        sub.portal_application_ref = payload.portal_application_ref
    if payload.consumer_number is not None:
        sub.consumer_number = payload.consumer_number
    if payload.inspection_date is not None:
        sub.inspection_date = payload.inspection_date
    if payload.approval_date is not None:
        sub.approval_date = payload.approval_date
    if payload.disbursement_date is not None:
        sub.disbursement_date = payload.disbursement_date
    if payload.approved_amount is not None:
        sub.approved_amount = payload.approved_amount
    if payload.disbursed_amount is not None:
        sub.disbursed_amount = payload.disbursed_amount
    if payload.disbursement_reference is not None:
        sub.disbursement_reference = payload.disbursement_reference
    if payload.subsidy_amount is not None:
        sub.subsidy_amount = payload.subsidy_amount
    if payload.payment_status is not None:
        sub.payment_status = payload.payment_status
    if payload.assigned_officer is not None:
        sub.assigned_officer = payload.assigned_officer
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
        order_id=sub.order_id,
        scheme_name=sub.scheme_name,
        installation_id=sub.installation_id,
        category=sub.category,
        state=sub.state,
        discom_name=sub.discom_name,
        consumer_number=sub.consumer_number,
        portal_application_ref=sub.portal_application_ref,
        capacity_kw=sub.capacity_kw,
        submission_date=sub.submission_date,
        inspection_date=sub.inspection_date,
        approval_date=sub.approval_date,
        disbursement_date=sub.disbursement_date,
        verification_status=sub.verification_status,
        approval_status=sub.approval_status,
        subsidy_amount=sub.subsidy_amount,
        approved_amount=sub.approved_amount or 0.0,
        disbursed_amount=sub.disbursed_amount or 0.0,
        disbursement_reference=sub.disbursement_reference,
        payment_status=sub.payment_status,
        assigned_officer=sub.assigned_officer,
        eligibility_notes=sub.eligibility_notes,
        documents=sub.documents or "[]",
        remarks=sub.remarks,
        created_at=sub.created_at,
        updated_at=sub.updated_at
    )


# ================= DOCUMENT MANAGEMENT & VERIFICATION =================
@router.post("/{subsidy_id}/documents")
@router.post("/{subsidy_id}/upload-doc")
async def upload_subsidy_document(
    subsidy_id: int,
    file: UploadFile = File(...),
    doc_type: str = Form("ELECTRICITY_BILL"),
    remarks: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(SubsidyApplication).filter(SubsidyApplication.id == subsidy_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subsidy application not found")

    upload_dir = "backend/uploads/subsidies"
    os.makedirs(upload_dir, exist_ok=True)
    clean_fn = file.filename.replace(" ", "_") if file.filename else "doc.pdf"
    unique_fn = f"sub_{sub.id}_{int(datetime.now().timestamp())}_{clean_fn}"
    file_path = os.path.join(upload_dir, unique_fn)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    rel_url = f"/api/uploads/subsidies/{unique_fn}"

    docs = []
    try:
        docs = json.loads(sub.documents or "[]")
    except Exception:
        docs = []

    doc_entry = {
        "id": len(docs) + 1,
        "doc_type": doc_type,
        "name": file.filename,
        "url": rel_url,
        "uploaded_by": current_user.name,
        "upload_date": str(date.today()),
        "verification_status": "PENDING_VERIFICATION",
        "verified_by": None,
        "verification_remarks": remarks or "Uploaded for compliance verification"
    }
    docs.append(doc_entry)
    sub.documents = json.dumps(docs)
    db.commit()

    return {"success": True, "document": doc_entry, "all_documents": docs}


@router.put("/{subsidy_id}/documents/{doc_id}/verify")
def verify_subsidy_document(
    subsidy_id: int,
    doc_id: int,
    verification_status: str = Query(..., description="VERIFIED | REJECTED"),
    remarks: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(SubsidyApplication).filter(SubsidyApplication.id == subsidy_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subsidy application not found")

    docs = []
    try:
        docs = json.loads(sub.documents or "[]")
    except Exception:
        docs = []

    found = False
    for d in docs:
        if d.get("id") == doc_id:
            d["verification_status"] = verification_status
            d["verified_by"] = current_user.name
            d["verification_remarks"] = remarks or f"Marked {verification_status} by {current_user.name}"
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="Document with specified ID not found")

    # If all docs verified, update overall verification status
    all_verified = all(d.get("verification_status") == "VERIFIED" for d in docs)
    if all_verified and len(docs) > 0:
        sub.verification_status = "VERIFIED"

    sub.documents = json.dumps(docs)
    db.commit()

    return {"success": True, "documents": docs, "overall_verification": sub.verification_status}
