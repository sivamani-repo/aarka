from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product, Package, BOMTemplate
from app.schemas.schemas import BOMCalculationResult, BOMItemOut
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/bom", tags=["Bill of Materials (BOM)"])


@router.get("/calculate", response_model=BOMCalculationResult)
def calculate_bom(
    package_type: str = Query("On-Grid System"),
    capacity_kw: float = Query(3.0),
    include_installation: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Cap capacity between 1.0 and 10.0 kW
    capacity_kw = float(capacity_kw)
    if capacity_kw <= 0:
        capacity_kw = 1.0

    # 1. Check if configured BOM templates exist in database
    templates = db.query(BOMTemplate).filter(
        BOMTemplate.package_type == package_type,
        BOMTemplate.capacity_kw == capacity_kw
    ).all()

    components: List[BOMItemOut] = []
    hardware_cost = 0.0
    installation_cost = 0.0

    if templates:
        for t in templates:
            prod = t.product
            if not prod:
                continue
            item_total = prod.selling_price * t.quantity
            if prod.category == "installation_service":
                if include_installation:
                    installation_cost += item_total
                    components.append(BOMItemOut(
                        product_id=prod.id,
                        product_name=prod.name,
                        sku=prod.sku,
                        category=prod.category,
                        quantity=t.quantity,
                        unit=prod.unit,
                        unit_price=prod.selling_price,
                        total_price=item_total,
                        is_serialized=prod.requires_serial
                    ))
            else:
                hardware_cost += item_total
                components.append(BOMItemOut(
                    product_id=prod.id,
                    product_name=prod.name,
                    sku=prod.sku,
                    category=prod.category,
                    quantity=t.quantity,
                    unit=prod.unit,
                    unit_price=prod.selling_price,
                    total_price=item_total,
                    is_serialized=prod.requires_serial
                ))
    else:
        # Dynamic calculation based on available products in catalog
        panels_count = max(2, int(round((capacity_kw * 1000) / 540)))

        # A. Solar Panels
        panel = db.query(Product).filter(Product.category == "solar_panel").first()
        if panel:
            tot = panel.selling_price * panels_count
            hardware_cost += tot
            components.append(BOMItemOut(
                product_id=panel.id,
                product_name=f"{panel.name} ({panels_count} panels)",
                sku=panel.sku,
                category=panel.category,
                quantity=float(panels_count),
                unit=panel.unit,
                unit_price=panel.selling_price,
                total_price=tot,
                is_serialized=panel.requires_serial
            ))

        # B. Inverter (for On-Grid or Off-Grid)
        if package_type in ["On-Grid System", "Off-Grid System"]:
            inv_query = db.query(Product).filter(Product.category == "inverter")
            if package_type == "On-Grid System":
                inv = inv_query.filter(Product.system_type.in_(["On-Grid", "Both"])).first()
            else:
                inv = inv_query.filter(Product.system_type.in_(["Off-Grid", "Both"])).first() or inv_query.first()
            
            if inv:
                tot = inv.selling_price * 1.0
                hardware_cost += tot
                components.append(BOMItemOut(
                    product_id=inv.id,
                    product_name=f"{inv.name} ({capacity_kw}kW Rated)",
                    sku=inv.sku,
                    category=inv.category,
                    quantity=1.0,
                    unit=inv.unit,
                    unit_price=inv.selling_price,
                    total_price=tot,
                    is_serialized=True
                ))

        # C. Batteries (Only for Off-Grid System)
        if package_type == "Off-Grid System":
            bat = db.query(Product).filter(Product.category == "battery").first()
            if bat:
                bat_count = 2 if capacity_kw <= 2.0 else 4
                tot = bat.selling_price * bat_count
                hardware_cost += tot
                components.append(BOMItemOut(
                    product_id=bat.id,
                    product_name=f"{bat.name} (Storage Pack)",
                    sku=bat.sku,
                    category=bat.category,
                    quantity=float(bat_count),
                    unit=bat.unit,
                    unit_price=bat.selling_price,
                    total_price=tot,
                    is_serialized=True
                ))

        # D. Mounting Structure
        structure = db.query(Product).filter(Product.category == "mounting_structure").first()
        if structure:
            tot = structure.selling_price * capacity_kw
            hardware_cost += tot
            components.append(BOMItemOut(
                product_id=structure.id,
                product_name=f"{structure.name} (Custom Roof Tilt GI)",
                sku=structure.sku,
                category=structure.category,
                quantity=float(capacity_kw),
                unit=structure.unit,
                unit_price=structure.selling_price,
                total_price=tot,
                is_serialized=False
            ))

        # E. Solar DC Cable
        wire = db.query(Product).filter(Product.category == "wires").first()
        if wire:
            wire_meters = max(30.0, capacity_kw * 15.0)
            tot = wire.selling_price * wire_meters
            hardware_cost += tot
            components.append(BOMItemOut(
                product_id=wire.id,
                product_name=f"{wire.name} (4 sqmm UV Resistant)",
                sku=wire.sku,
                category=wire.category,
                quantity=wire_meters,
                unit=wire.unit,
                unit_price=wire.selling_price,
                total_price=tot,
                is_serialized=False
            ))

        # F. MC4 Connectors
        connector = db.query(Product).filter(Product.category == "connectors").first()
        if connector:
            conn_qty = float(panels_count * 2)
            tot = connector.selling_price * conn_qty
            hardware_cost += tot
            components.append(BOMItemOut(
                product_id=connector.id,
                product_name=f"{connector.name} (Male/Female Pair)",
                sku=connector.sku,
                category=connector.category,
                quantity=conn_qty,
                unit=connector.unit,
                unit_price=connector.selling_price,
                total_price=tot,
                is_serialized=False
            ))

        # G. Safety Switches / ACDB & DCDB
        box = db.query(Product).filter(Product.category == "wiring_box").first()
        if box:
            tot = box.selling_price * 2.0
            hardware_cost += tot
            components.append(BOMItemOut(
                product_id=box.id,
                product_name=f"{box.name} (ACDB + DCDB with SPD & MCB)",
                sku=box.sku,
                category=box.category,
                quantity=2.0,
                unit=box.unit,
                unit_price=box.selling_price,
                total_price=tot,
                is_serialized=False
            ))

        # H. Earthing & Lightning Protection
        earthing = db.query(Product).filter(Product.category == "earthing_system").first()
        if earthing:
            earth_qty = 2.0 if capacity_kw <= 2.0 else 3.0
            tot = earthing.selling_price * earth_qty
            hardware_cost += tot
            components.append(BOMItemOut(
                product_id=earthing.id,
                product_name=f"{earthing.name} (Chemical Rods + Compound)",
                sku=earthing.sku,
                category=earthing.category,
                quantity=earth_qty,
                unit=earthing.unit,
                unit_price=earthing.selling_price,
                total_price=tot,
                is_serialized=False
            ))

        # I. Installation Service
        if include_installation:
            inst = db.query(Product).filter(Product.category == "installation_service").first()
            if inst:
                tot = inst.selling_price * capacity_kw
                installation_cost += tot
                components.append(BOMItemOut(
                    product_id=inst.id,
                    product_name=f"{inst.name} ({capacity_kw}kW Complete Installation)",
                    sku=inst.sku,
                    category=inst.category,
                    quantity=float(capacity_kw),
                    unit=inst.unit,
                    unit_price=inst.selling_price,
                    total_price=tot,
                    is_serialized=False
                ))

    subtotal = hardware_cost + installation_cost
    tax_rate = 0.18
    tax_amount = round(subtotal * tax_rate, 2)
    grand_total = round(subtotal + tax_amount, 2)

    return BOMCalculationResult(
        package_type=package_type,
        capacity_kw=capacity_kw,
        hardware_cost=round(hardware_cost, 2),
        installation_cost=round(installation_cost, 2),
        subtotal=round(subtotal, 2),
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        grand_total=grand_total,
        components=components
    )


@router.get("/templates")
def list_bom_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    templates = db.query(BOMTemplate).all()
    return [
        {
            "id": t.id,
            "package_type": t.package_type,
            "capacity_kw": t.capacity_kw,
            "product_id": t.product_id,
            "product_name": t.product.name if t.product else "",
            "sku": t.product.sku if t.product else "",
            "category": t.product.category if t.product else "",
            "quantity": t.quantity,
            "unit": t.product.unit if t.product else "nos",
            "unit_price": t.product.selling_price if t.product else 0.0,
            "is_mandatory": t.is_mandatory,
            "notes": t.notes
        }
        for t in templates
    ]

