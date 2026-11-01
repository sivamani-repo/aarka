import pytest
from fastapi import HTTPException, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.rbac import (
    ACTIONS,
    DIRECTOR_ROLES,
    RESOURCES,
    effective_permissions,
    has_permission,
    request_permission,
    seed_rbac_catalog,
)
from app.routers.dashboard import _scope_dashboard_query, get_director_command_summary
from app.database import Base
from app.models.customer import Lead
from app.models.user import User, UserPermission


def _request(path: str, method: str = "GET") -> Request:
    return Request({
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
    })


def test_catalog_seeds_13_roles_and_is_idempotent():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        seed_rbac_catalog(session)
        seed_rbac_catalog(session)

        assert session.query(User).count() == 0
        assert session.query(User.__table__.metadata.tables["roles"]).count() == 13
        assert session.query(User.__table__.metadata.tables["permissions"]).count() == len(RESOURCES) * len(ACTIONS)
    finally:
        session.close()
        engine.dispose()


def test_role_and_individual_grants_are_enforced():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        seed_rbac_catalog(session)
        director = User(name="Director", email="director@example.com", role="Director / Super Admin")
        sales_employee = User(name="Sales Employee", email="sales@example.com", role="Sales Executive")
        customer = User(name="Customer", email="customer@example.com", role="Customer")
        session.add_all((director, sales_employee, customer))
        session.flush()

        assert has_permission(session, director, "finance", "VIEW")
        assert has_permission(session, sales_employee, "leads", "CREATE")
        assert not has_permission(session, sales_employee, "finance", "VIEW")
        assert not has_permission(session, customer, "customers", "VIEW")

        session.add(UserPermission(
            user_id=sales_employee.id,
            resource="finance",
            action="VIEW",
            granted_by=director.id,
        ))
        session.flush()
        assert has_permission(session, sales_employee, "finance", "VIEW")
        assert {"resource": "finance", "action": "VIEW"} in effective_permissions(session, sales_employee)
    finally:
        session.close()
        engine.dispose()


def test_all_director_role_names_have_full_module_access():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        seed_rbac_catalog(session)
        for role in DIRECTOR_ROLES:
            director = User(
                name=f"Director {role}",
                email=f"{role.replace('/', '-').replace(' ', '-')}@example.com",
                role=role,
            )
            session.add(director)
            session.flush()
            assert all(
                has_permission(session, director, resource, action)
                for resource in RESOURCES
                for action in ACTIONS
            )
    finally:
        session.close()
        engine.dispose()


def test_director_dashboard_endpoint_rejects_non_director_roles():
    employee = User(
        name="Finance Manager",
        email="finance@example.com",
        role="Finance Manager",
    )
    with pytest.raises(HTTPException) as error:
        get_director_command_summary(
            period="month",
            start_date=None,
            end_date=None,
            db=None,
            current_user=employee,
        )
    assert error.value.status_code == 403


def test_api_path_maps_to_required_resource_and_action():
    assert request_permission(_request("/api/leads", "GET")) == ("leads", "VIEW")
    assert request_permission(_request("/api/leads/12/qualify", "POST")) == ("leads", "APPROVE")
    assert request_permission(_request("/api/dispatches/12/assign", "POST")) == ("dispatches", "ASSIGN")
    assert request_permission(_request("/api/dispatches/12/confirm-delivery", "POST")) == ("dispatches", "EDIT")
    assert request_permission(_request("/api/service/tickets/12/replace-equipment", "POST")) == ("service", "APPROVE")
    assert request_permission(_request("/api/reports/director-summary", "GET")) == ("reports", "EXPORT")
    assert request_permission(_request("/api/auth/login", "POST")) is None
    assert request_permission(_request("/api/public/enquiry", "POST")) is None
    assert request_permission(_request("/api/subsidies/schemes", "GET")) is None
    assert request_permission(_request("/api/subsidies/calculate", "GET")) is None
    assert request_permission(_request("/api/subsidies/check-eligibility", "POST")) is None


def test_sales_dashboard_only_counts_assigned_and_legacy_owned_leads():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        user = User(
            name="Sales Employee",
            email="sales@example.com",
            role="Sales Executive",
        )
        other_user = User(
            name="Other Sales Employee",
            email="other@example.com",
            role="Sales Executive",
        )
        session.add_all((user, other_user))
        session.flush()
        session.add_all((
            Lead(
                lead_reference="OWNED",
                customer_name="Assigned Customer",
                phone="111",
                address="Assigned address",
                assigned_user_id=user.id,
            ),
            Lead(
                lead_reference="LEGACY",
                customer_name="Legacy Customer",
                phone="222",
                address="Legacy address",
                assigned_sales_rep=user.name,
            ),
            Lead(
                lead_reference="OTHER",
                customer_name="Other Customer",
                phone="333",
                address="Other address",
                assigned_user_id=other_user.id,
            ),
        ))
        session.flush()

        visible = _scope_dashboard_query(session, session.query(Lead), Lead, user).all()

        assert {lead.lead_reference for lead in visible} == {"OWNED", "LEGACY"}
    finally:
        session.close()
        engine.dispose()
