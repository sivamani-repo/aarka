import secrets
import uuid
import os

import pytest
from fastapi.testclient import TestClient

from app.core.rbac import ROLE_DEPARTMENTS, seed_rbac_catalog
from app.core.security import get_password_hash
from app.database import SessionLocal
from app.models.user import Department, User
from main import app


client = TestClient(app)


def pytest_sessionstart(session):
    from app.config import settings

    if os.environ.get("AARKA_TEST_DATABASE") != "1" or "test" not in settings.db_name.lower():
        pytest.exit(
            "Integration tests require AARKA_TEST_DATABASE=1 and a DB_NAME containing 'test'.",
            returncode=2,
        )


@pytest.fixture(scope="session")
def test_admin_credentials():
    db = SessionLocal()
    try:
        seed_rbac_catalog(db)
        department_name = ROLE_DEPARTMENTS["Director / Super Admin"]
        department = db.query(Department).filter(Department.name == department_name).one()
        token = uuid.uuid4().hex
        email = f"test-admin-{token}@example.test"
        password = f"Aa1-{secrets.token_urlsafe(24)}"
        db.add(User(
            name="Automated Test Administrator",
            email=email,
            password_hash=get_password_hash(password),
            role="Director / Super Admin",
            phone=None,
            is_active=True,
            is_verified=True,
            employee_id=f"TEST-{token[:24]}",
            department_id=department.id,
        ))
        db.commit()
        return email, password
    finally:
        db.close()


@pytest.fixture(scope="session")
def auth_headers(test_admin_credentials):
    email, password = test_admin_credentials
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, f"Test administrator login failed: {response.text}"
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
