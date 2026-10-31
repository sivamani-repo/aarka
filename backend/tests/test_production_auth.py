import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import get_db, SessionLocal
from app.models.user import User

client = TestClient(app)

def test_full_auth_lifecycle():
    test_email = "authtest_user@aarka.com"
    initial_password = "SecurePassword123"
    updated_password = "NewSecurePassword456"

    # Cleanup if previously exists
    db = SessionLocal()
    existing = db.query(User).filter(User.email == test_email).first()
    if existing:
        db.delete(existing)
        db.commit()
    db.close()

    # 1. Password strength validation checks
    resp_weak = client.post("/api/auth/register", json={
        "name": "Weak User",
        "email": test_email,
        "password": "short",
        "confirm_password": "short"
    })
    assert resp_weak.status_code == 422

    # Password mismatch check
    resp_mismatch = client.post("/api/auth/register", json={
        "name": "Mismatch User",
        "email": test_email,
        "password": initial_password,
        "confirm_password": "DifferentPassword123"
    })
    assert resp_mismatch.status_code == 422

    # 2. Valid Registration
    reg_payload = {
        "name": "Auth Test User",
        "email": test_email,
        "phone": "+91 9876543210",
        "password": initial_password,
        "confirm_password": initial_password
    }
    reg_resp = client.post("/api/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert reg_data["email"] == test_email
    assert reg_data["requires_verification"] is True
    assert "password_hash" not in reg_data

    # Verify user in DB has safe role and is_verified=False
    db = SessionLocal()
    user_db = db.query(User).filter(User.email == test_email).first()
    assert user_db is not None
    assert user_db.role == "Customer"  # Safe default role enforced
    assert user_db.is_verified is False
    v_token = user_db.verification_token
    assert v_token is not None
    db.close()

    # 3. Duplicate Registration Check
    dup_resp = client.post("/api/auth/register", json=reg_payload)
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"].lower()

    # 4. Attempt login before email verification -> must be 403 Forbidden
    login_unverified = client.post("/api/auth/login", json={
        "email": test_email,
        "password": initial_password
    })
    assert login_unverified.status_code == 403
    assert "not verified" in login_unverified.json()["detail"].lower()

    # 6. Verify with invalid token
    invalid_verify = client.get("/api/auth/verify-email?token=invalid_dummy_token_12345")
    assert invalid_verify.status_code == 400

    # 7. Verify with valid token
    valid_verify = client.get(f"/api/auth/verify-email?token={v_token}")
    assert valid_verify.status_code == 200
    assert valid_verify.json()["verified"] is True

    # 8. Login after email verification -> must succeed
    login_verified = client.post("/api/auth/login", json={
        "email": test_email,
        "password": initial_password
    })
    assert login_verified.status_code == 200
    login_data = login_verified.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == test_email
    assert login_data["user"]["is_verified"] is True
    assert login_data["user"]["role"] == "Customer"
    jwt_token = login_data["access_token"]

    # 9. Verify authenticated profile via /api/auth/me
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {jwt_token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == test_email

    # 10. Forgot Password request
    forgot_resp = client.post("/api/auth/forgot-password", json={"email": test_email})
    assert forgot_resp.status_code == 200

    # Retrieve reset token from DB
    db = SessionLocal()
    user_db = db.query(User).filter(User.email == test_email).first()
    reset_token = user_db.reset_password_token
    assert reset_token is not None
    db.close()

    # 11. Reset Password with invalid token
    bad_reset = client.post("/api/auth/reset-password", json={
        "token": "fake_token",
        "password": updated_password,
        "confirm_password": updated_password
    })
    assert bad_reset.status_code == 400

    # Reset Password with valid token
    good_reset = client.post("/api/auth/reset-password", json={
        "token": reset_token,
        "password": updated_password,
        "confirm_password": updated_password
    })
    assert good_reset.status_code == 200

    # 12. Old password should now fail
    old_pw_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": initial_password
    })
    assert old_pw_login.status_code == 401

    # New password should succeed
    new_pw_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": updated_password
    })
    assert new_pw_login.status_code == 200

    # 13. Test Google Auth endpoint rejects invalid/fake credential tokens
    google_bad_resp = client.post("/api/auth/google", json={
        "credential": "invalid.google.jwt.token"
    })
    assert google_bad_resp.status_code in (400, 401)

    # Clean up test user
    db = SessionLocal()
    u = db.query(User).filter(User.email == test_email).first()
    if u:
        db.delete(u)
        db.commit()
    db.close()
