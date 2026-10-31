from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, AuditLog
from app.schemas.schemas import LoginRequest, TokenResponse, UserCreate, UserUpdate, UserOut
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.permissions import get_current_user, require_roles

router = APIRouter(prefix="/api/auth", tags=["Authentication & Team"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    token = create_access_token(subject=user.id, role=user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "phone": user.phone
        }
    }


@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    users = db.query(User).order_by(User.id.asc()).all()
    return users


@router.post("/users", response_model=UserOut)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Director / Admin"]))
):
    existing = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    hashed = get_password_hash(payload.password)
    user = User(
        name=payload.name,
        email=payload.email.lower().strip(),
        password_hash=hashed,
        role=payload.role,
        phone=payload.phone,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit = AuditLog(
        user_id=current_user.id,
        action="CREATE_USER",
        entity_type="USER",
        entity_id=user.id,
        details=f"Created user {user.email} with role {user.role}"
    )
    db.add(audit)
    db.commit()

    return user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Director / Admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.name is not None:
        user.name = payload.name
    if payload.email is not None:
        user.email = payload.email.lower().strip()
    if payload.role is not None:
        user.role = payload.role
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return user

