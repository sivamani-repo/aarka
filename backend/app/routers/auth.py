import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, AuditLog
from app.schemas.schemas import (
    LoginRequest,
    RegisterRequest,
    GoogleAuthRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserUpdate,
    UserOut,
)
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.permissions import get_current_user, require_roles
from app.core.rbac import (
    ACTIONS,
    DIRECTOR_ROLES,
    ROLE_DEPARTMENTS,
    RESOURCES,
    canonical_role,
    effective_permissions,
)
from app.core.email import send_verification_email, send_password_reset_email
from app.config import settings
from app.models.user import Department, UserPermission

router = APIRouter(prefix="/api/auth", tags=["Authentication & Team"])


def _serialize_user(user: User, db: Session) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": canonical_role(user.role),
        "phone": user.phone,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "employee_id": user.employee_id,
        "department": user.department_name,
        "reporting_manager_id": user.reporting_manager_id,
        "permissions": effective_permissions(db, user),
        "additional_permissions": [
            {"resource": grant.resource, "action": grant.action}
            for grant in db.query(UserPermission).filter(UserPermission.user_id == user.id).all()
        ],
    }


def _permission_pairs(values: List[str]) -> set[tuple[str, str]]:
    allowed_resources = set(RESOURCES)
    allowed_actions = set(ACTIONS)
    pairs = set()
    for value in values:
        resource, separator, action = value.partition(":")
        resource = resource.strip().lower()
        action = action.strip().upper()
        if not separator or resource not in allowed_resources or action not in allowed_actions:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid permission '{value}'. Use a valid resource:ACTION pair.",
            )
        pairs.add((resource, action))
    return pairs


def _validate_reporting_manager(db: Session, manager_id: Optional[int], user_id: Optional[int] = None):
    if manager_id is None:
        return
    if manager_id == user_id:
        raise HTTPException(status_code=400, detail="An employee cannot report to themselves.")
    manager = db.query(User).filter(User.id == manager_id, User.is_active.is_(True)).first()
    if manager is None:
        raise HTTPException(status_code=404, detail="Reporting manager not found or inactive.")
    canonical_manager_role = canonical_role(manager.role)
    if canonical_manager_role not in DIRECTOR_ROLES and not canonical_manager_role.endswith("Manager"):
        raise HTTPException(status_code=400, detail="Reporting manager must be a manager or director.")


def _ensure_director_remains_active(db: Session, user: User, is_active: Optional[bool]):
    if is_active is not False or canonical_role(user.role) != "Director / Super Admin" or not user.is_active:
        return
    active_directors = db.query(User).filter(User.is_active.is_(True)).all()
    if sum(canonical_role(candidate.role) == "Director / Super Admin" for candidate in active_directors) <= 1:
        raise HTTPException(status_code=400, detail="At least one active Director / Super Admin must remain.")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Public registration endpoint.
    - Validates email format and password strength via Pydantic.
    - Rejects existing emails.
    - Assigns safe default role 'Customer' (never trusts client-supplied roles).
    - Sets is_verified = False.
    - Generates cryptographic verification token and sends verification email.
    """
    clean_email = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.verification_token_expire_hours)
    hashed_pw = get_password_hash(payload.password)

    user = User(
        name=payload.name.strip(),
        email=clean_email,
        phone=payload.phone.strip() if payload.phone else None,
        password_hash=hashed_pw,
        role="Customer",  # Enforce safe default role
        is_active=True,
        is_verified=False,
        verification_token=token,
        verification_token_expires_at=expires_at,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Deliver verification email
    try:
        send_verification_email(user.email, user.name, token)
    except Exception as e:
        # Never claim email succeeded if delivery fails
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account created, but failed to send verification email: {str(e)}"
        )

    audit = AuditLog(
        user_id=user.id,
        action="REGISTER",
        entity_type="USER",
        entity_id=user.id,
        details=f"Public registration for {user.email}"
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Registration successful! Please check your email to verify your account.",
        "email": user.email,
        "requires_verification": True
    }


@router.get("/verify-email")
def verify_email(token: str = Query(..., description="Email verification token"), db: Session = Depends(get_db)):
    """
    Validates email verification token and marks account as verified.
    """
    if not token or len(token.strip()) < 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token.")

    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification link."
        )

    if user.verification_token_expires_at and user.verification_token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please request a new verification email."
        )

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires_at = None
    db.commit()

    audit = AuditLog(
        user_id=user.id,
        action="VERIFY_EMAIL",
        entity_type="USER",
        entity_id=user.id,
        details=f"Email verified for {user.email}"
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Email successfully verified! You can now log in to AARKA.",
        "verified": True
    }


@router.post("/resend-verification")
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    """
    Resends a verification email. Prevents account enumeration by returning a generic response.
    """
    clean_email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()

    if not user:
        return {"message": "If an unverified account exists with that email, a verification link has been sent."}

    if user.is_verified:
        return {"message": "This account is already verified. You can log in.", "already_verified": True}

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.verification_token_expire_hours)
    user.verification_token = token
    user.verification_token_expires_at = expires_at
    db.commit()

    try:
        send_verification_email(user.email, user.name, token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deliver verification email: {str(e)}"
        )

    return {"message": "Verification link has been sent to your email address."}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Email & password login.
    - Verifies password hash.
    - Checks account active status.
    - Enforces email verification.
    - Issues AARKA JWT session.
    """
    clean_email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()

    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account has been deactivated. Please contact your administrator."
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address not verified. Please verify your email before logging in."
        )

    token = create_access_token(subject=user.id, role=user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _serialize_user(user, db),
    }


@router.post("/google", response_model=TokenResponse)
def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Google OAuth 2.0 / Google Identity Services authentication.
    - Verifies Google token signature, issuer, audience, and expiration.
    - Requires verified email claim from Google.
    - Implements safe account linking if user exists.
    - Assigns safe default role 'Customer' for new accounts.
    - Issues AARKA JWT session.
    """
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        # Verify Google ID token
        id_info = id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            settings.google_client_id  # Validates audience against Google Client ID if configured
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google authentication failed: {str(e)}"
        )

    # Validate issuer
    issuer = id_info.get("iss")
    if issuer not in ["accounts.google.com", "https://accounts.google.com"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google token issuer."
        )

    email = id_info.get("email")
    email_verified = id_info.get("email_verified")
    google_sub = id_info.get("sub")
    name = id_info.get("name") or id_info.get("given_name") or "Google User"

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account did not return an email address."
        )

    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google email address is not verified by Google."
        )

    clean_email = email.lower().strip()

    # Safe Account Linking: Check by google_sub first, then by email
    user = db.query(User).filter(User.google_sub == google_sub).first()
    if not user:
        user = db.query(User).filter(User.email == clean_email).first()
        if user:
            # Link existing account to Google
            user.google_sub = google_sub
            user.is_verified = True  # Google verified email
        else:
            # Create new user with safe default role
            user = User(
                name=name,
                email=clean_email,
                password_hash=None,  # No password for Google-only login
                role="Customer",
                google_sub=google_sub,
                is_active=True,
                is_verified=True,
            )
            db.add(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account has been deactivated."
        )

    db.commit()
    db.refresh(user)

    audit = AuditLog(
        user_id=user.id,
        action="GOOGLE_LOGIN",
        entity_type="USER",
        entity_id=user.id,
        details=f"Google OAuth sign-in for {user.email}"
    )
    db.add(audit)
    db.commit()

    token = create_access_token(subject=user.id, role=user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _serialize_user(user, db),
    }


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Password recovery initiation.
    - Generates secure short-lived reset token.
    - Delivers reset link via email.
    - Always returns generic message to prevent account enumeration.
    """
    clean_email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()

    if user and user.is_active:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.reset_token_expire_minutes)
        user.reset_password_token = token
        user.reset_password_token_expires_at = expires_at
        db.commit()

        try:
            send_password_reset_email(user.email, user.name, token)
        except Exception:
            # Do not reveal email delivery internals to public client
            pass

    return {
        "message": "If an account exists with this email address, password reset instructions have been sent."
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Completes password reset using verified token.
    """
    if not payload.token or len(payload.token.strip()) < 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password reset token.")

    user = db.query(User).filter(User.reset_password_token == payload.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset link."
        )

    if user.reset_password_token_expires_at and user.reset_password_token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired. Please request a new link."
        )

    user.password_hash = get_password_hash(payload.password)
    user.reset_password_token = None
    user.reset_password_token_expires_at = None
    db.commit()

    audit = AuditLog(
        user_id=user.id,
        action="RESET_PASSWORD",
        entity_type="USER",
        entity_id=user.id,
        details=f"Password reset completed for {user.email}"
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Password successfully updated! You can now log in with your new password."
    }


# ================= PROFILE & ADMIN STAFF MANAGEMENT =================

@router.get("/me", response_model=UserOut)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _serialize_user(current_user, db)


@router.get("/roles")
def list_roles(db: Session = Depends(get_db)):
    from app.models.user import Role

    return [
        {
            "name": role.name,
            "department": role.department.name if role.department else None,
            "description": role.description,
        }
        for role in db.query(Role).order_by(Role.name.asc()).all()
    ]


@router.get("/permissions")
def list_permissions():
    return [
        {"resource": resource, "action": action}
        for resource in RESOURCES
        for action in ACTIONS
    ]


@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    users = db.query(User).filter(User.role != "Customer").order_by(User.id.asc()).all()
    return [_serialize_user(user, db) for user in users]


@router.post("/users", response_model=UserOut)
def create_staff_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Director / Admin", "Director / Super Admin"]))
):
    if payload.role not in ROLE_DEPARTMENTS:
        raise HTTPException(status_code=422, detail="Select one of the configured AARKA employee roles.")
    clean_email = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    _validate_reporting_manager(db, payload.reporting_manager_id)
    hashed = get_password_hash(payload.password)
    department = db.query(Department).filter(
        Department.name == ROLE_DEPARTMENTS[payload.role]
    ).one()
    user = User(
        name=payload.name.strip(),
        email=clean_email,
        password_hash=hashed,
        role=payload.role,
        department_id=department.id,
        reporting_manager_id=payload.reporting_manager_id,
        phone=payload.phone.strip() if payload.phone else None,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()
    user.employee_id = f"AARKA-EMP-{user.id:06d}"
    for resource, action in _permission_pairs(payload.permissions):
        db.add(UserPermission(
            user_id=user.id,
            resource=resource,
            action=action,
            granted_by=current_user.id,
        ))
    db.commit()
    db.refresh(user)

    audit = AuditLog(
        user_id=current_user.id,
        action="CREATE_STAFF_USER",
        entity_type="USER",
        entity_id=user.id,
        details=f"Admin {current_user.email} created staff account {user.email} as {user.role}"
    )
    db.add(audit)
    db.commit()

    return _serialize_user(user, db)


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Director / Admin", "Director / Super Admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id and (
        payload.role is not None or payload.permissions is not None or payload.is_active is False
    ):
        raise HTTPException(status_code=400, detail="You cannot change your own role, permissions, or account status.")
    if payload.role is not None and payload.role not in ROLE_DEPARTMENTS:
        raise HTTPException(status_code=422, detail="Select one of the configured AARKA employee roles.")
    if payload.email is not None:
        clean_email = payload.email.lower().strip()
        duplicate = db.query(User).filter(User.email == clean_email, User.id != user.id).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="User with this email already exists.")
        user.email = clean_email
    _validate_reporting_manager(db, payload.reporting_manager_id, user.id)
    _ensure_director_remains_active(db, user, payload.is_active)

    if payload.name is not None:
        user.name = payload.name.strip()
    if payload.role is not None:
        user.role = payload.role
        department = db.query(Department).filter(
            Department.name == ROLE_DEPARTMENTS[payload.role]
        ).one()
        user.department_id = department.id
    if "reporting_manager_id" in payload.model_fields_set:
        user.reporting_manager_id = payload.reporting_manager_id
    if payload.phone is not None:
        user.phone = payload.phone.strip()
    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.permissions is not None:
        db.query(UserPermission).filter(UserPermission.user_id == user.id).delete()
        for resource, action in _permission_pairs(payload.permissions):
            db.add(UserPermission(
                user_id=user.id,
                resource=resource,
                action=action,
                granted_by=current_user.id,
            ))

    db.commit()
    db.refresh(user)
    audit = AuditLog(
        user_id=current_user.id,
        action="UPDATE_STAFF_USER",
        entity_type="USER",
        entity_id=user.id,
        details=f"Admin {current_user.email} updated staff account {user.email}",
    )
    db.add(audit)
    db.commit()
    return _serialize_user(user, db)
