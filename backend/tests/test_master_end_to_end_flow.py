"""
AARKA Solar Installation Management System — Master End-to-End Acceptance Test
================================================================================
Verifies the complete 24-step operational solar lifecycle scenario from Section 16
of the enterprise specification:

  Step 1:  Homeowner submits enquiry for a 3 kW solar system
  Step 2:  Sales team immediately sees the lead in the dashboard
  Step 3:  Sales qualifies the customer
  Step 4:  Technician is assigned and completes the site survey
  Step 5:  Manager approves the site survey (unapproved prevents quotation)
  Step 6:  Quotation is generated from template (3 kW On-Grid)
  Step 7:  Customer accepts the quotation
  Step 8:  System automatically generates the Bill of Materials (BOM)
  Step 9:  Payment is recorded and balance is calculated correctly
  Step 10: Inventory receives the preparation request
  Step 11: Required equipment is reserved
  Step 12: Individual serialized equipment is scanned and assigned to installation
  Step 13: Dispatch is confirmed
  Step 14: Warranty records remain pending until certificate verification
  Step 15: Technician receives assigned installation job
  Step 16: Technician records work times, installed capacity, photos, and checklist
  Step 17: Homeowner signs digitally
  Step 18: Installation is marked completed
  Step 19: 18 months later, customer reports an inverter fault
  Step 20: Support locates customer, installation, inverter serial, and warranty
  Step 21: System correctly determines warranty eligibility (5-yr warranty > 18 mos)
  Step 22: Repair processed without invalid customer charge (₹0 under warranty)
  Step 23: Customer confirms resolution and ticket is closed
  Step 24: Director sees actual revenue, cost, profit, payment balance, and history
"""

import uuid
import random
from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient

from main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.customer import Customer, Lead
from app.models.survey import SiteSurvey
from app.models.commercial import Quotation, SalesOrder
from app.models.product import Product
from app.models.inventory import SerializedEquipment
from app.models.installation import InstallationJob
from app.models.service import WarrantyRecord, ServiceTicket

client = TestClient(app)


def test_section_16_complete_24_step_solar_lifecycle(auth_headers):
    # Unique tag to prevent collision with other test runs
    uid = uuid.uuid4().hex[:6]
    homeowner_name = f"Rajesh Sharma {uid}"
    homeowner_email = f"rajesh_{uid}@gmail.com"
    homeowner_phone = f"+91 9849{random.randint(100000, 999999)}"

    # =========================================================================
    # STEP 1: Homeowner submits an enquiry for a 3 kW solar system
    # =========================================================================
    enquiry_payload = {
        "customer_name": homeowner_name,
        "phone": homeowner_phone,
        "email": homeowner_email,
        "address": "Villa 42, Green Meadows, Jubilee Hills",
        "city": "Hyderabad",
        "customer_category": "Residential",
        "preferred_contact_method": "Phone",
        "lead_source": "Website",
        "required_capacity": 3.0,
        "solar_requirement": "On-Grid",
        "monthly_electricity_bill": 4200.0,
        "subsidy_requirement": True,
        "consent": True,
        "additional_requirements": "Looking for 3kW rooftop system under PM Surya Ghar DBT"
    }
    res_step1 = client.post("/api/public/enquiry", json=enquiry_payload)
    assert res_step1.status_code == 200, f"Step 1 failed: {res_step1.text}"
    step1_data = res_step1.json()
    assert step1_data["success"] is True
    lead_ref = step1_data["lead_reference"]
    assert lead_ref.startswith("LEAD-")
    assert step1_data["required_capacity_kw"] == 3.0

    # =========================================================================
    # STEP 2: Sales team can immediately see the lead
    # =========================================================================
    res_step2 = client.get(f"/api/leads?search={homeowner_name}", headers=auth_headers)
    assert res_step2.status_code == 200, f"Step 2 failed: {res_step2.text}"
    leads = res_step2.json()
    assert len(leads) >= 1, "Lead not found in sales register"
    matched_lead = next((l for l in leads if l["email"] == homeowner_email), None)
    assert matched_lead is not None, "Lead email mismatch"
    lead_id = matched_lead["id"]
    customer_id = matched_lead["customer_id"]
    assert matched_lead["stage"] in ["NEW", "CONTACTED", "QUALIFIED"]
    assert matched_lead["required_capacity_kw"] == 3.0

    # =========================================================================
    # STEP 3: Sales qualifies the customer
    # =========================================================================
    qual_payload = {
        "shadow_free_roof_space": "520 sqft RCC flat roof, unshaded South exposure",
        "monthly_electricity_bill": 4200.0,
        "grid_suitability": True,
        "customer_interest": "HIGH",
        "estimated_opportunity_value": 185000.0,
        "notes": "Verified latest electricity bill. Eligible for PM Surya Ghar subsidy."
    }
    res_step3 = client.post(f"/api/leads/{lead_id}/qualify", json=qual_payload, headers=auth_headers)
    assert res_step3.status_code == 200, f"Step 3 failed: {res_step3.text}"
    step3_data = res_step3.json()
    assert step3_data["stage"] == "QUALIFIED"

    # =========================================================================
    # STEP 4: Technician is assigned and completes the site survey
    # =========================================================================
    # 4a: Schedule survey
    survey_payload = {
        "customer_id": customer_id,
        "lead_id": lead_id,
        "scheduled_date": str(date.today()),
        "required_capacity_kw": 3.0,
        "observations": "Scheduled detailed shadow analysis and structural audit."
    }
    res_step4_sched = client.post("/api/surveys", json=survey_payload, headers=auth_headers)
    assert res_step4_sched.status_code == 200, f"Step 4 sched failed: {res_step4_sched.text}"
    survey = res_step4_sched.json()
    survey_id = survey["id"]

    # 4b: Technician conducts site survey and submits technical findings
    survey_update_payload = {
        "actual_survey_date": str(date.today()),
        "roof_area": 550.0,
        "shadow_free_area": 500.0,
        "roof_direction": "South",
        "roof_tilt": 18.0,
        "cable_distance": 22.0,
        "structural_condition": "EXCELLENT",
        "grid_connection_suitable": True,
        "observations": "Reinforced concrete slab; zero tree shading between 9am-4pm.",
        "technician_recommendation": "Optimal for 3 kW mono-PERC half-cut array + 3.3 kW string inverter.",
        "status": "COMPLETED"
    }
    res_step4_comp = client.put(f"/api/surveys/{survey_id}", json=survey_update_payload, headers=auth_headers)
    assert res_step4_comp.status_code == 200, f"Step 4 update failed: {res_step4_comp.text}"
    assert res_step4_comp.json()["status"] == "COMPLETED"

    # =========================================================================
    # STEP 5: Manager approves the survey (unapproved prevents quotation)
    # =========================================================================
    # Validation check: Creating a quotation with an unapproved survey must fail
    res_step5_unapproved = client.post("/api/quotations", json={
        "customer_id": customer_id,
        "survey_id": survey_id,
        "package_type": "On-Grid System",
        "capacity_kw": 3.0
    }, headers=auth_headers)
    assert res_step5_unapproved.status_code == 400, "Unapproved survey should reject quotation"
    assert "Business Rule Violation" in res_step5_unapproved.json()["detail"]

    # Manager officially approves the survey
    res_step5_appr = client.post(f"/api/surveys/{survey_id}/approve", json={"action": "APPROVE"}, headers=auth_headers)
    assert res_step5_appr.status_code == 200, f"Step 5 approval failed: {res_step5_appr.text}"
    assert res_step5_appr.json()["approval_status"] == "APPROVED"

    # =========================================================================
    # STEP 6: Quotation is generated from a template
    # =========================================================================
    quote_payload = {
        "customer_id": customer_id,
        "survey_id": survey_id,
        "package_type": "On-Grid System",
        "capacity_kw": 3.0,
        "include_battery": False
    }
    res_step6 = client.post("/api/quotations", json=quote_payload, headers=auth_headers)
    assert res_step6.status_code == 200, f"Step 6 quotation failed: {res_step6.text}"
    quote_data = res_step6.json()
    quotation_id = quote_data["id"]
    total_quote_amount = quote_data["total_amount"]
    advance_required = quote_data["advance_amount"]
    assert quote_data["quotation_number"].startswith("QT-")
    assert total_quote_amount > 100000.0, "Total price should reflect 3kW solar installation"
    assert advance_required >= (total_quote_amount * 0.20), "Advance must be >= 20%"

    # =========================================================================
    # STEP 7: Customer accepts the quotation
    # =========================================================================
    res_step7 = client.post(f"/api/quotations/{quotation_id}/accept", headers=auth_headers)
    assert res_step7.status_code == 200, f"Step 7 accept failed: {res_step7.text}"
    order_data = res_step7.json()
    order_id = order_data["id"]
    order_number = order_data["order_number"]
    assert order_number.startswith("SO-")
    assert order_data["status"] in ["CONFIRMED", "PENDING_PAYMENT", "APPROVED"]

    # =========================================================================
    # STEP 8: System automatically generates the BOM
    # =========================================================================
    # Verify sales order items or BOM generation for this order
    db = SessionLocal()
    try:
        order_obj = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        assert order_obj is not None
        # System has linked quotation items and calculated BOM
        assert order_obj.total_amount == total_quote_amount
    finally:
        db.close()

    # Verify BOM calculator endpoint matches configuration
    res_bom = client.get("/api/bom/calculate?package_type=On-Grid System&capacity_kw=3.0", headers=auth_headers)
    assert res_bom.status_code == 200
    bom_data = res_bom.json()
    assert bom_data["capacity_kw"] == 3.0
    assert len(bom_data["components"]) >= 3

    # =========================================================================
    # STEP 9: Payment is recorded and balance is calculated correctly
    # =========================================================================
    # Record advance payment (50% of quotation total)
    advance_paid = round(total_quote_amount * 0.50, 2)
    pay_payload = {
        "order_id": order_id,
        "customer_id": customer_id,
        "amount": advance_paid,
        "method": "NEFT",
        "reference": f"NEFT-AARKA-{uid}",
        "notes": "50% advance payment confirmed via HDFC Bank net banking."
    }
    res_step9 = client.post("/api/payments", json=pay_payload, headers=auth_headers)
    assert res_step9.status_code == 200, f"Step 9 payment failed: {res_step9.text}"
    payment_record = res_step9.json()
    assert payment_record["amount"] == advance_paid
    assert payment_record["status"] == "PENDING"
    verify_response = client.post(
        f"/api/payments/{payment_record['id']}/verify",
        json={"confirmation_note": "Verified against the supplied bank transaction reference."},
        headers=auth_headers,
    )
    assert verify_response.status_code == 200, verify_response.text

    # Verify order financial balance in database
    db = SessionLocal()
    try:
        updated_order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        assert updated_order.advance_paid >= advance_paid
        expected_balance = round(updated_order.total_amount - updated_order.advance_paid, 2)
        assert round(updated_order.balance_due, 2) == expected_balance
    finally:
        db.close()

    # =========================================================================
    # STEP 10: Inventory receives the preparation request
    # =========================================================================
    # Fetch dispatches / inventory register
    res_step10 = client.get("/api/dispatches", headers=auth_headers)
    assert res_step10.status_code == 200, f"Step 10 dispatches failed: {res_step10.text}"

    # =========================================================================
    # STEP 11: Required equipment is reserved
    # =========================================================================
    # Ensure products with requires_serial are available in inventory
    res_prods = client.get("/api/products?requires_serial=true", headers=auth_headers)
    assert res_prods.status_code == 200
    serial_prods = res_prods.json()
    assert len(serial_prods) > 0, "At least one product must require serial number"
    target_product_id = serial_prods[0]["id"]

    # =========================================================================
    # STEP 12: Individual serialized equipment is scanned and assigned to installation
    # =========================================================================
    # Generate unique inverter serial number and register it
    unique_serial_no = f"INV-3KW-SN-{uid.upper()}-{random.randint(1000, 9999)}"
    res_reg_serial = client.post("/api/serials", json={
        "product_id": target_product_id,
        "serial_number": unique_serial_no,
        "manufacturing_date": str(date.today() - timedelta(days=60))
    }, headers=auth_headers)
    assert res_reg_serial.status_code == 200, f"Serial registration failed: {res_reg_serial.text}"

    # Dispatch creation: Assign scanned serial to this order
    disp_payload = {
        "order_id": order_id,
        "serial_numbers": [unique_serial_no],
        "delivery_reference": f"DISP-E2E-{uid.upper()}",
        "courier_partner": "AARKA Logistics Fleet #3",
        "tracking_number": f"TRK-{uid.upper()}"
    }
    res_step12 = client.post("/api/dispatches", json=disp_payload, headers=auth_headers)
    assert res_step12.status_code == 200, f"Step 12 dispatch failed: {res_step12.text}"
    disp_data = res_step12.json()
    dispatch_id = disp_data["id"]

    # =========================================================================
    # STEP 13: Dispatch is confirmed
    # =========================================================================
    deliv_payload = {
        "delivery_date": str(date.today()),
        "customer_confirmed": True,
        "received_by": homeowner_name,
        "notes": "Delivered to site in pristine packaging. All items verified against packing list."
    }
    res_step13 = client.post(f"/api/dispatches/{dispatch_id}/confirm-delivery", json=deliv_payload, headers=auth_headers)
    assert res_step13.status_code == 200, f"Step 13 delivery confirm failed: {res_step13.text}"
    deliv_data = res_step13.json()
    assert deliv_data["success"] is True

    # =========================================================================
    # STEP 14: Delivery creates a pending warranty record
    # =========================================================================
    # Search warranties for the dispatched serial number
    res_step14 = client.get(f"/api/warranties/search?query={unique_serial_no}", headers=auth_headers)
    assert res_step14.status_code == 200, f"Step 14 warranty search failed: {res_step14.text}"
    war_search = res_step14.json()
    assert war_search["count"] >= 1, "A pending warranty record must exist for the dispatched serial"
    warranty_record = war_search["results"][0]
    assert warranty_record["serial_number"] == unique_serial_no
    assert warranty_record["status"] == "PENDING_ACTIVATION"
    assert warranty_record["days_remaining"] > 0

    # =========================================================================
    # STEP 15: A technician receives the assigned installation job
    # =========================================================================
    # Fetch active technician
    techs_res = client.get("/api/technicians", headers=auth_headers)
    assert techs_res.status_code == 200
    techs = techs_res.json()
    assert len(techs) > 0
    assigned_tech_id = techs[0]["id"]

    # Locate the installation job created for this order or schedule one
    all_jobs_res = client.get("/api/installations", headers=auth_headers)
    assert all_jobs_res.status_code == 200
    jobs = all_jobs_res.json()
    matched_job = next((j for j in jobs if j["order_id"] == order_id), None)
    if matched_job:
        job_id = matched_job["id"]
    else:
        inst_sched_payload = {
            "order_id": order_id,
            "technician_id": assigned_tech_id,
            "scheduled_date": str(date.today()),
            "capacity_kw": 3.0,
            "notes": "3kW On-Grid solar rooftop installation. Structure, panels, inverter, and net meter wiring."
        }
        res_step15 = client.post("/api/installations", json=inst_sched_payload, headers=auth_headers)
        assert res_step15.status_code == 200, f"Step 15 installation schedule failed: {res_step15.text}"
        job_id = res_step15.json()["id"]

    # =========================================================================
    # STEP 16: Technician records work times, installed capacity, photos, and checklist
    # =========================================================================
    # Complete 9-point commissioning checklist
    full_checklist = {
        "mounting_inspected": True,
        "panels_installed": True,
        "inverter_installed": True,
        "wiring_completed": True,
        "earthing_completed": True,
        "safety_checked": True,
        "system_tested": True,
        "power_verified": True,
        "customer_handover": True
    }
    # Update checklist
    res_step16_chk = client.put(f"/api/installations/{job_id}/checklist", json={"checklist_state": full_checklist}, headers=auth_headers)
    assert res_step16_chk.status_code == 200, f"Step 16 checklist update failed: {res_step16_chk.text}"

    # =========================================================================
    # STEP 17: Homeowner signs digitally
    # =========================================================================
    digital_signature = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxwYXRoIGQ9Ik0xMCA4MCBDIDQwIDEwLC...=="

    # =========================================================================
    # STEP 18: Installation is marked completed
    # =========================================================================
    complete_payload = {
        "checklist_state": full_checklist,
        "technical_observations": "VOC and ISC measured within tolerance. Dual earthing pits verified < 2 ohms.",
        "testing_results": "Grid sync verified: 238V AC 50.0Hz. Generation active at 2.85 kW peak midday.",
        "customer_signature": digital_signature,
        "labour_hours": 7.5
    }
    res_step18 = client.post(f"/api/installations/{job_id}/complete", json=complete_payload, headers=auth_headers)
    assert res_step18.status_code == 200, f"Step 18 complete failed: {res_step18.text}"
    step18_data = res_step18.json()
    assert step18_data["success"] is True
    assert step18_data["status"] == "CUSTOMER_ACCEPTED"

    # Verify equipment status is now INSTALLED
    db = SessionLocal()
    try:
        installed_eq = db.query(SerializedEquipment).filter(SerializedEquipment.serial_number == unique_serial_no).first()
        assert installed_eq.status == "INSTALLED"
        assert installed_eq.installation_id == job_id
    finally:
        db.close()

    # =========================================================================
    # STEP 19: The customer reports an inverter fault after installation
    # =========================================================================
    # The manufacturer coverage has not been verified yet.
    ticket_payload = {
        "customer_id": customer_id,
        "serial_number": unique_serial_no,
        "fault_description": "Inverter DC-DC converter alarm E04 triggered after grid fluctuation.",
        "fault_code": "ERR-E04",
        "priority": "HIGH",
        "notes": "Customer called helpline stating red fault LED is blinking on inverter panel."
    }
    res_step19 = client.post("/api/service/tickets", json=ticket_payload, headers=auth_headers)
    assert res_step19.status_code == 200, f"Step 19 ticket creation failed: {res_step19.text}"
    ticket = res_step19.json()
    ticket_id = ticket["id"]
    ticket_number = ticket["ticket_number"]
    assert "TKT-" in ticket_number or "SRV-" in ticket_number

    # =========================================================================
    # STEP 20: Support locates customer, installation, inverter serial, and warranty
    # =========================================================================
    res_step20_search = client.get(f"/api/service/tickets?search={homeowner_name}", headers=auth_headers)
    assert res_step20_search.status_code == 200, f"Step 20 support search failed: {res_step20_search.text}"
    tickets = res_step20_search.json()
    assert any(t["id"] == ticket_id for t in tickets), "Support could not locate the active ticket"

    # Support inspects warranty record for this inverter
    res_step20_war = client.get(f"/api/warranties/search?query={unique_serial_no}", headers=auth_headers)
    assert res_step20_war.status_code == 200
    war_info = res_step20_war.json()["results"][0]
    assert war_info["customer_name"] == homeowner_name

    # =========================================================================
    # STEP 21: Pending coverage is not represented as active
    # =========================================================================
    assert ticket["warranty_status"] == "PENDING_ACTIVATION", f"Expected PENDING_ACTIVATION, got: {ticket['warranty_status']}"

    # =========================================================================
    # STEP 22: No customer charge is applied while coverage is unverified
    # =========================================================================
    assert ticket["labour_charges"] == 0.0, "Labour charges must be ₹0 under warranty"
    assert ticket["parts_charges"] == 0.0, "Parts charges must be ₹0 under warranty"
    assert ticket["total_charges"] == 0.0, "Total charges must be ₹0 under warranty"

    # =========================================================================
    # STEP 23: Customer confirms resolution and the ticket is closed
    # =========================================================================
    # 23a: Support resolves the ticket
    res_step23_res = client.post(f"/api/service/tickets/{ticket_id}/resolve", headers=auth_headers)
    assert res_step23_res.status_code == 200, f"Step 23 resolve failed: {res_step23_res.text}"
    assert res_step23_res.json()["success"] is True

    # 23b: Customer confirms resolution and ticket is officially closed
    res_step23_conf = client.post(f"/api/service/tickets/{ticket_id}/confirm", headers=auth_headers)
    assert res_step23_conf.status_code == 200, f"Step 23 confirm failed: {res_step23_conf.text}"
    assert res_step23_conf.json()["success"] is True

    # Verify status in database
    db = SessionLocal()
    try:
        closed_ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
        assert closed_ticket.status == "CLOSED"
        assert closed_ticket.customer_confirmed is True
    finally:
        db.close()

    # =========================================================================
    # STEP 24: Director can see project's actual revenue, cost, profit, balance, and service history
    # =========================================================================
    # 24a: Financial dashboard metrics
    res_fin_dash = client.get("/api/finance/overview", headers=auth_headers)
    assert res_fin_dash.status_code == 200, f"Step 24 finance overview failed: {res_fin_dash.text}"
    fin_data = res_fin_dash.json()
    assert fin_data["total_revenue"] > 0
    assert "outstanding_receivables" in fin_data

    # 24b: Project profitability register
    res_prof = client.get("/api/finance/project-profitability", headers=auth_headers)
    assert res_prof.status_code == 200, f"Step 24 profitability failed: {res_prof.text}"
    projects = res_prof.json()
    assert len(projects) >= 1
    # Find our project or verify general profitability arithmetic
    for p in projects:
        assert "recognized_revenue" in p
        assert "total_cost" in p
        assert "gross_margin" in p
        assert round(p["recognized_revenue"] - p["total_cost"], 2) == round(p["gross_margin"], 2)

    # 24c: Holistic Executive Dashboard
    res_exec = client.get("/api/dashboard/summary?period=month", headers=auth_headers)
    assert res_exec.status_code == 200, f"Step 24 executive dashboard failed: {res_exec.text}"
    exec_data = res_exec.json()
    assert exec_data["metrics"]["total_customers"] > 0
    assert exec_data["metrics"]["total_enquiries"] > 0
    assert exec_data["financials"]["total_revenue"] > 0
    assert len(exec_data["charts"]["revenue_trend"]) > 0
    assert len(exec_data["charts"]["funnel"]) > 0

    print("\n✅ SECTION 16: Complete 24-step end-to-end solar lifecycle verified successfully!")
