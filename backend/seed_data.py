import os
import json
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.core.rbac import seed_rbac_catalog
import app.models
from app.models.survey import Technician, SiteSurvey
from app.models.customer import Customer, Lead
from app.models.product import Product, Package, BOMTemplate
from app.models.inventory import Supplier, InventoryItem, StockMovement, SerializedEquipment, Dispatch
from app.models.commercial import Quotation, QuotationItem, SalesOrder, SalesOrderItem, Payment
from app.models.installation import InstallationJob
from app.models.service import WarrantyRecord, ServiceTicket
from app.models.finance import ProjectExpense, Invoice
from app.models.subsidy import SubsidyApplication


def seed():
    db: Session = SessionLocal()
    try:
        if os.environ.get("AARKA_SEED_DEMO_DATA") != "1":
            raise RuntimeError(
                "Set AARKA_SEED_DEMO_DATA=1 only when using a disposable development database."
            )

        if db.query(Product).filter(Product.sku == "MOD-WAAREE-540W").first():
            print("Database already contains seed data. Skipping duplicate seed.")
            return

        print("Seeding AARKA Solar Management System database...")
        seed_rbac_catalog(db)

        # 1. Demo technician profiles; these do not create login accounts.
        tech_names = [
            ("Anand Kumar", "+91 98765 11001", "Rooftop, Inverters, AC Wiring", 5),
            ("Ramesh Varma", "+91 98765 11002", "Structural Mounts, Civil Work", 4),
            ("Mohan Krishna", "+91 98765 11003", "Off-Grid Batteries, High Voltage DC", 6),
            ("Suresh Babu", "+91 98765 11004", "Grid-Tied Inverters, Net Metering", 3),
            ("Karthik Pillai", "+91 98765 11005", "Site Survey, Shade Analysis", 4),
            ("Vijay Chary", "+91 98765 11006", "Solar PV Module Mounting", 2),
            ("Sunil Yadav", "+91 98765 11007", "Earthing & Lightning Arresters", 5),
            ("Praveen Teja", "+91 98765 11008", "Inverter Commissioning, Testing", 4),
            ("Mahesh Goud", "+91 98765 11009", "Residential Rooftop Systems", 3),
            ("Dinesh Reddy", "+91 98765 11010", "Commercial Solar Structures", 5),
            ("Santosh Kumar", "+91 98765 11011", "Battery Bank Integration", 4),
            ("Harish Naidu", "+91 98765 11012", "Cable Trays, Conduit Laying", 2),
            ("Ganesh Acharya", "+91 98765 11013", "After-Sales Repair, Fault Tracing", 6),
            ("Srinivas Rao", "+91 98765 11014", "Safety & Compliance Audit", 7),
            ("Naveen Prasad", "+91 98765 11015", "App & Wi-Fi Inverter Monitoring", 3),
        ]
        technicians = []
        for name, phone, skills, exp in tech_names:
            t = Technician(
                name=name,
                phone=phone,
                email=f"{name.lower().replace(' ', '.')}@aarka.com",
                skills=skills,
                experience_years=exp,
                availability="AVAILABLE",
                status="ACTIVE",
                employment_status="FULL_TIME"
            )
            db.add(t)
            technicians.append(t)
        db.commit()

        # 3. Suppliers
        suppliers_data = [
            ("Waaree Energies Ltd", "Amit Singhal", "+91 22 6644 4444", "support@waaree.com", "Mumbai, Maharashtra", "Solar Panels OEM", 5),
            ("Growatt New Energy", "Ken Zhang", "+91 11 4500 8800", "india@growatt.com", "Gurugram, Haryana", "Inverter Manufacturers", 4),
            ("Exide Solar Division", "Ramanathan K", "+91 33 2283 2120", "solar@exide.co.in", "Kolkata, West Bengal", "Battery Systems", 7),
            ("Polycab Wires & Switchgear", "Deepak Joshi", "+91 22 2410 7000", "info@polycab.com", "Vadodara, Gujarat", "Cables & Switchgear", 3),
            ("Tata Solar Steel", "Sanjay Mitra", "+91 20 6601 3000", "structures@tatasteel.com", "Jamshedpur, Jharkhand", "Mounting Structures", 6),
        ]
        for name, cp, phone, email, addr, cat, lt in suppliers_data:
            s = Supplier(
                name=name,
                contact_person=cp,
                phone=phone,
                email=email,
                address=addr,
                category=cat,
                lead_time_days=lt,
                status="ACTIVE"
            )
            db.add(s)
        db.commit()

        # 4. Products Catalogue
        products_data = [
            # Panels
            ("Waaree 540W Mono PERC Solar Panel", "MOD-WAAREE-540W", "solar_panel", "Waaree", "Arka 540", "nos", 0.54, "Both", 9800.0, 13500.0, 20, 240, False, "Warehouse Yard A"),
            # Inverters (Serialized!)
            ("Growatt 3.3kW On-Grid String Inverter", "INV-GROWATT-3.3KW", "inverter", "Growatt", "MIN 3300TL-X", "nos", 3.3, "On-Grid", 24000.0, 34500.0, 5, 24, True, "Secure Electronics Rack 1"),
            ("Growatt 5.0kW On-Grid String Inverter", "INV-GROWATT-5.0KW", "inverter", "Growatt", "MIN 5000TL-X", "nos", 5.0, "On-Grid", 34000.0, 48000.0, 4, 24, True, "Secure Electronics Rack 1"),
            ("Growatt 3.0kW Off-Grid Hybrid Inverter", "INV-GROWATT-3K-OFF", "inverter", "Growatt", "SPF 3000TL", "nos", 3.0, "Off-Grid", 28000.0, 39500.0, 4, 24, True, "Secure Electronics Rack 2"),
            ("Growatt 5.0kW Off-Grid Hybrid Inverter", "INV-GROWATT-5K-OFF", "inverter", "Growatt", "SPF 5000ES", "nos", 5.0, "Off-Grid", 42000.0, 58000.0, 3, 24, True, "Secure Electronics Rack 2"),
            # Batteries (Serialized!)
            ("Exide Solar 150Ah 12V Tubular Battery", "BAT-EXIDE-150AH", "battery", "Exide", "SolarTubular-150", "nos", 1.8, "Off-Grid", 9500.0, 14200.0, 8, 24, True, "Battery Storage Room"),
            ("Aarka LiFePO4 5.1kWh Wallmount Battery", "BAT-AARKA-5KWH", "battery", "Aarka Tech", "LFP-5120", "nos", 5.1, "Off-Grid", 85000.0, 115000.0, 4, 60, True, "Battery Storage Room"),
            # Electrical Balance of System (BOS)
            ("Solar DC Cable 4sqmm UV Resistant", "CAB-DC-4SQMM", "wires", "Polycab", "SolarDC-4", "meters", None, "Both", 35.0, 55.0, 200, 12, False, "Cable Reel Section"),
            ("MC4 Solar Connectors Male/Female Pair", "CON-MC4-PAIR", "connectors", "Aarka Tech", "MC4-1000V", "nos", None, "Both", 45.0, 90.0, 100, 12, False, "Bin B-12"),
            ("ACDB 1-Phase Distribution Box with SPD & MCB", "BOX-ACDB-1PH", "wiring_box", "Polycab", "ACDB-1P-32A", "nos", None, "Both", 2200.0, 3600.0, 10, 12, False, "Rack C-3"),
            ("DCDB 1-String 1000V Box with SPD & Fuse", "BOX-DCDB-1STR", "wiring_box", "Polycab", "DCDB-1S-1000V", "nos", None, "Both", 2400.0, 3900.0, 10, 12, False, "Rack C-4"),
            ("Chemical Earthing Electrode with BFC Compound", "EARTH-CHEM-2M", "earthing_system", "Aarka Tech", "EARTH-2M", "nos", None, "Both", 2100.0, 3500.0, 15, 12, False, "Heavy Yard"),
            ("Galvanized Iron Elevated Roof Mounting Set (per kW)", "STR-GI-ROOF-KW", "mounting_structure", "Tata Steel", "GI-HOTDIP-KW", "nos", 1.0, "Both", 3500.0, 5800.0, 25, 120, False, "Heavy Yard"),
            ("Solar Installation, Testing & Commissioning Service", "SRV-INSTALL-KW", "installation_service", "Aarka Tech", "INST-COMM-KW", "kW", 1.0, "Both", 2500.0, 4500.0, 100, 12, False, "Field Operations"),
        ]
        db_products = {}
        for row in products_data:
            p = Product(
                name=row[0],
                sku=row[1],
                category=row[2],
                manufacturer=row[3],
                model=row[4],
                unit=row[5],
                capacity_kw=row[6],
                system_type=row[7],
                purchase_price=row[8],
                selling_price=row[9],
                min_stock=row[10],
                warranty_months=row[11],
                requires_serial=row[12],
                warehouse_location=row[13],
                description=f"{row[0]} - High performance solar component"
            )
            db.add(p)
            db.flush()
            db_products[p.sku] = p

            # Inventory item
            initial_stock = 60 if p.category == "solar_panel" else (20 if p.requires_serial else 150)
            inv = InventoryItem(
                product_id=p.id,
                sku=p.sku,
                quantity=initial_stock,
                reserved_quantity=2,
                reorder_level=p.min_stock,
                unit_price=p.purchase_price,
                warehouse_location=p.warehouse_location,
                supplier=p.manufacturer
            )
            db.add(inv)
        db.commit()

        # 5. Configured Packages
        packages_list = [
            ("Solar Panel Set", "Solar Panel Set", 1.0, 35000.0),
            ("Solar Panel Set", "Solar Panel Set", 3.0, 95000.0),
            ("Solar Panel Set", "Solar Panel Set", 5.0, 155000.0),
            ("On-Grid System", "On-Grid System", 1.0, 68000.0),
            ("On-Grid System", "On-Grid System", 2.0, 125000.0),
            ("On-Grid System", "On-Grid System", 3.0, 178000.0),
            ("On-Grid System", "On-Grid System", 4.0, 235000.0),
            ("On-Grid System", "On-Grid System", 5.0, 285000.0),
            ("Off-Grid System", "Off-Grid System", 1.0, 98000.0),
            ("Off-Grid System", "Off-Grid System", 2.0, 175000.0),
            ("Off-Grid System", "Off-Grid System", 3.0, 245000.0),
            ("Off-Grid System", "Off-Grid System", 4.0, 320000.0),
            ("Off-Grid System", "Off-Grid System", 5.0, 395000.0),
            ("Installation Service", "Installation Service", 1.0, 5000.0),
            ("Installation Service", "Installation Service", 3.0, 14000.0),
            ("Installation Service", "Installation Service", 5.0, 22000.0),
        ]
        for name, p_type, cap, price in packages_list:
            pkg = Package(
                name=f"{name} {cap} kW",
                package_type=p_type,
                capacity_kw=cap,
                base_price=price,
                description=f"Complete {cap} kW {p_type} engineered for high yield rooftop solar."
            )
            db.add(pkg)
        db.commit()

        # 6. Configured BOM Template for 3 kW On-Grid System
        panel_p = db_products["MOD-WAAREE-540W"]
        inv_3k = db_products["INV-GROWATT-3.3KW"]
        cab = db_products["CAB-DC-4SQMM"]
        mc4 = db_products["CON-MC4-PAIR"]
        acdb = db_products["BOX-ACDB-1PH"]
        dcdb = db_products["BOX-DCDB-1STR"]
        earth = db_products["EARTH-CHEM-2M"]
        struct = db_products["STR-GI-ROOF-KW"]
        inst_srv = db_products["SRV-INSTALL-KW"]

        bom_items_3k = [
            (panel_p.id, 6.0, "6x 540W Mono PERC = 3.24 kW Array"),
            (inv_3k.id, 1.0, "1x 3.3kW On-Grid Inverter"),
            (struct.id, 3.0, "3kW GI Roof Structure"),
            (cab.id, 50.0, "50m UV Resistant DC Cable"),
            (mc4.id, 12.0, "12 pairs MC4 Connectors"),
            (acdb.id, 1.0, "1x ACDB Box with SPD"),
            (dcdb.id, 1.0, "1x DCDB Box with SPD"),
            (earth.id, 3.0, "3x Chemical Earthing Rods"),
            (inst_srv.id, 3.0, "3 kW Installation & Commissioning"),
        ]
        for pid, qty, note in bom_items_3k:
            b_temp = BOMTemplate(
                package_type="On-Grid System",
                capacity_kw=3.0,
                product_id=pid,
                quantity=qty,
                is_mandatory=True,
                notes=note
            )
            db.add(b_temp)
        db.commit()

        # 7. Serialized Equipment In Stock
        serials_data = [
            (inv_3k.id, "INV-3KW-9001", "AVAILABLE", "Warehouse - Rack S1"),
            (inv_3k.id, "INV-3KW-9002", "AVAILABLE", "Warehouse - Rack S1"),
            (inv_3k.id, "INV-3KW-9003", "AVAILABLE", "Warehouse - Rack S1"),
            (inv_3k.id, "INV-3KW-9004", "AVAILABLE", "Warehouse - Rack S1"),
            (inv_3k.id, "INV-3KW-9005", "AVAILABLE", "Warehouse - Rack S1"),
            (db_products["INV-GROWATT-5.0KW"].id, "INV-5KW-9010", "AVAILABLE", "Warehouse - Rack S2"),
            (db_products["INV-GROWATT-5.0KW"].id, "INV-5KW-9011", "AVAILABLE", "Warehouse - Rack S2"),
            (db_products["BAT-EXIDE-150AH"].id, "BAT-150AH-8001", "AVAILABLE", "Battery Rack 1"),
            (db_products["BAT-EXIDE-150AH"].id, "BAT-150AH-8002", "AVAILABLE", "Battery Rack 1"),
            (db_products["BAT-EXIDE-150AH"].id, "BAT-150AH-8003", "AVAILABLE", "Battery Rack 1"),
            (db_products["BAT-AARKA-5KWH"].id, "BAT-5KWH-7001", "AVAILABLE", "Battery Rack 2"),
        ]
        for pid, sn, st, loc in serials_data:
            se = SerializedEquipment(
                product_id=pid,
                serial_number=sn,
                status=st,
                supplier="Growatt New Energy" if "INV" in sn else "Exide Solar Division",
                purchase_reference="PO-2026-INWARD",
                current_location=loc
            )
            db.add(se)
        db.commit()

        # 8. Sample Customers & Leads
        cust_1 = Customer(
            name="Venkateswara Rao",
            phone="+91 94401 23456",
            email="v.rao@gmail.com",
            address="Plot 42, Jubilee Hills, Road No 36",
            city="Hyderabad",
            customer_type="Residential",
            lead_source="Website",
            required_capacity_kw=3.0,
            solar_requirement="On-Grid",
            monthly_bill=3200.0,
            subsidy_required=True,
            status="ACTIVE"
        )
        cust_2 = Customer(
            name="Sri Krishna Diagnostics",
            phone="+91 98490 87654",
            email="admin@krishnadiag.in",
            address="Commercial Complex, Madhapur Main Road",
            city="Hyderabad",
            customer_type="Commercial",
            lead_source="Referral",
            required_capacity_kw=5.0,
            solar_requirement="On-Grid",
            monthly_bill=14500.0,
            subsidy_required=False,
            status="ACTIVE"
        )
        cust_3 = Customer(
            name="Dr. Sunita Varma",
            phone="+91 97012 34567",
            email="dr.sunita@hospital.org",
            address="Villa 18, Gachibowli Green Acres",
            city="Hyderabad",
            customer_type="Residential",
            lead_source="WhatsApp",
            required_capacity_kw=4.0,
            solar_requirement="Off-Grid",
            monthly_bill=5600.0,
            subsidy_required=True,
            status="ACTIVE"
        )
        db.add_all([cust_1, cust_2, cust_3])
        db.commit()

        # Leads
        lead_1 = Lead(
            lead_reference="LEAD-1001",
            customer_id=cust_1.id,
            customer_name=cust_1.name,
            phone=cust_1.phone,
            email=cust_1.email,
            address=cust_1.address,
            city=cust_1.city,
            customer_type=cust_1.customer_type,
            lead_source=cust_1.lead_source,
            required_capacity_kw=3.0,
            solar_requirement="On-Grid",
            monthly_bill=cust_1.monthly_bill,
            subsidy_required=True,
            roof_availability="600 sqft shadow-free RCC roof",
            grid_suitable=True,
            estimated_value=178000.0,
            assigned_sales_rep="Rajesh Sharma",
            stage="QUALIFIED",
            status="OPEN",
            notes="Customer interested in 3kW On-Grid under PM Surya Ghar Muft Bijli Yojana."
        )
        lead_2 = Lead(
            lead_reference="LEAD-1002",
            customer_id=cust_2.id,
            customer_name=cust_2.name,
            phone=cust_2.phone,
            email=cust_2.email,
            address=cust_2.address,
            city=cust_2.city,
            customer_type=cust_2.customer_type,
            lead_source="Referral",
            required_capacity_kw=5.0,
            solar_requirement="On-Grid",
            monthly_bill=14500.0,
            subsidy_required=False,
            roof_availability="1200 sqft sheet roof",
            grid_suitable=True,
            estimated_value=285000.0,
            assigned_sales_rep="Rajesh Sharma",
            stage="NEW",
            status="OPEN",
            notes="High daytime consumption. Wants quick commercial quotation."
        )
        db.add_all([lead_1, lead_2])
        db.commit()

        # 9. Site Survey for Customer 1 (Approved)
        survey_1 = SiteSurvey(
            survey_reference="SURV-2026-101",
            lead_id=lead_1.id,
            customer_id=cust_1.id,
            technician_id=technicians[4].id,  # Karthik Pillai
            scheduled_date=date.today() - timedelta(days=5),
            actual_survey_date=date.today() - timedelta(days=5),
            roof_area=650.0,
            shadow_free_area=580.0,
            roof_direction="South",
            roof_tilt=18.0,
            cable_distance=18.0,
            structural_condition="RCC Flat Concrete Slab - Excellent structural strength",
            grid_connection_suitable=True,
            monthly_bill=cust_1.monthly_bill,
            required_capacity_kw=3.0,
            observations="South facing flat terrace with zero tall trees. Direct connection to meter panel within 18 meters.",
            technician_recommendation="Recommended 3.24 kW system (6x 540W modules) with 3.3kW On-Grid inverter.",
            status="APPROVED",
            approval_status="APPROVED",
            approved_by="Sivamani Dasari",
            photo_urls=json.dumps(["/api/uploads/surveys/sample_roof_1.jpg", "/api/uploads/surveys/sample_meter_1.jpg"])
        )
        db.add(survey_1)
        lead_1.stage = "SURVEY_APPROVED"
        db.commit()

        # 10. Completed Historical Order for Dr. Sunita Varma (with Warranty & Service Ticket)
        # To demonstrate the warranty claim workflow immediately!
        hist_order = SalesOrder(
            order_number="SO-2026-0881",
            customer_id=cust_3.id,
            package_type="On-Grid System",
            capacity_kw=3.0,
            hardware_cost=135000.0,
            installation_cost=15000.0,
            total_amount=177000.0,
            advance_paid=177000.0,
            balance_due=0.0,
            delivery_address=cust_3.address,
            status="COMPLETED",
            picklist_generated=True
        )
        db.add(hist_order)
        db.commit()

        # Assigned Serialized Inverter for customer 3
        ser_c3 = SerializedEquipment(
            product_id=inv_3k.id,
            serial_number="INV-3KW-8888",
            status="INSTALLED",
            supplier="Growatt New Energy",
            purchase_reference="PO-HIST-2025",
            current_location=f"Customer Site - {cust_3.name}",
            customer_id=cust_3.id,
            order_id=hist_order.id,
            dispatch_date=date.today() - timedelta(days=120),
            warranty_start=date.today() - timedelta(days=120),
            warranty_end=date.today() - timedelta(days=120) + timedelta(days=730)
        )
        db.add(ser_c3)
        db.commit()

        # Active Warranty Record for Dr. Sunita
        war_c3 = WarrantyRecord(
            warranty_number="WAR-2026-0042",
            serial_number="INV-3KW-8888",
            product_id=inv_3k.id,
            customer_id=cust_3.id,
            order_id=hist_order.id,
            delivery_date=date.today() - timedelta(days=120),
            warranty_start=date.today() - timedelta(days=120),
            warranty_end=date.today() - timedelta(days=120) + timedelta(days=730),
            status="COVERED",
            coverage_terms="100% parts & labor covered under manufacturer warranty policy."
        )
        db.add(war_c3)

        # Service Ticket for Dr. Sunita (Simulating inverter fault ERR-04)
        tkt_c3 = ServiceTicket(
            ticket_number="TKT-2026-0105",
            customer_id=cust_3.id,
            serial_number="INV-3KW-8888",
            equipment_type="Growatt 3.3kW On-Grid String Inverter",
            fault_code="ERR-04",
            fault_description="Inverter displays Error 04: DC Bus over-voltage warning during peak solar noon.",
            complaint_photos=json.dumps(["/api/uploads/service/inverter_fault_err04.jpg"]),
            priority="HIGH",
            technician_id=technicians[12].id,  # Ganesh Acharya
            warranty_eligible=True,
            warranty_status="COVERED",
            diagnosis="Faulty DC input surge capacitor detected on MPPT tracker 1.",
            repair_details="Technician replaced internal surge module under warranty. Firmware updated to v3.12.",
            parts_used=json.dumps([{"part": "DC Surge Module MPPT1", "qty": 1, "cost": 0.0}]),
            labour_charges=0.0,
            parts_charges=0.0,
            total_charges=0.0,
            customer_approved_estimate=True,
            status="IN_PROGRESS",
            reported_date=date.today() - timedelta(days=2),
            customer_confirmed=False
        )
        db.add(tkt_c3)

        # Subsidy Application for Dr. Sunita
        sub_c3 = SubsidyApplication(
            application_number="SUB-2026-88001",
            customer_id=cust_3.id,
            scheme_name="PM Surya Ghar Muft Bijli Yojana",
            capacity_kw=3.0,
            submission_date=date.today() - timedelta(days=60),
            verification_status="VERIFIED",
            approval_status="APPROVED",
            subsidy_amount=78000.0,
            payment_status="PENDING",
            documents=json.dumps([{"name": "DISCOM_Sanction_Letter.pdf", "url": "/api/uploads/subsidies/sample.pdf"}]),
            remarks="Inspection completed by TSNPDCL inspector. Subsidy disbursement in queue."
        )
        db.add(sub_c3)

        # Project Expense
        exp_c3 = ProjectExpense(
            order_id=hist_order.id,
            category="LABOUR",
            amount=8500.0,
            description="Field technician team installation labour (3 crew members, 1 day)",
            expense_date=date.today() - timedelta(days=118),
            recorded_by="Suresh Gupta"
        )
        db.add(exp_c3)

        db.commit()
        print("Database seeded successfully with 100% relational integrity!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
