import calendar
import random
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.models.service import WarrantyRecord
from app.models.installation import InstallationJob
from app.models.commercial import SalesOrder, SalesOrderItem
from app.models.inventory import SerializedEquipment
from app.models.product import Product
from app.models.user import AuditLog


def add_calendar_months(start_date: date, months: int) -> date:
    """
    Performs calendar-aware month and year addition, properly handling leap years
    and varying month lengths (e.g. Feb 29 -> Feb 28 on non-leap years).
    """
    total_months = start_date.month + months - 1
    year = start_date.year + (total_months // 12)
    month = (total_months % 12) + 1
    max_days = calendar.monthrange(year, month)[1]
    day = min(start_date.day, max_days)
    return date(year, month, day)


def get_manufacturer_warranty_rules(product: Product) -> List[Dict[str, Any]]:
    """
    Retrieves manufacturer warranty rules for solar equipment.
    Solar panels have both Product (10-12 yrs) and Performance (25 yrs) warranties.
    Inverters have 5-10 years, Batteries have 5 years, and Structures have 10 years.
    """
    category = (product.category or "").upper()
    name = (product.name or "").lower()
    mfr = product.manufacturer or "Aarka Tech"
    model = product.model or product.sku

    rules = []

    # 1. Solar PV Panels: Product Warranty (10-12 yrs) + Linear Performance Warranty (25 yrs)
    if "PANEL" in category or "SOLAR" in category or "panel" in name or "module" in name:
        prod_months = max(120, product.warranty_months or 120)  # 10 years
        rules.append({
            "warranty_type": "PRODUCT",
            "duration_months": prod_months,
            "manufacturer": mfr,
            "model_number": model,
            "coverage_terms": f"10-Year ({prod_months // 12}-Year) Manufacturer Product Warranty against defects in materials and manufacturing workmanship under standard operating conditions."
        })
        rules.append({
            "warranty_type": "PERFORMANCE",
            "duration_months": 300,  # 25 years
            "manufacturer": mfr,
            "model_number": model,
            "coverage_terms": "25-Year Linear Power Output Warranty guaranteeing ≥98% nominal power output in Year 1 and ≤0.55% annual degradation through Year 25 (minimum 84.8% at Year 25)."
        })

    # 2. Solar Inverters: 5 to 10 Year Product Warranty
    elif "INVERTER" in category or "inverter" in name:
        inv_months = max(60, product.warranty_months or 60)  # 5 to 10 years
        rules.append({
            "warranty_type": "PRODUCT",
            "duration_months": inv_months,
            "manufacturer": mfr,
            "model_number": model,
            "coverage_terms": f"{inv_months // 12}-Year Comprehensive Inverter Warranty covering power conversion electronics, MPPT controllers, display interface, and remote communication telemetry."
        })

    # 3. Batteries / Energy Storage: 5 Year / Cycle Warranty
    elif "BATTERY" in category or "battery" in name or "storage" in name:
        bat_months = max(60, product.warranty_months or 60)
        rules.append({
            "warranty_type": "PRODUCT",
            "duration_months": bat_months,
            "manufacturer": mfr,
            "model_number": model,
            "coverage_terms": f"{bat_months // 12}-Year / 6,000 Cycle Lithium-ion Solar Storage Warranty with minimum 70% retained capacity retention."
        })

    # 4. Mounting Structures: 10 Year Structural Integrity Warranty
    elif "STRUCTURE" in category or "structure" in name or "mounting" in name:
        struct_months = max(120, product.warranty_months or 120)
        rules.append({
            "warranty_type": "PRODUCT",
            "duration_months": struct_months,
            "manufacturer": mfr,
            "model_number": model,
            "coverage_terms": "10-Year Structural Integrity Warranty for Elevated Anodized Aluminium / Hot-Dip Galvanized Mounting Structures against mechanical failure and corrosion."
        })

    # 5. Electrical Balance of System (BOS) / Standard Products
    else:
        gen_months = max(24, product.warranty_months or 24)
        rules.append({
            "warranty_type": "PRODUCT",
            "duration_months": gen_months,
            "manufacturer": mfr,
            "model_number": model,
            "coverage_terms": f"{gen_months}-Month Standard Manufacturer Equipment Warranty against manufacturing and operational faults."
        })

    return rules


def generate_unique_warranty_number(db: Session, year: Optional[int] = None) -> str:
    yr = year or date.today().year
    num = f"WAR-{yr}-{random.randint(10000, 99999)}"
    while db.query(WarrantyRecord).filter(WarrantyRecord.warranty_number == num).first():
        num = f"WAR-{yr}-{random.randint(10000, 99999)}"
    return num


def activate_warranties_for_installation(
    db: Session,
    job: InstallationJob,
    completion_date: Optional[date] = None,
    user_name: str = "System"
) -> List[WarrantyRecord]:
    """
    PRIMARY BUSINESS WORKFLOW:
    When an installation is marked as completed (and customer signature recorded),
    AARKA automatically activates warranties for all installed equipment.

    Enforces:
    1. Verification of completion status.
    2. Equipment identification (via SerializedEquipment and Order items).
    3. Product warranty term retrieval.
    4. Separate records for Product vs Performance warranties.
    5. Calendar-aware activation and expiry calculation.
    6. Customer & SalesOrder association.
    7. Idempotency (prevent duplicate records if re-run).
    8. AuditLog creation.
    """
    # Verify installation status is completed or customer accepted
    if job.status not in ["CUSTOMER_ACCEPTED", "COMPLETED"]:
        raise ValueError(f"Cannot activate warranty: Installation status is '{job.status}', but must be COMPLETED or CUSTOMER_ACCEPTED.")

    order = job.order
    customer_id = job.customer_id
    order_id = job.order_id
    act_date = completion_date or (job.end_time.date() if job.end_time else date.today())

    activated_records: List[WarrantyRecord] = []

    # 1. Identify all serialized equipment assigned to this order or installation
    serials = db.query(SerializedEquipment).filter(
        (SerializedEquipment.order_id == order_id) | (SerializedEquipment.installation_id == job.id)
    ).all()

    processed_keys = set()

    for s in serials:
        product = s.product
        if not product:
            continue

        rules = get_manufacturer_warranty_rules(product)
        for rule in rules:
            key = (s.serial_number, rule["warranty_type"])
            if key in processed_keys:
                continue
            processed_keys.add(key)

            # Check for existing warranty record (IDEMPOTENCY)
            existing = db.query(WarrantyRecord).filter(
                WarrantyRecord.serial_number == s.serial_number,
                WarrantyRecord.warranty_type == rule["warranty_type"]
            ).first()

            if existing:
                # Update status to ACTIVE if it was pending
                if existing.status in ["PENDING_ACTIVATION", "COVERED"]:
                    existing.status = "ACTIVE"
                    existing.warranty_start = act_date
                    existing.warranty_end = add_calendar_months(act_date, rule["duration_months"])
                activated_records.append(existing)
                continue

            # Calculate calendar-aware expiry
            exp_date = add_calendar_months(act_date, rule["duration_months"])
            war_num = generate_unique_warranty_number(db, act_date.year)

            warranty = WarrantyRecord(
                warranty_number=war_num,
                serial_number=s.serial_number,
                product_id=product.id,
                customer_id=customer_id,
                order_id=order_id,
                installation_id=job.id,
                warranty_type=rule["warranty_type"],
                manufacturer=rule["manufacturer"],
                model_number=rule["model_number"],
                duration_months=rule["duration_months"],
                delivery_date=s.dispatch_date if s.dispatch_date else act_date,
                warranty_start=act_date,
                warranty_end=exp_date,
                status="ACTIVE",
                coverage_terms=rule["coverage_terms"],
                notes=f"Auto-activated on installation completion ({job.job_number}). Recorded by {user_name}."
            )
            db.add(warranty)
            activated_records.append(warranty)

    # 2. Also check if there are non-serialized order items (e.g. Structure or Workmanship)
    if order:
        # AARKA EPC System Workmanship Warranty (5-Year / 60-Month Workmanship Warranty)
        workmanship_key = (f"WORKMANSHIP-{order.order_number}", "WORKMANSHIP")
        if workmanship_key not in processed_keys:
            processed_keys.add(workmanship_key)
            existing_workmanship = db.query(WarrantyRecord).filter(
                WarrantyRecord.order_id == order.id,
                WarrantyRecord.warranty_type == "WORKMANSHIP"
            ).first()

            if not existing_workmanship:
                # Find any product id or default product
                default_prod = db.query(Product).first()
                if default_prod:
                    workmanship_exp = add_calendar_months(act_date, 60)  # 5 years
                    work_num = generate_unique_warranty_number(db, act_date.year)
                    workmanship_war = WarrantyRecord(
                        warranty_number=work_num,
                        serial_number=f"AARKA-EPC-{order.order_number}",
                        product_id=default_prod.id,
                        customer_id=customer_id,
                        order_id=order_id,
                        installation_id=job.id,
                        warranty_type="WORKMANSHIP",
                        manufacturer="AARKA Solar Solutions",
                        model_number=f"Turnkey EPC ({job.capacity_kw} kW)",
                        duration_months=60,
                        delivery_date=act_date,
                        warranty_start=act_date,
                        warranty_end=workmanship_exp,
                        status="ACTIVE",
                        coverage_terms="5-Year Complete EPC Installation & Workmanship Warranty covering roof penetrations, water-tightness, DC/AC cabling, earthing grounding, and DISCOM grid-tie synchronization.",
                        notes=f"System Workmanship Warranty auto-activated upon customer handover of job {job.job_number}."
                    )
                    db.add(workmanship_war)
                    activated_records.append(workmanship_war)

    db.commit()

    # Record Audit Event
    audit = AuditLog(
        user_id=None,
        action="WARRANTY_AUTO_ACTIVATION",
        entity_type="INSTALLATION",
        entity_id=job.id,
        details=f"Auto-activated {len(activated_records)} warranty certificates for Installation Job {job.job_number} (Order {order.order_number if order else 'N/A'}). Handover accepted on {act_date}."
    )
    db.add(audit)
    db.commit()

    return activated_records
