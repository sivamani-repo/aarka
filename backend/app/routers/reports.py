import io
import csv
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commercial import SalesOrder, Payment
from app.models.installation import InstallationJob
from app.models.inventory import InventoryItem, SerializedEquipment
from app.models.service import WarrantyRecord, ServiceTicket
from app.models.survey import Technician
from app.models.subsidy import SubsidyApplication
from app.models.finance import ProjectExpense
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/reports", tags=["Director Analytics & Reports"])


def _generate_csv(report_type: str, db: Session):
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "profitability":
        writer.writerow(["Order Number", "Customer", "Capacity (kW)", "Package", "Recognized Revenue", "Advance Paid", "Balance Due", "Hardware Cost", "Labour Cost", "Total Cost", "Gross Margin", "Margin %", "Status"])
        orders = db.query(SalesOrder).all()
        for o in orders:
            expenses = db.query(ProjectExpense).filter(ProjectExpense.order_id == o.id).all()
            other_exp = sum(e.amount for e in expenses)
            total_cost = (o.hardware_cost or 0.0) + (o.installation_cost or 0.0) + other_exp
            gross_margin = o.total_amount - total_cost
            pct = round((gross_margin / o.total_amount * 100), 2) if o.total_amount > 0 else 0.0
            writer.writerow([
                o.order_number,
                o.customer.name if o.customer else "",
                o.capacity_kw,
                o.package_type,
                o.total_amount,
                o.advance_paid,
                o.balance_due,
                o.hardware_cost,
                o.installation_cost,
                total_cost,
                gross_margin,
                f"{pct}%",
                o.status
            ])
        filename = f"aarka_project_profitability_{date.today()}.csv"

    elif report_type == "inventory":
        writer.writerow(["SKU", "Product Name", "Category", "Quantity On Hand", "Reserved", "Available", "Reorder Level", "Unit Price", "Total Valuation", "Location", "Supplier"])
        items = db.query(InventoryItem).all()
        for it in items:
            writer.writerow([
                it.sku,
                it.product.name if it.product else "",
                it.product.category if it.product else "",
                it.quantity,
                it.reserved_quantity,
                max(0, it.quantity - it.reserved_quantity),
                it.reorder_level,
                it.unit_price,
                round(it.quantity * it.unit_price, 2),
                it.warehouse_location,
                it.supplier
            ])
        filename = f"aarka_inventory_valuation_{date.today()}.csv"

    elif report_type == "installations":
        writer.writerow(["Job Number", "Order Number", "Customer Name", "Customer Phone", "Technician", "Capacity (kW)", "Scheduled Date", "Status", "Labour Hours", "Testing Results"])
        installs = db.query(InstallationJob).all()
        for i in installs:
            writer.writerow([
                i.job_number,
                i.order.order_number if i.order else "",
                i.customer.name if i.customer else "",
                i.customer.phone if i.customer else "",
                i.technician.name if i.technician else "Unassigned",
                i.capacity_kw,
                i.scheduled_date,
                i.status,
                i.labour_hours,
                i.testing_results
            ])
        filename = f"aarka_installations_report_{date.today()}.csv"

    elif report_type == "warranties":
        writer.writerow(["Warranty Number", "Serial Number", "Product Name", "Customer Name", "Customer Phone", "Delivery Date", "Warranty Start", "Warranty End", "Status", "Coverage Terms"])
        warranties = db.query(WarrantyRecord).all()
        for w in warranties:
            writer.writerow([
                w.warranty_number,
                w.serial_number,
                w.product.name if w.product else "",
                w.customer.name if w.customer else "",
                w.customer.phone if w.customer else "",
                w.delivery_date,
                w.warranty_start,
                w.warranty_end,
                w.status,
                w.coverage_terms
            ])
        filename = f"aarka_warranty_records_{date.today()}.csv"

    else:
        # Default Receivables
        writer.writerow(["Order Number", "Customer Name", "Phone", "Total Invoiced", "Advance Paid", "Outstanding Balance Due", "Order Status"])
        orders = db.query(SalesOrder).filter(SalesOrder.balance_due > 0).all()
        for o in orders:
            writer.writerow([
                o.order_number,
                o.customer.name if o.customer else "",
                o.customer.phone if o.customer else "",
                o.total_amount,
                o.advance_paid,
                o.balance_due,
                o.status
            ])
        filename = f"aarka_receivables_report_{date.today()}.csv"

    return output.getvalue(), filename


@router.get("/export-csv")
def export_report_csv_query(
    report_type: str = Query("profitability"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    csv_data, filename = _generate_csv(report_type, db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/{report_type}")
def export_report_csv_path(
    report_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    csv_data, filename = _generate_csv(report_type, db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/director-summary")
def get_director_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orders = db.query(SalesOrder).all()
    total_rev = sum(o.total_amount for o in orders)
    active_projects = sum(1 for o in orders if o.status not in ["COMPLETED", "CANCELLED"])
    completed_installs = db.query(InstallationJob).filter(InstallationJob.status == "COMPLETED").count()
    inv_items = db.query(InventoryItem).all()
    inv_val = sum((it.quantity or 0) * (it.unit_price or 0.0) for it in inv_items)

    return {
        "total_revenue": round(total_rev, 2),
        "active_projects_count": active_projects,
        "completed_installations_count": completed_installs,
        "inventory_value": round(inv_val, 2),
    }


