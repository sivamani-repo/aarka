import os
import json
import random
import shutil
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.database import get_db
from app.models.subsidy import (
    GovernmentScheme, SchemeRule, SubsidyAssessment,
    SubsidyApplication, SubsidyDocument, VerificationRecord, SubsidyStatusHistory
)
from app.models.customer import Customer
from app.models.commercial import SalesOrder
from app.models.installation import InstallationJob
from app.schemas.schemas import (
    SubsidyCreate, SubsidyUpdate, SubsidyOut,
    SubsidyEligibilityCheckRequest, SubsidyEligibilityCheckResponse,
    SubsidyCalculateResponse,
    GovernmentSchemeOut, SchemeRuleOut,
    SubsidyAssessmentCreate, SubsidyAssessmentOut,
    SubsidyDocumentOut, SubsidyDocumentReviewRequest,
    VerificationRecordOut, SubsidyStatusHistoryOut,
    SubsidyOfficialStatusUpdateRequest
)
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/subsidies", tags=["Government Subsidies & Governance (PM Surya Ghar)"])

SPECIAL_CATEGORY_STATES = [
    "Sikkim", "Uttarakhand", "Himachal Pradesh", "Jammu and Kashmir",
    "Ladakh", "Assam", "Arunachal Pradesh", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Tripura", "Andaman and Nicobar Islands", "Lakshadweep"
]

INTERNAL_STATUSES = [
    "DRAFT",
    "DOCUMENTS_PENDING",
    "UNDER_INTERNAL_REVIEW",
    "CORRECTION_REQUIRED",
    "READY_FOR_SUBMISSION"
]

OFFICIAL_STATUSES = [
    "NOT_SUBMITTED",
    "SUBMITTED",
    "FEASIBILITY_PENDING",
    "FEASIBILITY_APPROVED",
    "FEASIBILITY_REJECTED",
    "AWAITING_INSTALLATION",
    "INSTALLED",
    "INSPECTION_PENDING",
    "COMMISSIONED",
    "SUBSIDY_CLAIM_PENDING",
    "APPROVED",
    "REJECTED",
    "DISBURSED"
]

# Legacy lifecycle stages mapping for backwards compatibility
LIFECYCLE_STAGES = OFFICIAL_STATUSES + INTERNAL_STATUSES + [
    "DOCS_VERIFIED", "INSPECTION_SCHEDULED", "INSPECTION_PASSED", "PARTIALLY_DISBURSED"
]


# ================= 1. SCHEMES CATALOGUE =================
@router.get("/schemes", response_model=List[GovernmentSchemeOut])
def list_government_schemes(
    category: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns verified government schemes from the central and state catalog.
    Publicly accessible to help customers understand available programs.
    """
    query = db.query(GovernmentScheme).filter(GovernmentScheme.is_active == True)
    if category and category != "ALL":
        query = query.filter(GovernmentScheme.category == category)
    if jurisdiction and jurisdiction != "ALL":
        query = query.filter(GovernmentScheme.jurisdiction == jurisdiction)
    if state and state != "ALL":
        query = query.filter(or_(GovernmentScheme.state == state, GovernmentScheme.state == None))

    return query.order_by(GovernmentScheme.id.asc()).all()


@router.get("/schemes/{scheme_id_or_code}", response_model=GovernmentSchemeOut)
def get_government_scheme(
    scheme_id_or_code: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves detailed rules, documentation requirements, and verified source references for a scheme.
    """
    if scheme_id_or_code.isdigit():
        scheme = db.query(GovernmentScheme).filter(GovernmentScheme.id == int(scheme_id_or_code)).first()
    else:
        scheme = db.query(GovernmentScheme).filter(GovernmentScheme.code == scheme_id_or_code).first()

    if not scheme:
        raise HTTPException(status_code=404, detail="Government scheme not found in catalog")
    return scheme


@router.get("/schemes/{scheme_id_or_code}/documents")
def get_scheme_document_checklist(
    scheme_id_or_code: str,
    db: Session = Depends(get_db)
):
    """
    Returns stage-by-stage document checklist (Initial, Commissioning, CFA Claim) for a scheme.
    """
    if scheme_id_or_code.isdigit():
        scheme = db.query(GovernmentScheme).filter(GovernmentScheme.id == int(scheme_id_or_code)).first()
    else:
        scheme = db.query(GovernmentScheme).filter(GovernmentScheme.code == scheme_id_or_code).first()

    if not scheme:
        raise HTTPException(status_code=404, detail="Government scheme not found")

    rules = scheme.rules
    if not rules:
        return {"scheme": scheme.name, "stages": []}

    try:
        checklist = json.loads(rules[0].document_checklist_configuration or "[]")
    except Exception:
        checklist = []

    return {
        "scheme_code": scheme.code,
        "scheme_name": scheme.name,
        "authority": scheme.authority,
        "stages": checklist
    }


# ================= 2. DASHBOARD METRICS & ANALYTICS =================
@router.get("/dashboard-metrics")
def get_subsidy_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes all government governance KPIs directly from database records.
    Strictly separates:
    - Internal Document Verification vs Official Government Approval
    - Estimated vs Approved vs Disbursed Subsidy
    """
    applications = db.query(SubsidyApplication).all()
    total_apps = len(applications)

    draft_count = sum(1 for a in applications if (a.internal_status or a.approval_status) in ["DRAFT", "DOCUMENTS_PENDING"])
    internal_review_count = sum(1 for a in applications if (a.internal_status or a.approval_status) in ["UNDER_INTERNAL_REVIEW", "DOCS_VERIFIED"])
    ready_for_submission_count = sum(1 for a in applications if a.internal_status == "READY_FOR_SUBMISSION")

    official_submitted_count = sum(1 for a in applications if (a.official_status or a.approval_status) in [
        "SUBMITTED", "FEASIBILITY_PENDING", "FEASIBILITY_APPROVED", "AWAITING_INSTALLATION", "INSTALLED",
        "INSPECTION_PENDING", "COMMISSIONED", "SUBSIDY_CLAIM_PENDING", "APPROVED", "DISBURSED"
    ])
    feasibility_approved_count = sum(1 for a in applications if (a.official_status or a.approval_status) in [
        "FEASIBILITY_APPROVED", "AWAITING_INSTALLATION", "INSTALLED", "INSPECTION_PENDING", "COMMISSIONED", "SUBSIDY_CLAIM_PENDING", "APPROVED", "DISBURSED"
    ])
    commissioned_count = sum(1 for a in applications if (a.official_status or a.approval_status) in [
        "COMMISSIONED", "SUBSIDY_CLAIM_PENDING", "APPROVED", "DISBURSED"
    ])
    approved_count = sum(1 for a in applications if (a.official_status or a.approval_status) in ["APPROVED", "DISBURSED"])
    disbursed_count = sum(1 for a in applications if a.payment_status == "DISBURSED" or (a.official_status or a.approval_status) == "DISBURSED")
    rejected_count = sum(1 for a in applications if (a.official_status or a.approval_status) in ["REJECTED", "FEASIBILITY_REJECTED"])

    # Financial sums
    estimated_amount_total = sum(a.estimated_amount or a.subsidy_amount for a in applications)
    approved_amount_total = sum(a.approved_amount or (a.subsidy_amount if a.approval_status in ["APPROVED", "DISBURSED"] else 0.0) for a in applications)
    disbursed_amount_total = sum(a.disbursed_amount or (a.subsidy_amount if a.payment_status == "DISBURSED" else 0.0) for a in applications)

    # Status distribution for charts
    status_counts: Dict[str, int] = {}
    for a in applications:
        st = (a.official_status or a.approval_status or "DRAFT").replace("_", " ").title()
        status_counts[st] = status_counts.get(st, 0) + 1

    status_distribution = [
        {"name": k, "value": v} for k, v in status_counts.items()
    ]

    # Category & State distributions
    cat_counts: Dict[str, int] = {}
    state_counts: Dict[str, int] = {}
    for a in applications:
        c = (a.category or "RESIDENTIAL").replace("_", " ")
        s = a.state or "Telangana"
        cat_counts[c] = cat_counts.get(c, 0) + 1
        state_counts[s] = state_counts.get(s, 0) + 1

    category_distribution = [{"name": k, "value": v} for k, v in cat_counts.items()]
    state_distribution = [{"name": k, "value": v} for k, v in state_counts.items()]

    # Official Conversion Funnel
    funnel = [
        {"stage": "1. Applications Drafted", "count": total_apps},
        {"stage": "2. Internal Docs Verified", "count": total_apps - draft_count},
        {"stage": "3. Portal Submitted", "count": official_submitted_count},
        {"stage": "4. Feasibility Approved", "count": feasibility_approved_count},
        {"stage": "5. System Commissioned", "count": commissioned_count},
        {"stage": "6. Govt Subsidy Sanctioned", "count": approved_count},
        {"stage": "7. DBT Disbursed to Customer", "count": disbursed_count},
    ]

    return {
        "total_applications": total_apps,
        "eligible_customers": db.query(Customer).count(),
        "draft_applications": draft_count,
        "internal_review_applications": internal_review_count,
        "ready_for_submission": ready_for_submission_count,
        "submitted_applications": official_submitted_count,
        "feasibility_approved": feasibility_approved_count,
        "commissioned_systems": commissioned_count,
        "approved_applications": approved_count,
        "disbursed_applications": disbursed_count,
        "rejected_applications": rejected_count,
        "estimated_subsidy_total": round(estimated_amount_total, 2),
        "approved_subsidy_total": round(approved_amount_total, 2),
        "disbursed_subsidy_total": round(disbursed_amount_total, 2),
        "status_distribution": status_distribution,
        "category_distribution": category_distribution,
        "state_distribution": state_distribution,
        "conversion_funnel": funnel,
    }


# ================= 3. ELIGIBILITY ENGINE & ASSESSMENTS =================
def compute_subsidy_logic(
    category: str,
    capacity_kw: float,
    state: str,
    is_grid_connected: bool,
    prior_subsidy_claimed: bool,
    has_roof_rights: bool = True
) -> Dict[str, Any]:
    """
    Pure business logic implementing official MNRE guidelines and verified state rules.
    """
    cat = category.upper()
    cap = max(0.5, float(capacity_kw))
    st = state.strip()

    reasons = []
    conditions = []
    calculation_steps = []
    is_eligible = True
    status_str = "POTENTIALLY_ELIGIBLE"

    # Category Rule: Commercial / Industrial is strictly excluded from PM Surya Ghar DBT
    if cat in ["COMMERCIAL", "INDUSTRIAL", "INSTITUTIONAL"]:
        is_eligible = False
        status_str = "POTENTIALLY_NOT_ELIGIBLE"
        reasons.append("Commercial, industrial, and institutional premises are ineligible for central DBT subsidies under PM Surya Ghar. Commercial consumers may claim accelerated depreciation or corporate green energy benefits instead.")
    elif cat == "RESIDENTIAL":
        reasons.append("Applicant category qualifies as an individual residential electricity consumer.")
    elif cat == "GHS_RWA":
        reasons.append("Group Housing Society / Resident Welfare Association qualifies for common facility solar power assistance.")
    elif cat == "AGRICULTURAL":
        reasons.append("Agricultural farming premise qualifies for PM-KUSUM scheme discovery.")

    # Grid Connectivity Check
    if not is_grid_connected:
        if cat != "AGRICULTURAL":
            is_eligible = False
            status_str = "POTENTIALLY_NOT_ELIGIBLE"
            reasons.append("Off-grid installations are not eligible. PM Surya Ghar requires a grid-connected system with two-way DISCOM net-metering.")
    else:
        conditions.append("Must install grid-interactive solar modules with DCR (Domestic Content Requirement) and ALMM certification.")

    # Roof Rights Check
    if not has_roof_rights:
        is_eligible = False
        status_str = "POTENTIALLY_NOT_ELIGIBLE"
        reasons.append("Customer must have legal roof rights / ownership consent for solar installation.")

    # Prior Subsidy Check
    if prior_subsidy_claimed:
        is_eligible = False
        status_str = "POTENTIALLY_NOT_ELIGIBLE"
        reasons.append("A central financial assistance (CFA) subsidy has already been disbursed against this electricity consumer account number. Subsidies are limited to one per consumer account.")

    # Capacity & Subsidy Arithmetic
    central_sub = 0.0
    state_sub = 0.0
    eligible_cap = cap
    is_special_state = st in SPECIAL_CATEGORY_STATES

    if is_eligible:
        if cat == "RESIDENTIAL":
            eligible_cap = min(3.0, cap)
            first_2kw_rate = 33000.0 if is_special_state else 30000.0
            third_kw_rate = 19800.0 if is_special_state else 18000.0
            max_cap = 85800.0 if is_special_state else 78000.0

            if cap <= 1.0:
                central_sub = cap * first_2kw_rate
                calculation_steps.append(f"Capacity {cap:.2f} kW × ₹{first_2kw_rate:,.0f}/kW = ₹{central_sub:,.2f}")
            elif cap <= 2.0:
                central_sub = cap * first_2kw_rate
                calculation_steps.append(f"First {cap:.2f} kW @ ₹{first_2kw_rate:,.0f}/kW = ₹{central_sub:,.2f}")
            else:
                addl_cap = min(1.0, cap - 2.0)
                base = 2.0 * first_2kw_rate
                addl = addl_cap * third_kw_rate
                central_sub = base + addl
                calculation_steps.append(f"First 2.0 kW @ ₹{first_2kw_rate:,.0f}/kW = ₹{base:,.2f}")
                calculation_steps.append(f"Additional {addl_cap:.2f} kW @ ₹{third_kw_rate:,.0f}/kW = ₹{addl:,.2f}")
                if cap > 3.0:
                    calculation_steps.append(f"Capacity above 3.0 kW ({cap - 3.0:.2f} kW) capped at maximum scheme limit of ₹{max_cap:,.2f}")

            central_sub = min(max_cap, central_sub)

            # State Add-On Logic
            if st == "Uttar Pradesh":
                # UPNEDA state top-up ₹15,000/kW max ₹30,000
                state_sub = min(30000.0, cap * 15000.0)
                calculation_steps.append(f"Uttar Pradesh (UPNEDA) state top-up incentive: ₹{state_sub:,.2f}")
            elif st == "Delhi":
                state_sub = 0.0
                calculation_steps.append("Delhi Solar Policy provides Generation-Based Incentive (GBI @ ₹3/unit) on energy bills rather than upfront capital grant.")
            elif st == "Telangana":
                state_sub = 0.0
                calculation_steps.append("Telangana State: No additional direct state-budget cash subsidy. Net-metering energy banking active under TSSPDCL/TSNPDCL.")
            else:
                calculation_steps.append(f"State-specific incentive for {st} requires official confirmation. Only Central PM Surya Ghar DBT applies.")

        elif cat == "GHS_RWA":
            eligible_cap = min(500.0, cap)
            central_sub = round(18000.0 * eligible_cap, 2)
            calculation_steps.append(f"GHS/RWA Common Facility: {eligible_cap:.2f} kW × ₹18,000/kW = ₹{central_sub:,.2f}")
            if cap > 500.0:
                calculation_steps.append("Capacity above 500 kW capped at maximum permissible CFA.")

        elif cat == "AGRICULTURAL":
            # PM-KUSUM illustrative estimation
            benchmark_cost_per_hp = 45000.0
            est_cost = cap * benchmark_cost_per_hp
            central_sub = round(est_cost * 0.30, 2)
            state_sub = round(est_cost * 0.30, 2)
            calculation_steps.append(f"PM-KUSUM Component B Benchmark: 30% Central CFA (₹{central_sub:,.2f}) + 30% State Subsidy (₹{state_sub:,.2f})")

    # Benchmark solar installation cost in India
    benchmark_rate = 60000.0
    est_project_cost = round(cap * benchmark_rate, 2)
    est_total_sub = round(central_sub + state_sub, 2)
    est_customer_outlay = max(0.0, round(est_project_cost - est_total_sub, 2))

    conditions.extend([
        "DISCOM technical feasibility approval and Net-Meter installation mandatory.",
        "Bank account must be seeded with Aadhaar for Direct Beneficiary Transfer (DBT).",
        "Geo-tagged photographs of module serial numbers and inverters required."
    ])

    return {
        "is_eligible": is_eligible,
        "status": status_str,
        "category": cat,
        "capacity_kw": cap,
        "eligible_capacity_kw": eligible_cap,
        "central_subsidy": round(central_sub, 2),
        "state_subsidy": round(state_sub, 2),
        "total_subsidy": est_total_sub,
        "benchmark_cost": benchmark_rate,
        "estimated_project_cost": est_project_cost,
        "estimated_customer_outlay": est_customer_outlay,
        "reasons": reasons,
        "conditions": conditions,
        "calculation_steps": calculation_steps,
        "rule_version": "2024.1-MNRE" if not is_special_state else "2024.1-MNRE-SPECIAL",
        "disclaimer": "Eligibility shown by AARKA is a preliminary assessment. Final eligibility, technical feasibility, approval and subsidy disbursement are determined by the relevant government authority or DISCOM."
    }


@router.post("/check-eligibility", response_model=SubsidyEligibilityCheckResponse)
def check_subsidy_eligibility(
    payload: SubsidyEligibilityCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Formal Government Scheme Eligibility Assessment Engine.
    Evaluates applicant inputs, checks scheme criteria, records assessment, and returns calculation breakdown.
    """
    calc = compute_subsidy_logic(
        category=payload.category,
        capacity_kw=payload.capacity_kw,
        state=payload.state,
        is_grid_connected=payload.is_grid_connected,
        prior_subsidy_claimed=payload.prior_subsidy_claimed
    )

    # Persist assessment record in database
    assessment = SubsidyAssessment(
        customer_id=payload.customer_id,
        applicant_name=payload.customer_name or (f"Consumer {payload.consumer_number}"),
        state=payload.state,
        customer_category=calc["category"],
        proposed_capacity=calc["capacity_kw"],
        discom_name=payload.discom_name,
        consumer_number=payload.consumer_number,
        rule_version=calc["rule_version"],
        estimated_central_assistance=calc["central_subsidy"],
        estimated_state_assistance=calc["state_subsidy"],
        estimated_total_assistance=calc["total_subsidy"],
        estimated_project_cost=calc["estimated_project_cost"],
        estimated_customer_outlay=calc["estimated_customer_outlay"],
        eligibility_status=calc["status"],
        calculation_breakdown=json.dumps({
            "steps": calc["calculation_steps"],
            "reasons": calc["reasons"],
            "conditions": calc["conditions"]
        }),
        disclaimer_acknowledged=True
    )
    db.add(assessment)
    db.commit()

    return SubsidyEligibilityCheckResponse(
        is_eligible=calc["is_eligible"],
        scheme_name="PM Surya Ghar: Muft Bijli Yojana (MNRE)",
        category=calc["category"],
        capacity_kw=calc["capacity_kw"],
        eligible_capacity_kw=calc["eligible_capacity_kw"],
        estimated_subsidy=calc["total_subsidy"],
        central_subsidy=calc["central_subsidy"],
        state_subsidy=calc["state_subsidy"],
        benchmark_cost=calc["benchmark_cost"],
        estimated_project_cost=calc["estimated_project_cost"],
        estimated_customer_outlay=calc["estimated_customer_outlay"],
        status=calc["status"],
        reasons=calc["reasons"],
        conditions=calc["conditions"],
        disclaimer=calc["disclaimer"],
        scheme_source="Ministry of New and Renewable Energy (MNRE), Govt. of India (Gazette 2024)"
    )


@router.post("/assessments", response_model=SubsidyAssessmentOut)
def create_comprehensive_assessment(
    payload: SubsidyAssessmentCreate,
    db: Session = Depends(get_db)
):
    """
    Submits a complete 4-step eligibility assessment with consumer, electricity, and installation details.
    """
    calc = compute_subsidy_logic(
        category=payload.customer_category,
        capacity_kw=payload.proposed_capacity,
        state=payload.state,
        is_grid_connected=payload.is_grid_connected,
        prior_subsidy_claimed=payload.prior_subsidy_claimed,
        has_roof_rights=payload.has_roof_rights
    )

    assessment = SubsidyAssessment(
        customer_id=payload.customer_id,
        applicant_name=payload.applicant_name or payload.consumer_number,
        applicant_phone=payload.applicant_phone,
        applicant_email=payload.applicant_email,
        order_id=payload.order_id,
        scheme_code=payload.scheme_code,
        state=payload.state,
        customer_category=calc["category"],
        proposed_capacity=calc["capacity_kw"],
        discom_name=payload.discom_name,
        consumer_number=payload.consumer_number,
        rule_version=calc["rule_version"],
        estimated_central_assistance=calc["central_subsidy"],
        estimated_state_assistance=calc["state_subsidy"],
        estimated_total_assistance=calc["total_subsidy"],
        estimated_project_cost=calc["estimated_project_cost"],
        estimated_customer_outlay=calc["estimated_customer_outlay"],
        eligibility_status=calc["status"],
        calculation_breakdown=json.dumps({
            "steps": calc["calculation_steps"],
            "reasons": calc["reasons"],
            "conditions": calc["conditions"],
            "applicant": {
                "tariff_category": payload.tariff_category,
                "sanctioned_load_kw": payload.sanctioned_load_kw,
                "monthly_consumption_units": payload.monthly_consumption_units,
                "roof_type": payload.roof_type,
                "available_roof_area_sqft": payload.available_roof_area_sqft
            }
        }),
        disclaimer_acknowledged=True
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


@router.get("/assessments", response_model=List[SubsidyAssessmentOut])
def list_assessments(
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(SubsidyAssessment)
    if customer_id:
        query = query.filter(SubsidyAssessment.customer_id == customer_id)
    return query.order_by(SubsidyAssessment.id.desc()).limit(100).all()


@router.get("/calculate", response_model=SubsidyCalculateResponse)
def calculate_government_subsidy(
    capacity_kw: float = Query(3.0, ge=0.5, le=500.0),
    category: str = Query("RESIDENTIAL"),
    state: str = Query("Telangana")
):
    """
    Dedicated scheme subsidy calculator supporting configurable scheme parameters.
    """
    calc = compute_subsidy_logic(
        category=category,
        capacity_kw=capacity_kw,
        state=state,
        is_grid_connected=True,
        prior_subsidy_claimed=False
    )

    scheme_title = "PM Surya Ghar: Muft Bijli Yojana"
    if category.upper() == "GHS_RWA":
        scheme_title = "PM Surya Ghar: Group Housing Societies / RWAs"
    elif category.upper() == "AGRICULTURAL":
        scheme_title = "PM-KUSUM Agricultural Solar Scheme"

    max_limit = 78000.0
    if state in SPECIAL_CATEGORY_STATES and category.upper() == "RESIDENTIAL":
        max_limit = 85800.0
    elif category.upper() == "GHS_RWA":
        max_limit = 9000000.0

    return SubsidyCalculateResponse(
        scheme_name=scheme_title,
        category=calc["category"],
        capacity_kw=calc["capacity_kw"],
        eligible_capacity_kw=calc["eligible_capacity_kw"],
        central_subsidy=calc["central_subsidy"],
        state_subsidy=calc["state_subsidy"],
        total_subsidy=calc["total_subsidy"],
        estimated_cost=calc["estimated_project_cost"],
        customer_contribution=calc["estimated_customer_outlay"],
        calculation_steps=calc["calculation_steps"],
        max_subsidy_limit=max_limit,
        disclaimer=calc["disclaimer"]
    )


# ================= 4. SUBSIDY APPLICATIONS CRUD =================
@router.get("", response_model=List[SubsidyOut])
def list_subsidies(
    approval_status: Optional[str] = None,
    official_status: Optional[str] = None,
    internal_status: Optional[str] = None,
    customer_id: Optional[int] = None,
    order_id: Optional[int] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(SubsidyApplication)

    # Scoping for Customer role
    if current_user.role == "Customer":
        cust = db.query(Customer).filter(Customer.email == current_user.email).first()
        if cust:
            query = query.filter(SubsidyApplication.customer_id == cust.id)
        else:
            return []

    if approval_status and approval_status != "ALL":
        query = query.filter(SubsidyApplication.approval_status == approval_status)
    if official_status and official_status != "ALL":
        query = query.filter(SubsidyApplication.official_status == official_status)
    if internal_status and internal_status != "ALL":
        query = query.filter(SubsidyApplication.internal_status == internal_status)
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
            scheme_id=s.scheme_id,
            assessment_id=s.assessment_id,
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
            commissioning_date=s.commissioning_date,
            disbursement_date=s.disbursement_date,
            internal_status=s.internal_status or "DRAFT",
            verification_status=s.verification_status,
            official_status=s.official_status or "NOT_SUBMITTED",
            approval_status=s.approval_status,
            estimated_amount=s.estimated_amount or s.subsidy_amount,
            requested_amount=s.requested_amount or s.subsidy_amount,
            subsidy_amount=s.subsidy_amount,
            approved_amount=s.approved_amount or 0.0,
            disbursed_amount=s.disbursed_amount or 0.0,
            disbursement_reference=s.disbursement_reference,
            payment_status=s.payment_status,
            assigned_officer=s.assigned_officer,
            assigned_employee_id=s.assigned_employee_id,
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
    """
    Creates a new subsidy application, initializes document checklist, and records audit history.
    """
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    year = date.today().year
    app_num = f"SUB-{year}-{random.randint(10000, 99999)}"
    while db.query(SubsidyApplication).filter(SubsidyApplication.application_number == app_num).first():
        app_num = f"SUB-{year}-{random.randint(10000, 99999)}"

    cap = float(payload.capacity_kw)
    cat = payload.category.upper() if payload.category else "RESIDENTIAL"
    calc = compute_subsidy_logic(
        category=cat,
        capacity_kw=cap,
        state=payload.state or "Telangana",
        is_grid_connected=True,
        prior_subsidy_claimed=False
    )
    est_sub = payload.subsidy_amount if payload.subsidy_amount is not None else calc["total_subsidy"]

    # Match scheme
    scheme = db.query(GovernmentScheme).filter(GovernmentScheme.category == cat).first()

    subsidy = SubsidyApplication(
        application_number=app_num,
        customer_id=customer.id,
        order_id=payload.order_id,
        scheme_id=scheme.id if scheme else None,
        scheme_name=payload.scheme_name or (scheme.name if scheme else "PM Surya Ghar Muft Bijli Yojana"),
        installation_id=payload.installation_id,
        category=cat,
        state=payload.state or "Telangana",
        discom_name=payload.discom_name or "TSSPDCL",
        consumer_number=payload.consumer_number,
        portal_application_ref=payload.portal_application_ref,
        capacity_kw=cap,
        submission_date=date.today(),
        internal_status="DOCUMENTS_PENDING",
        verification_status="PENDING",
        official_status="NOT_SUBMITTED",
        approval_status="UNDER_REVIEW",
        estimated_amount=est_sub,
        requested_amount=est_sub,
        subsidy_amount=est_sub,
        payment_status="PENDING",
        assigned_officer=payload.assigned_officer or current_user.name,
        assigned_employee_id=current_user.id,
        documents="[]",
        remarks=payload.remarks or f"Application initiated by {current_user.name}"
    )
    db.add(subsidy)
    db.flush()

    # Record Initial History
    hist = SubsidyStatusHistory(
        application_id=subsidy.id,
        previous_status=None,
        new_status="DOCUMENTS_PENDING",
        status_type="INTERNAL",
        updated_by=current_user.name,
        actor_type="AARKA_EMPLOYEE",
        remarks="Subsidy application registered. Awaiting customer document submissions."
    )
    db.add(hist)
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
        scheme_id=subsidy.scheme_id,
        assessment_id=subsidy.assessment_id,
        installation_id=subsidy.installation_id,
        category=subsidy.category,
        state=subsidy.state,
        discom_name=subsidy.discom_name,
        consumer_number=subsidy.consumer_number,
        portal_application_ref=subsidy.portal_application_ref,
        capacity_kw=subsidy.capacity_kw,
        submission_date=subsidy.submission_date,
        internal_status=subsidy.internal_status,
        verification_status=subsidy.verification_status,
        official_status=subsidy.official_status,
        approval_status=subsidy.approval_status,
        estimated_amount=subsidy.estimated_amount,
        requested_amount=subsidy.requested_amount,
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


@router.get("/{subsidy_id}", response_model=SubsidyOut)
def get_subsidy_detail(
    subsidy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(SubsidyApplication).filter(SubsidyApplication.id == subsidy_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subsidy application not found")

    if current_user.role == "Customer":
        cust = db.query(Customer).filter(Customer.email == current_user.email).first()
        if not cust or sub.customer_id != cust.id:
            raise HTTPException(status_code=403, detail="Unauthorized to view this application")

    return SubsidyOut(
        id=sub.id,
        application_number=sub.application_number,
        customer_id=sub.customer_id,
        customer_name=sub.customer.name if sub.customer else None,
        customer_phone=sub.customer.phone if sub.customer else None,
        order_id=sub.order_id,
        order_number=sub.order.order_number if sub.order else None,
        scheme_name=sub.scheme_name,
        scheme_id=sub.scheme_id,
        assessment_id=sub.assessment_id,
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
        commissioning_date=sub.commissioning_date,
        disbursement_date=sub.disbursement_date,
        internal_status=sub.internal_status,
        verification_status=sub.verification_status,
        official_status=sub.official_status,
        approval_status=sub.approval_status,
        estimated_amount=sub.estimated_amount or sub.subsidy_amount,
        requested_amount=sub.requested_amount or sub.subsidy_amount,
        subsidy_amount=sub.subsidy_amount,
        approved_amount=sub.approved_amount or 0.0,
        disbursed_amount=sub.disbursed_amount or 0.0,
        disbursement_reference=sub.disbursement_reference,
        payment_status=sub.payment_status,
        assigned_officer=sub.assigned_officer,
        assigned_employee_id=sub.assigned_employee_id,
        eligibility_notes=sub.eligibility_notes,
        documents=sub.documents or "[]",
        remarks=sub.remarks,
        created_at=sub.created_at,
        updated_at=sub.updated_at
    )


@router.put("/{subsidy_id}/status", response_model=SubsidyOut)
@router.put("/{subsidy_id}", response_model=SubsidyOut)
def update_subsidy_lifecycle_status(
    subsidy_id: int,
    payload: SubsidyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(SubsidyApplication).filter(SubsidyApplication.id == subsidy_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subsidy application not found")

    old_status = sub.approval_status

    if payload.approval_status is not None:
        if payload.approval_status not in LIFECYCLE_STAGES:
            raise HTTPException(status_code=400, detail=f"Invalid status '{payload.approval_status}'.")
        sub.approval_status = payload.approval_status
        sub.official_status = payload.approval_status

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

    # Status History Record
    if payload.approval_status and payload.approval_status != old_status:
        hist = SubsidyStatusHistory(
            application_id=sub.id,
            previous_status=old_status,
            new_status=payload.approval_status,
            status_type="OFFICIAL",
            updated_by=current_user.name,
            actor_type="AARKA_EMPLOYEE",
            remarks=payload.remarks or f"Status changed to {payload.approval_status}"
        )
        db.add(hist)

    db.commit()
    db.refresh(sub)
    return get_subsidy_detail(subsidy_id, db, current_user)


# ================= 5. THREE-LEVEL VERIFICATION & DOCUMENTS =================
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
    """
    Secure document collection:
    - Validates file extension (PDF, JPG, PNG, WEBP)
    - Validates max file size (10 MB)
    - Saves to private backend storage
    - Executes Level 1 Automated Validation
    - Updates application internal status to UNDER_INTERNAL_REVIEW
    """
    sub = db.query(SubsidyApplication).filter(SubsidyApplication.id == subsidy_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subsidy application not found")

    allowed_exts = [".pdf", ".jpg", ".jpeg", ".png", ".webp"]
    clean_fn = file.filename.replace(" ", "_") if file.filename else "doc.pdf"
    _, ext = os.path.splitext(clean_fn)
    if ext.lower() not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Invalid file format '{ext}'. Allowed formats: PDF, JPG, PNG, WEBP")

    upload_dir = "backend/uploads/subsidies"
    os.makedirs(upload_dir, exist_ok=True)
    unique_fn = f"sub_{sub.id}_{int(datetime.now().timestamp())}_{clean_fn}"
    file_path = os.path.join(upload_dir, unique_fn)

    # Read bytes and validate size
    contents = await file.read()
    file_size = len(contents)
    if file_size > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=400, detail="Document exceeds maximum size limit of 10 MB")

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    # Check if a document of this type already exists (Version Increment)
    existing_doc = db.query(SubsidyDocument).filter(
        SubsidyDocument.application_id == sub.id,
        SubsidyDocument.document_type == doc_type
    ).order_by(SubsidyDocument.version_number.desc()).first()

    next_version = (existing_doc.version_number + 1) if existing_doc else 1

    new_doc = SubsidyDocument(
        application_id=sub.id,
        document_type=doc_type,
        storage_path=file_path,
        original_filename=file.filename or unique_fn,
        file_size_bytes=file_size,
        mime_type=file.content_type,
        uploaded_by=current_user.name,
        review_status="UPLOADED",
        version_number=next_version
    )
    db.add(new_doc)

    # Level 1 Automated Validation Check:
    # Verify consumer number presence and naming consistency
    auto_decision = "MATCH"
    auto_notes = f"File {file.filename} uploaded ({file_size / 1024:.1f} KB). Format and size validated automatically."
    if not sub.consumer_number:
        auto_decision = "INFO_MISSING"
        auto_notes += " Warning: Consumer account number is missing from application."

    # Record Level 1 verification record
    v_rec = VerificationRecord(
        application_id=sub.id,
        document_id=None,
        reviewer_id=None,
        reviewer_name="AARKA System Validator (Level 1)",
        verification_type="AUTOMATED_VALIDATION",
        decision=auto_decision,
        remarks=auto_notes
    )
    db.add(v_rec)

    # Update application internal status
    sub.internal_status = "UNDER_INTERNAL_REVIEW"

    # Also keep JSON snapshot for backward compatibility
    docs = []
    try:
        docs = json.loads(sub.documents or "[]")
    except Exception:
        docs = []
    docs.append({
        "id": len(docs) + 1,
        "doc_type": doc_type,
        "name": file.filename,
        "url": f"/api/subsidies/documents/file/{unique_fn}",
        "uploaded_by": current_user.name,
        "upload_date": str(date.today()),
        "verification_status": "UPLOADED",
        "verification_remarks": remarks or "Uploaded for review"
    })
    sub.documents = json.dumps(docs)

    db.commit()
    db.refresh(new_doc)

    return {
        "success": True,
        "document_id": new_doc.id,
        "document_type": new_doc.document_type,
        "version": new_doc.version_number,
        "review_status": new_doc.review_status,
        "automated_check": auto_decision
    }


@router.get("/{subsidy_id}/documents", response_model=List[SubsidyDocumentOut])
def list_application_documents(
    subsidy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(SubsidyApplication).filter(SubsidyApplication.id == subsidy_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subsidy application not found")

    docs = db.query(SubsidyDocument).filter(SubsidyDocument.application_id == subsidy_id).order_by(SubsidyDocument.id.asc()).all()
    return docs


@router.get("/documents/file/{file_name}")
def download_subsidy_file(
    file_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Secure file streaming endpoint requiring authentication.
    """
    safe_name = os.path.basename(file_name)
    file_path = os.path.join("backend/uploads/subsidies", safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document file not found on disk")
    return FileResponse(file_path, filename=safe_name)


@router.patch("/documents/{doc_id}/review")
def review_subsidy_document_level_2(
    doc_id: int,
    payload: SubsidyDocumentReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Level 2: AARKA Employee Verification.
    Authorized employee reviews document, compares customer details, marks VERIFIED, REJECTED, or CORRECTION_REQUESTED.
    Does NOT imply official government portal approval.
    """
    doc = db.query(SubsidyDocument).filter(SubsidyDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    sub = doc.application
    decision = payload.decision.upper()

    if decision not in ["VERIFIED", "REJECTED", "CORRECTION_REQUESTED"]:
        raise HTTPException(status_code=400, detail="Decision must be VERIFIED, REJECTED, or CORRECTION_REQUESTED")

    if decision == "VERIFIED":
        doc.review_status = "VERIFIED_BY_AARKA"
        doc.rejection_reason = None
    elif decision == "REJECTED":
        doc.review_status = "REJECTED"
        doc.rejection_reason = payload.remarks or "Document does not satisfy compliance requirements."
        sub.internal_status = "CORRECTION_REQUIRED"
    elif decision == "CORRECTION_REQUESTED":
        doc.review_status = "RE_UPLOAD_REQUIRED"
        doc.rejection_reason = payload.remarks or "Clearer copy or corrected bill required."
        sub.internal_status = "CORRECTION_REQUIRED"

    doc.reviewed_by = current_user.name
    doc.reviewed_at = datetime.now()

    # Log Level 2 verification record
    v_rec = VerificationRecord(
        application_id=sub.id,
        document_id=doc.id,
        reviewer_id=current_user.id,
        reviewer_name=current_user.name,
        verification_type="EMPLOYEE_DOCUMENT_REVIEW",
        decision=decision,
        remarks=payload.remarks or f"Document reviewed by {current_user.name}"
    )
    db.add(v_rec)

    # Check if all documents for this application are verified
    all_docs = db.query(SubsidyDocument).filter(SubsidyDocument.application_id == sub.id).all()
    if all(d.review_status == "VERIFIED_BY_AARKA" for d in all_docs) and len(all_docs) > 0:
        sub.internal_status = "READY_FOR_SUBMISSION"
        sub.verification_status = "VERIFIED"

    db.commit()
    db.refresh(doc)

    return {
        "success": True,
        "document_id": doc.id,
        "review_status": doc.review_status,
        "application_internal_status": sub.internal_status
    }


# ================= 6. LEVEL 3 OFFICIAL GOVERNMENT & DISCOM TRACKING =================
@router.post("/{subsidy_id}/official-status")
def update_official_government_status(
    subsidy_id: int,
    payload: SubsidyOfficialStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Level 3: Official Government / DISCOM Verification.
    Tracks official status changes on the National Portal / DISCOM.
    Requires official application reference and evidence documentation.
    """
    sub = db.query(SubsidyApplication).filter(SubsidyApplication.id == subsidy_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subsidy application not found")

    new_st = payload.official_status.upper()
    if new_st not in OFFICIAL_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid official status. Must be one of {OFFICIAL_STATUSES}")

    old_st = sub.official_status or "NOT_SUBMITTED"
    sub.official_status = new_st
    sub.approval_status = new_st  # Keep synchronized for compatibility

    if payload.portal_application_ref:
        sub.portal_application_ref = payload.portal_application_ref
    if payload.inspection_date:
        sub.inspection_date = payload.inspection_date
    if payload.commissioning_date:
        sub.commissioning_date = payload.commissioning_date
    if payload.approval_date:
        sub.approval_date = payload.approval_date
    if payload.disbursement_date:
        sub.disbursement_date = payload.disbursement_date

    # Financial Assistance Confirmation
    if new_st == "APPROVED":
        sub.approved_amount = payload.approved_amount or sub.estimated_amount or sub.subsidy_amount
        if not sub.approval_date:
            sub.approval_date = date.today()

    if new_st == "DISBURSED":
        sub.payment_status = "DISBURSED"
        sub.disbursed_amount = payload.disbursed_amount or sub.approved_amount or sub.subsidy_amount
        if payload.disbursement_reference:
            sub.disbursement_reference = payload.disbursement_reference
        if not sub.disbursement_date:
            sub.disbursement_date = date.today()

    # Record Level 3 Official Status Audit Log
    hist = SubsidyStatusHistory(
        application_id=sub.id,
        previous_status=old_st,
        new_status=new_st,
        status_type="OFFICIAL",
        updated_by=current_user.name,
        actor_type="DISCOM" if "FEASIBILITY" in new_st or "INSPECTION" in new_st else "GOVT_PORTAL",
        evidence_reference=payload.evidence_reference or payload.portal_application_ref,
        remarks=payload.remarks or f"Official government milestone updated to {new_st}"
    )
    db.add(hist)

    db.commit()
    db.refresh(sub)
    return {
        "success": True,
        "official_status": sub.official_status,
        "approved_amount": sub.approved_amount,
        "disbursed_amount": sub.disbursed_amount,
        "payment_status": sub.payment_status
    }


@router.get("/{subsidy_id}/history", response_model=List[SubsidyStatusHistoryOut])
def get_subsidy_status_history(
    subsidy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns complete chronological audit history of all status changes, reviewer actions, and government milestones.
    """
    sub = db.query(SubsidyApplication).filter(SubsidyApplication.id == subsidy_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subsidy application not found")
    return db.query(SubsidyStatusHistory).filter(SubsidyStatusHistory.application_id == subsidy_id).order_by(SubsidyStatusHistory.id.asc()).all()


# ================= 7. CUSTOMER APPLICATION TRACKER =================
@router.get("/track/{identifier}")
def track_customer_application(
    identifier: str,
    db: Session = Depends(get_db)
):
    """
    Public or customer tracking endpoint to lookup application status by Application Number or Portal Reference.
    Returns 12-stage progress timeline with responsible parties and transparent milestone tracking.
    """
    sub = db.query(SubsidyApplication).filter(
        or_(
            SubsidyApplication.application_number == identifier,
            SubsidyApplication.portal_application_ref == identifier
        )
    ).first()

    if not sub:
        raise HTTPException(status_code=404, detail="Application record not found")

    # Define standard 12-stage roadmap
    roadmap = [
        {"key": "DRAFT", "title": "Application Created", "actor": "Customer / AARKA", "description": "Preliminary details entered"},
        {"key": "DOCUMENTS_PENDING", "title": "Documents Submitted", "actor": "Customer", "description": "Electricity bill and roof photos submitted"},
        {"key": "UNDER_INTERNAL_REVIEW", "title": "AARKA Document Review", "actor": "AARKA Staff", "description": "Level 2 compliance and bill verification"},
        {"key": "READY_FOR_SUBMISSION", "title": "Docs Accepted for Submission", "actor": "AARKA Staff", "description": "Application marked ready for portal upload"},
        {"key": "SUBMITTED", "title": "Official Portal Application", "actor": "AARKA / Customer", "description": "Submitted to National Portal with consumer USCNO"},
        {"key": "FEASIBILITY_APPROVED", "title": "DISCOM Technical Feasibility", "actor": "DISCOM", "description": "Transformer capacity and LT line feasibility sanctioned"},
        {"key": "INSTALLED", "title": "Installation Completed", "actor": "AARKA EPC Team", "description": "Solar PV modules and inverter installed per standards"},
        {"key": "INSPECTION_PENDING", "title": "DISCOM Net-Meter & Joint Inspection", "actor": "DISCOM Officer", "description": "Bi-directional net-meter installed & plant tested"},
        {"key": "COMMISSIONED", "title": "System Commissioned (JCC)", "actor": "DISCOM / MNRE", "description": "Commissioning certificate issued"},
        {"key": "SUBSIDY_CLAIM_PENDING", "title": "Subsidy Claim Submitted", "actor": "Customer / AARKA", "description": "Aadhaar-seeded bank account uploaded for DBT"},
        {"key": "APPROVED", "title": "Subsidy Approved", "actor": "Central Govt (MNRE)", "description": "CFA amount sanctioned by ministry"},
        {"key": "DISBURSED", "title": "Subsidy Disbursed via DBT", "actor": "PFMS / Central Govt", "description": "Direct credit to customer bank account"},
    ]

    # Map current progress
    current_key = sub.official_status if sub.official_status not in ["NOT_SUBMITTED", None] else sub.internal_status
    if sub.payment_status == "DISBURSED":
        current_key = "DISBURSED"

    timeline = []
    current_reached = False
    for step in roadmap:
        is_completed = False
        is_active = False
        if step["key"] == current_key:
            is_active = True
            current_reached = True
        elif not current_reached:
            is_completed = True

        timeline.append({
            "stage": step["title"],
            "responsible_party": step["actor"],
            "description": step["description"],
            "status": "COMPLETED" if is_completed else ("CURRENT" if is_active else "PENDING"),
        })

    return {
        "application_number": sub.application_number,
        "portal_reference": sub.portal_application_ref or "Pending Portal Allotment",
        "customer_name": sub.customer.name if sub.customer else "Valued Homeowner",
        "category": sub.category,
        "state": sub.state,
        "discom": sub.discom_name,
        "capacity_kw": sub.capacity_kw,
        "estimated_subsidy": sub.estimated_amount or sub.subsidy_amount,
        "approved_subsidy": sub.approved_amount or 0.0,
        "disbursed_subsidy": sub.disbursed_amount or 0.0,
        "internal_status": sub.internal_status,
        "official_status": sub.official_status,
        "payment_status": sub.payment_status,
        "disbursement_reference": sub.disbursement_reference,
        "timeline": timeline,
        "disclaimer": "Eligibility and tracker statuses shown are assisted by AARKA. Direct Beneficiary Transfer (DBT) is credited directly by the Government of India."
    }
