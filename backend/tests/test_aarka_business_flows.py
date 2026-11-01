import pytest
import random
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.customer import Customer
from app.models.survey import SiteSurvey
from app.models.inventory import SerializedEquipment
from app.routers.dashboard import _dashboard_local_date, _dashboard_period_window

client = TestClient(app)


@pytest.fixture(scope="module")
def auth_headers():
    response = client.post("/api/auth/login", json={
        "email": "admin@aarka.com",
        "password": "admin123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_auth_and_profile(auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "admin@aarka.com"
    assert "Director" in data["role"] or "Admin" in data["role"]


def test_public_enquiry_and_lead_creation():
    payload = {
        "customer_name": "Kishore Kumar",
        "phone": "+91 99887 76655",
        "email": "kishore@gmail.com",
        "address": "House 14, Banjara Hills Road 12",
        "city": "Hyderabad",
        "customer_category": "Residential",
        "preferred_contact_method": "Phone",
        "lead_source": "Website",
        "required_capacity": 3.0,
        "solar_requirement": "On-Grid",
        "monthly_electricity_bill": 3200.0,
        "subsidy_requirement": True,
        "additional_requirements": "Looking for 3kW rooftop system under PM Surya Ghar"
    }
    res = client.post("/api/public/enquiry", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "LEAD-" in data["lead_reference"]
    assert data["required_capacity_kw"] == 3.0


def test_lead_qualification(auth_headers):
    # Fetch the newly created lead
    leads_res = client.get("/api/leads?search=Kishore", headers=auth_headers)
    assert leads_res.status_code == 200
    leads = leads_res.json()
    assert len(leads) > 0
    lead_id = leads[0]["id"]

    # Qualify lead
    qual_payload = {
        "shadow_free_roof_space": "550 sqft RCC Flat Roof",
        "monthly_electricity_bill": 3200.0,
        "grid_suitability": True,
        "customer_interest": "HIGH",
        "estimated_opportunity_value": 178000.0,
        "notes": "Verified electricity bill and south-facing terrace orientation."
    }
    res = client.post(f"/api/leads/{lead_id}/qualify", json=qual_payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["stage"] == "QUALIFIED"


def test_bom_calculation(auth_headers):
    res = client.get("/api/bom/calculate?package_type=On-Grid System&capacity_kw=3.0", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["capacity_kw"] == 3.0
    assert data["subtotal"] > 100000.0
    assert data["grand_total"] > data["subtotal"]
    assert len(data["components"]) > 0


def test_survey_schedule_and_approval_enforcement(auth_headers):
    # Find Kishore customer
    cust_res = client.get("/api/customers?search=Kishore", headers=auth_headers)
    cust_id = cust_res.json()[0]["id"]

    # Schedule survey
    survey_payload = {
        "customer_id": cust_id,
        "scheduled_date": "2026-11-02",
        "required_capacity_kw": 3.0,
        "observations": "Terrace inspection scheduled"
    }
    s_res = client.post("/api/surveys", json=survey_payload, headers=auth_headers)
    assert s_res.status_code == 200
    survey_id = s_res.json()["id"]

    # CRITICAL RULE #1: Try to create quotation with an unapproved survey - MUST FAIL!
    bad_quote = {
        "customer_id": cust_id,
        "survey_id": survey_id,
        "package_type": "On-Grid System",
        "capacity_kw": 3.0
    }
    fail_res = client.post("/api/quotations", json=bad_quote, headers=auth_headers)
    assert fail_res.status_code == 400
    assert "Business Rule Violation" in fail_res.json()["detail"]

    # Approve survey
    appr_res = client.post(f"/api/surveys/{survey_id}/approve", json={"action": "APPROVE"}, headers=auth_headers)
    assert appr_res.status_code == 200
    assert appr_res.json()["approval_status"] == "APPROVED"

    # Now create quotation with approved survey - MUST SUCCEED!
    quote_res = client.post("/api/quotations", json=bad_quote, headers=auth_headers)
    assert quote_res.status_code == 200
    q_data = quote_res.json()
    assert "QT-2026-" in q_data["quotation_number"]
    assert q_data["total_amount"] > 0
    assert q_data["advance_amount"] > 0


def test_order_creation_and_payment_validation(auth_headers):
    # Customer 1 has approved survey from seed data
    cust_res = client.get("/api/customers?search=Venkateswara", headers=auth_headers)
    cust_id = cust_res.json()[0]["id"]

    # Create quotation
    q_res = client.post("/api/quotations", json={
        "customer_id": cust_id,
        "package_type": "On-Grid System",
        "capacity_kw": 3.0
    }, headers=auth_headers)
    assert q_res.status_code == 200
    q_id = q_res.json()["id"]

    # Accept quotation -> creates order
    acc_res = client.post(f"/api/quotations/{q_id}/accept", headers=auth_headers)
    assert acc_res.status_code == 200
    order = acc_res.json()
    assert "SO-2026-" in order["order_number"]
    order_id = order["id"]
    total = order["total_amount"]

    # CRITICAL RULE #16: Payment cannot exceed payable amount!
    excess_res = client.post("/api/payments", json={
        "order_id": order_id,
        "customer_id": cust_id,
        "amount": total + 50000.0,
        "method": "Bank Transfer"
    }, headers=auth_headers)
    assert excess_res.status_code == 400
    assert "Business Rule Violation" in excess_res.json()["detail"]

    # Record legitimate advance payment (20%)
    adv_amount = round(total * 0.20, 2)
    pay_res = client.post("/api/payments", json={
        "order_id": order_id,
        "customer_id": cust_id,
        "amount": adv_amount,
        "method": "UPI",
        "reference": "UPI-DEMO-ADVANCE"
    }, headers=auth_headers)
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    assert pay_data["amount"] == adv_amount

    # Verify order updated
    ord_check = client.get(f"/api/orders/{order_id}", headers=auth_headers).json()
    assert ord_check["advance_paid"] == adv_amount
    assert ord_check["status"] == "READY_FOR_DISPATCH"


def test_duplicate_serial_prevention(auth_headers):
    # Get any product id requiring serial
    prods = client.get("/api/products?requires_serial=true", headers=auth_headers).json()
    prod_id = prods[0]["id"]

    # Register serial
    test_sn = "INV-TEST-UNIQUE-999"
    res1 = client.post("/api/serials", json={"product_id": prod_id, "serial_number": test_sn}, headers=auth_headers)
    assert res1.status_code in [200, 400]

    # Attempt to register the exact same serial again - MUST FAIL!
    res2 = client.post("/api/serials", json={"product_id": prod_id, "serial_number": test_sn}, headers=auth_headers)
    assert res2.status_code == 400
    assert "already registered" in res2.json()["detail"].lower()


def test_dispatch_and_automatic_warranty_activation(auth_headers):
    # Create fresh order for dispatch testing
    cust_res = client.get("/api/customers?search=Venkateswara", headers=auth_headers).json()
    cust_id = cust_res[0]["id"]
    q_res = client.post("/api/quotations", json={"customer_id": cust_id, "package_type": "On-Grid System", "capacity_kw": 3.0}, headers=auth_headers).json()
    order = client.post(f"/api/quotations/{q_res['id']}/accept", headers=auth_headers).json()
    order_id = order["id"]

    # Attempt dispatch without serial numbers - MUST FAIL (Rule #7)
    fail_disp = client.post("/api/dispatches", json={"order_id": order_id, "serial_numbers": []}, headers=auth_headers)
    assert fail_disp.status_code == 400

    # Find an available serial number or create one if exhausted
    avail_serials = client.get("/api/serials?status=AVAILABLE", headers=auth_headers).json()
    if not avail_serials:
        prods = client.get("/api/products?requires_serial=true", headers=auth_headers).json()
        prod_id = prods[0]["id"]
        sn_unique = f"INV-TEST-DISP-{random.randint(100000, 999999)}"
        client.post("/api/serials", json={"product_id": prod_id, "serial_number": sn_unique}, headers=auth_headers)
        avail_serials = client.get("/api/serials?status=AVAILABLE", headers=auth_headers).json()
    assert len(avail_serials) > 0, "No available serial found"
    active_sn = avail_serials[0]["serial_number"]

    # Dispatch with available serial
    disp_res = client.post("/api/dispatches", json={
        "order_id": order_id,
        "serial_numbers": [active_sn],
        "delivery_reference": f"DISP-TEST-{order_id}"
    }, headers=auth_headers)
    assert disp_res.status_code == 200
    disp_id = disp_res.json()["id"]

    # Confirm delivery -> Activates warranty (Rule #8 & #9)
    from datetime import date
    deliv_res = client.post(f"/api/dispatches/{disp_id}/confirm-delivery", json={
        "delivery_date": str(date.today()),
        "customer_confirmed": True
    }, headers=auth_headers)
    assert deliv_res.status_code == 200
    assert len(deliv_res.json()["activated_warranties"]) > 0

    # Search warranty for this serial
    war_search = client.get(f"/api/warranties/search?query={active_sn}", headers=auth_headers).json()
    assert war_search["count"] > 0
    assert war_search["results"][0]["status"] == "COVERED"


def test_service_ticket_and_warranty_coverage_evaluation(auth_headers):
    # Test with Dr. Sunita's active warranty inverter INV-3KW-8888
    cust_res = client.get("/api/customers?search=Sunita", headers=auth_headers).json()
    cust_id = cust_res[0]["id"]

    tkt_payload = {
        "customer_id": cust_id,
        "serial_number": "INV-3KW-8888",
        "fault_description": "Inverter DC surge alarm triggered during storm",
        "fault_code": "ERR-04",
        "priority": "HIGH"
    }
    tkt_res = client.post("/api/service/tickets", json=tkt_payload, headers=auth_headers)
    assert tkt_res.status_code == 200
    ticket = tkt_res.json()
    # CRITICAL RULE #10: Under covered warranty, customer charges MUST be 0!
    assert ticket["warranty_status"] == "COVERED"
    assert ticket["total_charges"] == 0.0
    assert ticket["labour_charges"] == 0.0
    assert ticket["parts_charges"] == 0.0


def test_project_profitability_and_finance(auth_headers):
    res = client.get("/api/finance/project-profitability", headers=auth_headers)
    assert res.status_code == 200
    projects = res.json()
    assert len(projects) > 0
    p = projects[0]
    assert "recognized_revenue" in p
    assert "total_cost" in p
    assert "gross_margin" in p
    # RECOGNIZED PROJECT REVENUE - RECORDED PROJECT COSTS = PROJECT PROFIT (Rule #15)
    assert round(p["recognized_revenue"] - p["total_cost"], 2) == round(p["gross_margin"], 2)


def test_dashboard_summary_metrics(auth_headers):
    res = client.get("/api/dashboard/summary?period=all", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["metrics"]["total_customers"] > 0
    assert data["metrics"]["total_enquiries"] > 0
    assert data["financials"]["total_revenue"] > 0
    assert len(data["charts"]["revenue_trend"]) > 0
    assert len(data["charts"]["funnel"]) > 0


def test_dashboard_period_filters(auth_headers):
    results = {}
    for period in ("today", "week", "month", "all"):
        response = client.get(f"/api/dashboard/summary?period={period}", headers=auth_headers)
        assert response.status_code == 200
        results[period] = response.json()
        assert results[period]["period"] == period

    all_customers = results["all"]["metrics"]["total_customers"]
    assert results["today"]["metrics"]["total_customers"] <= all_customers
    assert results["week"]["metrics"]["total_customers"] <= all_customers
    assert results["month"]["metrics"]["total_customers"] <= all_customers
    assert results["today"]["metrics"]["total_customers"] <= results["week"]["metrics"]["total_customers"]
    assert results["today"]["metrics"]["total_customers"] <= results["month"]["metrics"]["total_customers"]
    assert len(results["today"]["charts"]["revenue_trend"]) == 1
    for metric in (
        "pending_site_surveys",
        "active_installations",
        "open_service_tickets",
        "active_warranties",
        "pending_subsidies",
    ):
        assert results["today"]["metrics"][metric] == results["all"]["metrics"][metric]

    invalid_period = client.get("/api/dashboard/summary?period=last-year", headers=auth_headers)
    assert invalid_period.status_code == 422


def test_director_command_summary_uses_real_records_and_custom_dates(auth_headers):
    response = client.get(
        "/api/dashboard/director-summary?period=month",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "month"
    assert "recognized_revenue" in data["financials"]
    assert "pending_technician_payments" in data["financials"]
    assert "unfinished_installations" in data["operations"]
    assert isinstance(data["projects"], list)
    assert isinstance(data["alerts"], list)

    custom_response = client.get(
        "/api/dashboard/director-summary",
        params={
            "period": "custom",
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        },
        headers=auth_headers,
    )
    assert custom_response.status_code == 200
    assert custom_response.json()["date_start"] == "2026-10-01"
    assert custom_response.json()["date_end"] == "2026-10-31"

    missing_custom_dates = client.get(
        "/api/dashboard/director-summary?period=custom",
        headers=auth_headers,
    )
    assert missing_custom_dates.status_code == 422


def test_dashboard_periods_use_india_local_dates():
    now = datetime(2026, 11, 1, 0, 30, tzinfo=timezone.utc)
    record_created_at = datetime(2026, 10, 31, 18, 44, tzinfo=timezone.utc)

    today, start, end = _dashboard_period_window("today", now)
    assert str(today) == "2026-11-01"
    assert start <= record_created_at < end
    assert _dashboard_local_date(record_created_at) == today

    _, week_start, week_end = _dashboard_period_window("week", now)
    _, month_start, month_end = _dashboard_period_window("month", now)
    assert week_start <= record_created_at < week_end
    assert month_start <= record_created_at < month_end
    assert _dashboard_period_window("all", now) == (today, None, None)


def test_technician_category_can_be_created_and_updated(auth_headers):
    suffix = random.randint(100000, 999999)
    response = client.post(
        "/api/technicians",
        headers=auth_headers,
        json={
            "name": f"Category Test Technician {suffix}",
            "phone": f"90000{suffix}",
            "category": "Junior Technician",
        },
    )
    assert response.status_code == 200
    technician = response.json()
    assert technician["category"] == "Junior Technician"

    updated = client.patch(
        f"/api/technicians/{technician['id']}",
        headers=auth_headers,
        json={"category": "Supervisor"},
    )
    assert updated.status_code == 200
    assert updated.json()["category"] == "Supervisor"

    invalid = client.patch(
        f"/api/technicians/{technician['id']}",
        headers=auth_headers,
        json={"category": "Customer"},
    )
    assert invalid.status_code == 422
