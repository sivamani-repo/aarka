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
from app.core.email import send_verification_email, send_password_reset_email
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication & Team"])


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
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
            "is_verified": user.is_verified
        }
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
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
            "is_verified": user.is_verified
        }
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
def create_staff_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Director / Admin"]))
):
    """
    Admin-controlled staff creation.
    - Restricted to Director / Admin.
    - Sets is_verified = True so internal staff can access their workspace immediately.
    """
    clean_email = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    hashed = get_password_hash(payload.password)
    user = User(
        name=payload.name.strip(),
        email=clean_email,
        password_hash=hashed,
        role=payload.role,
        phone=payload.phone.strip() if payload.phone else None,
        is_active=True,
        is_verified=True  # Pre-verified by administrator
    )
    db.add(user)
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
        user.name = payload.name.strip()
    if payload.email is not None:
        user.email = payload.email.lower().strip()
    if payload.role is not None:
        user.role = payload.role
    if payload.phone is not None:
        user.phone = payload.phone.strip()
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return user
