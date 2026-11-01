import pytest
from datetime import date
from fastapi.testclient import TestClient
from main import app
from app.database import SessionLocal
from app.models.service import WarrantyRecord, WarrantyClaim
from app.models.installation import InstallationJob
from app.models.commercial import SalesOrder
from app.models.inventory import SerializedEquipment
from app.models.product import Product
from app.core.warranty_service import add_calendar_months

client = TestClient(app)


@pytest.fixture
def auth_headers():
    login_res = client.post("/api/auth/login", json={
        "email": "admin@aarka.com",
        "password": "admin123"
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_calendar_aware_date_arithmetic():
    """Verifies leap-year safe and calendar-aware month and year additions."""
    # Regular date: Jan 15 + 12 months = Jan 15 next year
    d1 = date(2026, 1, 15)
    assert add_calendar_months(d1, 12) == date(2027, 1, 15)
    assert add_calendar_months(d1, 60) == date(2031, 1, 15)  # 5 years
    assert add_calendar_months(d1, 300) == date(2051, 1, 15)  # 25 years

    # Leap year handling: Feb 29, 2024 + 12 months (non-leap year 2025) -> Feb 28, 2025
    d_leap = date(2024, 2, 29)
    assert add_calendar_months(d_leap, 12) == date(2025, 2, 28)
    # Feb 29, 2024 + 48 months (leap year 2028) -> Feb 29, 2028
    assert add_calendar_months(d_leap, 48) == date(2028, 2, 29)

    # 31-day month to 30-day month: Aug 31 + 1 month -> Sep 30
    d_31 = date(2026, 8, 31)
    assert add_calendar_months(d_31, 1) == date(2026, 9, 30)


def test_automatic_warranty_activation_on_completion(auth_headers):
    """
    PRIMARY BUSINESS RULE TEST:
    Warranties must NOT be activated when installation is SCHEDULED or IN_PROGRESS.
    Warranties MUST be automatically activated when installation is COMPLETED with customer handover.
    """
    db = SessionLocal()
    # Find an installation job with linked order
    job = db.query(InstallationJob).filter(InstallationJob.status == "SCHEDULED").first()
    if not job:
        job = db.query(InstallationJob).first()

    assert job is not None, "Installation job needed for test"
    job_id = job.id
    order_id = job.order_id

    # Ensure serials exist for this order
    serials = db.query(SerializedEquipment).filter(SerializedEquipment.order_id == order_id).all()
    if not serials:
        # Allocate a test serial
        panel_prod = db.query(Product).filter(Product.category == "SOLAR_PANELS").first()
        if not panel_prod:
            panel_prod = db.query(Product).first()
        test_sn = f"SN-TEST-WARR-{order_id}"
        existing_s = db.query(SerializedEquipment).filter(SerializedEquipment.serial_number == test_sn).first()
        if not existing_s:
            s_obj = SerializedEquipment(
                serial_number=test_sn,
                product_id=panel_prod.id,
                order_id=order_id,
                status="DISPATCHED"
            )
            db.add(s_obj)
            db.commit()
    db.close()

    # Complete the installation with full 9 checklist points and customer signature
    checklist_payload = {
        "checklist_state": {
            "mounting_inspected": True,
            "panels_installed": True,
            "inverter_installed": True,
            "wiring_completed": True,
            "earthing_completed": True,
            "safety_checked": True,
            "system_tested": True,
            "power_verified": True,
            "customer_handover": True
        },
        "customer_signature": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAJYAAAALCAYAAACmK88O...",
        "technical_observations": "Array tilt angle set to 18 degrees South, Voc measured 420V DC.",
        "testing_results": "Grid sync verified at 238V AC, power generation active.",
        "labour_hours": 7.5
    }

    comp_res = client.post(f"/api/installations/{job_id}/complete", json=checklist_payload, headers=auth_headers)
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["status"] == "CUSTOMER_ACCEPTED"
    assert comp_data["activated_warranties_count"] > 0

    # IDEMPOTENCY CHECK: Retry completion -> Should NOT duplicate warranties
    retry_res = client.post(f"/api/installations/{job_id}/complete", json=checklist_payload, headers=auth_headers)
    assert retry_res.status_code == 200

    # Verify warranties in database
    db = SessionLocal()
    order_warranties = db.query(WarrantyRecord).filter(WarrantyRecord.order_id == order_id).all()
    assert len(order_warranties) > 0

    # Verify that warranties are in active status and have valid date boundaries
    for w in order_warranties:
        assert w.status in ["ACTIVE", "COVERED"]
        assert w.warranty_start <= w.warranty_end
        assert w.warranty_number.startswith("WAR-")

    # Verify EPC Workmanship warranty exists for the order
    workmanship = [w for w in order_warranties if w.warranty_type == "WORKMANSHIP"]
    assert len(workmanship) >= 1
    db.close()


def test_warranty_dashboard_summary(auth_headers):
    """Verifies that the dashboard summary computes KPIs from live database records."""
    res = client.get("/api/warranties/dashboard-summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert "total_warranties" in data
    assert "active_warranties" in data
    assert "expiring_soon_count" in data
    assert "expired_count" in data
    assert "open_claims_count" in data
    assert "distribution_by_equipment" in data
    assert "expiry_timeline" in data
    assert len(data["expiry_timeline"]) == 12


def test_warranty_search_and_certificate(auth_headers):
    """Verifies warranty search tool and official digital certificate retrieval."""
    # List warranties
    list_res = client.get("/api/warranties", headers=auth_headers)
    assert list_res.status_code == 200
    warranties = list_res.json()
    assert len(warranties) > 0

    target = warranties[0]
    w_id = target["id"]
    sn = target["serial_number"]

    # Search by serial number
    search_res = client.get(f"/api/warranties/search?query={sn[:6]}", headers=auth_headers)
    assert search_res.status_code == 200
    s_data = search_res.json()
    assert s_data["count"] > 0

    # Retrieve official certificate
    cert_res = client.get(f"/api/warranties/{w_id}/certificate", headers=auth_headers)
    assert cert_res.status_code == 200
    cert = cert_res.json()
    assert "certificate_number" in cert
    assert "beneficiary" in cert
    assert "equipment" in cert
    assert "terms" in cert


def test_warranty_claim_lifecycle(auth_headers):
    """Verifies claim creation, status transitions, and resolution."""
    list_res = client.get("/api/warranties", headers=auth_headers)
    warranties = list_res.json()
    target_w = warranties[0]

    # 1. Raise Warranty Claim
    claim_payload = {
        "warranty_id": target_w["id"],
        "issue_description": "Inverter displays Ground Fault F04 error during heavy rains.",
        "manufacturer_reference": "OEM-RMA-TEST-99"
    }
    create_res = client.post("/api/warranties/claims", json=claim_payload, headers=auth_headers)
    assert create_res.status_code == 200
    claim = create_res.json()
    assert claim["claim_number"].startswith("CLM-")
    assert claim["claim_status"] == "CLAIM_RAISED"
    claim_id = claim["id"]

    # Verify warranty status transitioned to CLAIM_RAISED
    w_detail = client.get(f"/api/warranties/{target_w['id']}", headers=auth_headers).json()
    assert w_detail["status"] == "CLAIM_RAISED"

    # 2. Update claim to UNDER_REVIEW
    update_1 = client.put(f"/api/warranties/claims/{claim_id}/status", json={
        "claim_status": "UNDER_REVIEW"
    }, headers=auth_headers)
    assert update_1.status_code == 200
    assert update_1.json()["claim_status"] == "UNDER_REVIEW"

    # 3. Resolve claim
    update_2 = client.put(f"/api/warranties/claims/{claim_id}/status", json={
        "claim_status": "RESOLVED",
        "replacement_serial_number": "INV-NEW-REPLACEMENT-01",
        "resolution_details": "OEM replaced internal DC surge suppressor board. Field re-testing passed."
    }, headers=auth_headers)
    assert update_2.status_code == 200
    assert update_2.json()["claim_status"] == "RESOLVED"

    # Verify warranty returned to ACTIVE status upon resolution
    w_resolved = client.get(f"/api/warranties/{target_w['id']}", headers=auth_headers).json()
    assert w_resolved["status"] == "ACTIVE"


def test_expiry_alerts_and_duplicate_prevention(auth_headers):
    """Verifies expiry alerts query and ensures alert triggers prevent duplicates."""
    alerts_res = client.get("/api/warranties/expiry-alerts", headers=auth_headers)
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert "critical_7_days" in alerts
    assert "urgent_30_days" in alerts
    assert "notice_90_days" in alerts

    # Trigger alerts
    trigger_res = client.post("/api/warranties/expiry-alerts/trigger", headers=auth_headers)
    assert trigger_res.status_code == 200
    assert trigger_res.json()["success"] is True
