import io
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_government_schemes_catalogue():
    """Verify schemes catalog endpoint lists official central and state schemes."""
    res = client.get("/api/subsidies/schemes")
    assert res.status_code == 200
    schemes = res.json()
    assert len(schemes) >= 3

    codes = [s["code"] for s in schemes]
    assert "PM_SURYA_GHAR_RES" in codes
    assert "PM_SURYA_GHAR_GHS" in codes
    assert "PM_KUSUM_COMP_B" in codes

    # Check document checklist
    chk_res = client.get("/api/subsidies/schemes/PM_SURYA_GHAR_RES/documents")
    assert chk_res.status_code == 200
    chk_data = chk_res.json()
    assert len(chk_data["stages"]) >= 2


def test_subsidy_calculator_tiered_rates():
    """Verify official PM Surya Ghar tiered calculation arithmetic."""
    # 1 kW system
    c1 = client.get("/api/subsidies/calculate?capacity_kw=1.0&category=RESIDENTIAL&state=Telangana").json()
    assert c1["central_subsidy"] == 30000.0
    assert c1["total_subsidy"] == 30000.0

    # 2 kW system
    c2 = client.get("/api/subsidies/calculate?capacity_kw=2.0&category=RESIDENTIAL&state=Telangana").json()
    assert c2["central_subsidy"] == 60000.0
    assert c2["total_subsidy"] == 60000.0

    # 3 kW system (2 * 30k + 1 * 18k = 78k)
    c3 = client.get("/api/subsidies/calculate?capacity_kw=3.0&category=RESIDENTIAL&state=Telangana").json()
    assert c3["central_subsidy"] == 78000.0
    assert c3["total_subsidy"] == 78000.0

    # 5 kW system (Capped at 78k for general states)
    c5 = client.get("/api/subsidies/calculate?capacity_kw=5.0&category=RESIDENTIAL&state=Telangana").json()
    assert c5["central_subsidy"] == 78000.0

    # Special category state: Ladakh (3 kW = 2 * 33k + 19.8k = 85.8k)
    c_sp = client.get("/api/subsidies/calculate?capacity_kw=3.0&category=RESIDENTIAL&state=Ladakh").json()
    assert c_sp["central_subsidy"] == 85800.0

    # Group Housing Society: 50 kW @ 18k/kW = 9,00,000
    c_ghs = client.get("/api/subsidies/calculate?capacity_kw=50.0&category=GHS_RWA&state=Telangana").json()
    assert c_ghs["central_subsidy"] == 900000.0


def test_subsidy_eligibility_engine_rules():
    """Verify strict eligibility outcomes: Commercial excluded, Off-grid excluded, etc."""
    # Commercial consumer attempt -> Must be POTENTIALLY_NOT_ELIGIBLE
    res_comm = client.post("/api/subsidies/check-eligibility", json={
        "category": "COMMERCIAL",
        "state": "Telangana",
        "discom_name": "TSSPDCL",
        "consumer_number": "100234567",
        "capacity_kw": 10.0,
        "is_grid_connected": True,
        "prior_subsidy_claimed": False
    })
    assert res_comm.status_code == 200
    data_comm = res_comm.json()
    assert data_comm["is_eligible"] is False
    assert data_comm["status"] == "POTENTIALLY_NOT_ELIGIBLE"
    assert any("Commercial" in r for r in data_comm["reasons"])

    # Off-grid residential attempt -> Ineligible
    res_offgrid = client.post("/api/subsidies/check-eligibility", json={
        "category": "RESIDENTIAL",
        "state": "Telangana",
        "discom_name": "TSSPDCL",
        "consumer_number": "100234568",
        "capacity_kw": 3.0,
        "is_grid_connected": False,
        "prior_subsidy_claimed": False
    })
    assert res_offgrid.json()["is_eligible"] is False

    # Valid residential customer
    res_valid = client.post("/api/subsidies/check-eligibility", json={
        "category": "RESIDENTIAL",
        "state": "Telangana",
        "discom_name": "TSSPDCL",
        "consumer_number": "TS-USC-554433",
        "capacity_kw": 3.0,
        "is_grid_connected": True,
        "prior_subsidy_claimed": False
    })
    assert res_valid.json()["is_eligible"] is True
    assert res_valid.json()["estimated_subsidy"] == 78000.0


def test_subsidy_application_and_verification_lifecycle(auth_headers):
    """Test creating application, uploading documents (Level 1), employee review (Level 2), and official status (Level 3)."""
    # 1. Fetch customer
    custs = client.get("/api/customers", headers=auth_headers).json()
    cust_id = custs[0]["id"]

    # 2. Register application
    app_res = client.post("/api/subsidies", json={
        "customer_id": cust_id,
        "category": "RESIDENTIAL",
        "state": "Telangana",
        "discom_name": "TSSPDCL",
        "consumer_number": "USCNO-889977",
        "capacity_kw": 3.0
    }, headers=auth_headers)
    assert app_res.status_code == 200
    app_data = app_res.json()
    app_id = app_data["id"]
    app_num = app_data["application_number"]
    assert app_data["internal_status"] == "DOCUMENTS_PENDING"

    # 3. Document Upload (Level 1: System automated check)
    fake_bill = io.BytesIO(b"%PDF-1.4 Mock Electricity Bill TSSPDCL Content")
    up_res = client.post(
        f"/api/subsidies/{app_id}/documents",
        files={"file": ("tsspdcl_bill_sept.pdf", fake_bill, "application/pdf")},
        data={"doc_type": "ELECTRICITY_BILL"},
        headers=auth_headers
    )
    assert up_res.status_code == 200
    up_data = up_res.json()
    assert up_data["success"] is True
    doc_id = up_data["document_id"]
    assert up_data["automated_check"] == "MATCH"

    # Check that app status moved to UNDER_INTERNAL_REVIEW
    detail = client.get(f"/api/subsidies/{app_id}", headers=auth_headers).json()
    assert detail["internal_status"] == "UNDER_INTERNAL_REVIEW"

    # 4. Level 2: Employee Document Review
    rev_res = client.patch(
        f"/api/subsidies/documents/{doc_id}/review",
        json={"decision": "VERIFIED", "remarks": "Electricity bill verified with TSSPDCL USCNO."},
        headers=auth_headers
    )
    assert rev_res.status_code == 200
    assert rev_res.json()["review_status"] == "VERIFIED_BY_AARKA"

    # 5. Level 3: Official Government Status Update
    off_res = client.post(
        f"/api/subsidies/{app_id}/official-status",
        json={
            "official_status": "SUBMITTED",
            "portal_application_ref": f"PMSG-PORTAL-TEST-{app_id}",
            "evidence_reference": "PORTAL_ACK_RECEIPT_PDF",
            "remarks": "Application submitted on National Portal."
        },
        headers=auth_headers
    )
    assert off_res.status_code == 200
    assert off_res.json()["official_status"] == "SUBMITTED"

    # Progress to DISBURSED
    disb_res = client.post(
        f"/api/subsidies/{app_id}/official-status",
        json={
            "official_status": "DISBURSED",
            "disbursed_amount": 78000.0,
            "disbursement_reference": "PFMS-DBT-2026-998811",
            "remarks": "Subsidy credited directly to customer Aadhaar bank account."
        },
        headers=auth_headers
    )
    assert disb_res.status_code == 200
    assert disb_res.json()["payment_status"] == "DISBURSED"
    assert disb_res.json()["disbursed_amount"] == 78000.0

    # 6. Customer Timeline Tracker
    track_res = client.get(f"/api/subsidies/track/{app_num}")
    assert track_res.status_code == 200
    track_data = track_res.json()
    assert track_data["disbursed_subsidy"] == 78000.0
    assert len(track_data["timeline"]) == 12
    # Verify the final stage is marked completed
    final_stage = track_data["timeline"][-1]
    assert "Disbursed" in final_stage["stage"]
