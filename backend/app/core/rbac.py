from typing import Dict, Optional, Set, Tuple

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user, oauth2_scheme
from app.database import get_db
from app.models.user import (
    Department,
    Permission,
    Role,
    RolePermission,
    User,
    UserPermission,
)

VIEW = "VIEW"
CREATE = "CREATE"
EDIT = "EDIT"
DELETE = "DELETE"
APPROVE = "APPROVE"
ASSIGN = "ASSIGN"
EXPORT = "EXPORT"
MANAGE = "MANAGE"
ACTIONS = (VIEW, CREATE, EDIT, DELETE, APPROVE, ASSIGN, EXPORT, MANAGE)

DEPARTMENTS = (
    "Executive",
    "Operations",
    "Sales",
    "Warehouse & Inventory",
    "Finance & Accounts",
    "Installation",
    "Service & Maintenance",
    "Customer Support",
)

ROLE_DEPARTMENTS = {
    "Director / Super Admin": "Executive",
    "Operations Manager": "Operations",
    "Sales Manager": "Sales",
    "Warehouse Manager": "Warehouse & Inventory",
    "Finance Manager": "Finance & Accounts",
    "Installation Manager": "Installation",
    "Service Manager": "Service & Maintenance",
    "Sales Executive": "Sales",
    "Site Survey Engineer": "Installation",
    "Solar Technician": "Installation",
    "Dispatch Staff": "Warehouse & Inventory",
    "Storekeeper": "Warehouse & Inventory",
    "Support Executive": "Customer Support",
}

ROLE_DESCRIPTIONS = {
    "Director / Super Admin": "Company-wide administration and oversight.",
    "Operations Manager": "Coordinates cross-department project operations.",
    "Sales Manager": "Leads sales and customer management.",
    "Warehouse Manager": "Manages inventory, suppliers, and dispatch.",
    "Finance Manager": "Manages payments and financial records.",
    "Installation Manager": "Coordinates installation projects and field teams.",
    "Service Manager": "Manages service, complaints, and warranty workflows.",
    "Sales Executive": "Handles assigned leads and sales follow-ups.",
    "Site Survey Engineer": "Performs assigned solar site surveys.",
    "Solar Technician": "Updates assigned installation work.",
    "Dispatch Staff": "Prepares and updates authorized dispatches.",
    "Storekeeper": "Maintains warehouse stock records.",
    "Support Executive": "Handles assigned customer service requests.",
}

RESOURCES = (
    "dashboard",
    "employees",
    "leads",
    "customers",
    "surveys",
    "products",
    "bom",
    "quotations",
    "orders",
    "payments",
    "inventory",
    "serials",
    "dispatches",
    "technicians",
    "installations",
    "warranties",
    "service",
    "suppliers",
    "finance",
    "subsidies",
    "reports",
    "uploads",
    "settings",
)

ROLE_ACCESS: Dict[str, Dict[str, Set[str]]] = {
    "Operations Manager": {
        "dashboard": {VIEW},
        "leads": {VIEW},
        "customers": {VIEW},
        "surveys": {VIEW, EDIT, APPROVE, ASSIGN},
        "products": {VIEW},
        "quotations": {VIEW},
        "orders": {VIEW, EDIT},
        "inventory": {VIEW},
        "dispatches": {VIEW, EDIT, ASSIGN},
        "installations": {VIEW, EDIT, ASSIGN, APPROVE},
        "warranties": {VIEW},
        "service": {VIEW, EDIT, ASSIGN},
        "reports": {VIEW, EXPORT},
    },
    "Sales Manager": {
        "dashboard": {VIEW},
        "leads": {VIEW, CREATE, EDIT, DELETE, ASSIGN, APPROVE},
        "customers": {VIEW, CREATE, EDIT, ASSIGN},
        "surveys": {VIEW, CREATE, EDIT},
        "products": {VIEW},
        "bom": {VIEW},
        "quotations": {VIEW, CREATE, EDIT, APPROVE, ASSIGN},
        "orders": {VIEW, CREATE, EDIT},
        "reports": {VIEW, EXPORT},
    },
    "Warehouse Manager": {
        "dashboard": {VIEW},
        "inventory": {VIEW, CREATE, EDIT, APPROVE},
        "serials": {VIEW, CREATE, EDIT},
        "suppliers": {VIEW, CREATE, EDIT},
        "dispatches": {VIEW, CREATE, EDIT, APPROVE, ASSIGN},
        "orders": {VIEW},
        "reports": {VIEW, EXPORT},
    },
    "Finance Manager": {
        "dashboard": {VIEW},
        "payments": {VIEW, CREATE, EDIT, APPROVE},
        "finance": {VIEW, CREATE, EDIT, APPROVE},
        "orders": {VIEW},
        "reports": {VIEW, EXPORT},
    },
    "Installation Manager": {
        "dashboard": {VIEW},
        "customers": {VIEW},
        "surveys": {VIEW, EDIT, APPROVE, ASSIGN},
        "orders": {VIEW},
        "inventory": {VIEW, ASSIGN},
        "serials": {VIEW},
        "technicians": {VIEW, ASSIGN, MANAGE},
        "installations": {VIEW, CREATE, EDIT, ASSIGN, APPROVE},
        "warranties": {VIEW},
        "reports": {VIEW, EXPORT},
    },
    "Service Manager": {
        "dashboard": {VIEW},
        "customers": {VIEW},
        "technicians": {VIEW, ASSIGN},
        "warranties": {VIEW, CREATE, EDIT, APPROVE, ASSIGN},
        "service": {VIEW, CREATE, EDIT, APPROVE, ASSIGN},
        "reports": {VIEW, EXPORT},
    },
    "Sales Executive": {
        "dashboard": {VIEW},
        "leads": {VIEW, CREATE, EDIT},
        "customers": {VIEW, CREATE, EDIT},
        "surveys": {VIEW},
        "products": {VIEW},
        "bom": {VIEW},
        "quotations": {VIEW, CREATE, EDIT},
        "orders": {VIEW},
    },
    "Site Survey Engineer": {
        "dashboard": {VIEW},
        "customers": {VIEW},
        "surveys": {VIEW, CREATE, EDIT},
        "uploads": {VIEW, CREATE},
    },
    "Solar Technician": {
        "dashboard": {VIEW},
        "customers": {VIEW},
        "serials": {VIEW, CREATE},
        "installations": {VIEW, EDIT},
        "uploads": {VIEW, CREATE},
    },
    "Dispatch Staff": {
        "dashboard": {VIEW},
        "inventory": {VIEW},
        "serials": {VIEW, CREATE},
        "dispatches": {VIEW, EDIT},
        "uploads": {VIEW, CREATE},
    },
    "Storekeeper": {
        "dashboard": {VIEW},
        "inventory": {VIEW, CREATE, EDIT},
        "serials": {VIEW, CREATE, EDIT},
        "suppliers": {VIEW},
    },
    "Support Executive": {
        "dashboard": {VIEW},
        "customers": {VIEW},
        "warranties": {VIEW},
        "service": {VIEW, CREATE, EDIT},
        "uploads": {VIEW, CREATE},
    },
}

DIRECTOR_ROLES = {
    "Director / Super Admin",
    "Director / Admin",
    "Director",
    "Admin",
}

LEGACY_ROLES = {
    "Director / Admin": "Director / Super Admin",
    "Director": "Director / Super Admin",
    "Admin": "Director / Super Admin",
    "Sales Representative": "Sales Executive",
    "Site Surveyor": "Site Survey Engineer",
    "Survey Technician": "Site Survey Engineer",
    "Installation Engineer": "Solar Technician",
    "Installation Technician": "Solar Technician",
    "Service Coordinator": "Support Executive",
    "Finance / Accounts": "Finance Manager",
}

API_RESOURCES = {
    "dashboard": "dashboard",
    "leads": "leads",
    "customers": "customers",
    "surveys": "surveys",
    "products": "products",
    "bom": "bom",
    "quotations": "quotations",
    "orders": "orders",
    "payments": "payments",
    "inventory": "inventory",
    "serials": "serials",
    "dispatches": "dispatches",
    "technicians": "technicians",
    "installations": "installations",
    "warranties": "warranties",
    "service": "service",
    "suppliers": "suppliers",
    "finance": "finance",
    "subsidies": "subsidies",
    "reports": "reports",
    "uploads": "uploads",
    "settings": "settings",
}

SPECIAL_ACTIONS = {
    "approve": APPROVE,
    "qualify": APPROVE,
    "complete": APPROVE,
    "resolve": APPROVE,
    "confirm": APPROVE,
    "confirm-delivery": EDIT,
    "verify": APPROVE,
    "review": APPROVE,
    "trigger": APPROVE,
    "adjust": APPROVE,
    "assign": ASSIGN,
    "reserve-materials": ASSIGN,
    "send": EDIT,
    "accept": APPROVE,
    "replace-equipment": APPROVE,
    "replacement": APPROVE,
}


def canonical_role(role: str) -> str:
    return LEGACY_ROLES.get(role, role)


def get_role_access(role: str) -> Dict[str, Set[str]]:
    canonical = canonical_role(role)
    if canonical == "Director / Super Admin":
        return {resource: set(ACTIONS) for resource in RESOURCES}
    return ROLE_ACCESS.get(canonical, {})


def seed_rbac_catalog(db: Session) -> None:
    department_ids: Dict[str, int] = {}
    for department_name in DEPARTMENTS:
        department = db.query(Department).filter(Department.name == department_name).first()
        if department is None:
            department = Department(name=department_name)
            db.add(department)
            db.flush()
        department_ids[department_name] = department.id

    for role_name, department_name in ROLE_DEPARTMENTS.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if role is None:
            db.add(Role(
                name=role_name,
                department_id=department_ids[department_name],
                description=ROLE_DESCRIPTIONS[role_name],
            ))

    for resource in RESOURCES:
        for action in ACTIONS:
            if db.get(Permission, {"resource": resource, "action": action}) is None:
                db.add(Permission(resource=resource, action=action))
    db.flush()

    for role_name, resources in ROLE_ACCESS.items():
        for resource, actions in resources.items():
            for action in actions:
                key = {"role_name": role_name, "resource": resource, "action": action}
                if db.get(RolePermission, key) is None:
                    db.add(RolePermission(**key))

    for resource in RESOURCES:
        for action in ACTIONS:
            key = {"role_name": "Director / Super Admin", "resource": resource, "action": action}
            if db.get(RolePermission, key) is None:
                db.add(RolePermission(**key))
    db.commit()


def has_permission(db: Session, user: User, resource: str, action: str) -> bool:
    if user.role in DIRECTOR_ROLES:
        return True
    role = canonical_role(user.role)
    role_grant = db.get(
        RolePermission,
        {"role_name": role, "resource": resource, "action": action},
    )
    if role_grant is not None:
        return True
    return db.get(
        UserPermission,
        {"user_id": user.id, "resource": resource, "action": action},
    ) is not None


def effective_permissions(db: Session, user: User) -> list[dict]:
    if user.role in DIRECTOR_ROLES:
        return [
            {"resource": resource, "action": action}
            for resource in RESOURCES
            for action in ACTIONS
        ]
    role = canonical_role(user.role)
    permissions: Set[Tuple[str, str]] = {
        (grant.resource, grant.action)
        for grant in db.query(RolePermission).filter(RolePermission.role_name == role).all()
    }
    permissions.update(
        (grant.resource, grant.action)
        for grant in db.query(UserPermission).filter(UserPermission.user_id == user.id).all()
    )
    return [
        {"resource": resource, "action": action}
        for resource, action in sorted(permissions)
    ]


def request_permission(request: Request) -> Optional[Tuple[str, str]]:
    path = request.url.path.strip("/")
    if not path.startswith("api/"):
        return None

    segments = path.split("/")
    if len(segments) < 2:
        return None
    section = segments[1]

    if section == "auth":
        if len(segments) == 3 and segments[2] == "me":
            return ("profile", VIEW)
        if len(segments) == 3 and segments[2] in {"roles", "permissions"}:
            return ("catalog", VIEW)
        if len(segments) >= 3 and segments[2] == "users":
            return ("employees", MANAGE if request.method in {"POST", "PUT", "PATCH", "DELETE"} else VIEW)
        return None

    if section == "public":
        return None
    if section == "health":
        return None
    if section == "subsidies" and len(segments) >= 3:
        if request.method == "GET" and segments[2] in {"schemes", "calculate"}:
            return None
        if request.method == "POST" and segments[2] == "check-eligibility":
            return None
    resource = API_RESOURCES.get(section)
    if resource is None:
        return ("unknown", VIEW)

    trailing = segments[2:]
    action = VIEW if request.method in {"GET", "HEAD"} else {
        "POST": CREATE,
        "PUT": EDIT,
        "PATCH": EDIT,
        "DELETE": DELETE,
    }.get(request.method, MANAGE)

    for segment in trailing:
        if segment in SPECIAL_ACTIONS:
            action = SPECIAL_ACTIONS[segment]
    if section == "reports" and request.method == "GET":
        action = EXPORT
    return (resource, action)


def authorize_api_request(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> None:
    permission = request_permission(request)
    if permission is None:
        return

    user = get_current_user(token=token, db=db)
    resource, action = permission
    if resource == "profile":
        return
    if resource == "catalog":
        return
    if resource == "unknown" or not has_permission(db, user, resource, action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {action} access to {resource}.",
        )
