from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory import Supplier
from app.schemas.schemas import SupplierCreate, SupplierOut
from app.core.permissions import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers & Vendors"])


@router.get("", response_model=List[SupplierOut])
def list_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    suppliers = db.query(Supplier).order_by(Supplier.name.asc()).all()
    return suppliers


@router.post("", response_model=SupplierOut)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    supp = Supplier(
        name=payload.name.strip(),
        contact_person=payload.contact_person,
        phone=payload.phone.strip(),
        email=payload.email.strip() if payload.email else None,
        address=payload.address,
        category=payload.category,
        lead_time_days=payload.lead_time_days,
        status="ACTIVE"
    )
    db.add(supp)
    db.commit()
    db.refresh(supp)
    return supp

