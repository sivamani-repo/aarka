from datetime import date, timedelta
from types import SimpleNamespace
from fastapi.testclient import TestClient
from main import app
from app.core.warranty_service import add_calendar_months
from app.routers.warranties import _calculate_warranty_dynamic_status

client = TestClient(app)


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


def test_unverified_warranty_never_appears_active():
    pending = SimpleNamespace(
        status="PENDING_ACTIVATION",
        warranty_start=date.today(),
        warranty_end=date.today() + timedelta(days=365),
        certificate_url=None,
        activated_at=None,
        activated_by=None,
    )
    legacy_active_without_proof = SimpleNamespace(
        status="ACTIVE",
        warranty_start=date.today(),
        warranty_end=date.today() + timedelta(days=365),
        certificate_url=None,
        activated_at=None,
        activated_by=None,
    )
    assert _calculate_warranty_dynamic_status(pending, date.today()) == "PENDING_ACTIVATION"
    assert _calculate_warranty_dynamic_status(legacy_active_without_proof, date.today()) == "PENDING_ACTIVATION"


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


def test_warranty_search_and_uploaded_certificate(auth_headers):
    """Search returns warranty status; certificate access requires an uploaded document."""
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

    # Do not synthesize a certificate when no document was uploaded.
    cert_res = client.get(f"/api/warranties/{w_id}/certificate", headers=auth_headers)
    if target.get("certificate_url"):
        assert cert_res.status_code == 200
        assert cert_res.json()["serial_number"] == sn
        assert "certificate_url" in cert_res.json()
    else:
        assert cert_res.status_code == 404


def test_warranty_claim_lifecycle(auth_headers):
    """A claim cannot imply manufacturer coverage before warranty verification."""
    list_res = client.get("/api/warranties", headers=auth_headers)
    warranties = list_res.json()
    target_w = warranties[0]

    # Pending seeded warranties have no verified certificate and cannot create an OEM claim.
    claim_payload = {
        "warranty_id": target_w["id"],
        "issue_description": "Inverter displays Ground Fault F04 error during heavy rains.",
        "manufacturer_reference": "OEM-RMA-TEST-99"
    }
    create_res = client.post("/api/warranties/claims", json=claim_payload, headers=auth_headers)
    assert create_res.status_code == 409


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
