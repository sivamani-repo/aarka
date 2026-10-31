"""add role-based access control and employee profiles

Revision ID: 2d43cbd7a81f
Revises: 9a3e5d10e060
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2d43cbd7a81f"
down_revision: Union[str, Sequence[str], None] = "9a3e5d10e060"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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

ROLE_DEPARTMENTS = (
    ("Director / Super Admin", "Executive", "Company-wide administration and oversight."),
    ("Operations Manager", "Operations", "Coordinates cross-department project operations."),
    ("Sales Manager", "Sales", "Leads sales and customer management."),
    ("Warehouse Manager", "Warehouse & Inventory", "Manages inventory, suppliers, and dispatch."),
    ("Finance Manager", "Finance & Accounts", "Manages payments and financial records."),
    ("Installation Manager", "Installation", "Coordinates installation projects and field teams."),
    ("Service Manager", "Service & Maintenance", "Manages service, complaints, and warranty workflows."),
    ("Sales Executive", "Sales", "Handles assigned leads and sales follow-ups."),
    ("Site Survey Engineer", "Installation", "Performs assigned solar site surveys."),
    ("Solar Technician", "Installation", "Updates assigned installation work."),
    ("Dispatch Staff", "Warehouse & Inventory", "Prepares and updates authorized dispatches."),
    ("Storekeeper", "Warehouse & Inventory", "Maintains warehouse stock records."),
    ("Support Executive", "Customer Support", "Handles assigned customer service requests."),
)

RESOURCES = (
    "dashboard", "employees", "leads", "customers", "surveys", "products", "bom",
    "quotations", "orders", "payments", "inventory", "serials", "dispatches",
    "technicians", "installations", "warranties", "service", "suppliers",
    "finance", "subsidies", "reports", "uploads", "settings",
)
ACTIONS = ("VIEW", "CREATE", "EDIT", "DELETE", "APPROVE", "ASSIGN", "EXPORT", "MANAGE")


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
    )
    op.create_table(
        "roles",
        sa.Column("name", sa.String(length=80), primary_key=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id")),
        sa.Column("description", sa.String(length=255), nullable=False),
    )
    op.create_table(
        "permissions",
        sa.Column("resource", sa.String(length=80), primary_key=True),
        sa.Column("action", sa.String(length=20), primary_key=True),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_name", sa.String(length=80), sa.ForeignKey("roles.name", ondelete="CASCADE"), primary_key=True),
        sa.Column("resource", sa.String(length=80), primary_key=True),
        sa.Column("action", sa.String(length=20), primary_key=True),
        sa.ForeignKeyConstraint(
            ["resource", "action"],
            ["permissions.resource", "permissions.action"],
            ondelete="CASCADE",
        ),
    )
    op.create_table(
        "user_permissions",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("resource", sa.String(length=80), primary_key=True),
        sa.Column("action", sa.String(length=20), primary_key=True),
        sa.Column("granted_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["resource", "action"],
            ["permissions.resource", "permissions.action"],
            ondelete="CASCADE",
        ),
    )

    op.add_column("users", sa.Column("employee_id", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("department_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("reporting_manager_id", sa.Integer(), nullable=True))
    op.create_index("ix_users_employee_id", "users", ["employee_id"], unique=True)
    op.create_foreign_key(
        "fk_users_department_id_departments",
        "users",
        "departments",
        ["department_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_users_reporting_manager_id_users",
        "users",
        "users",
        ["reporting_manager_id"],
        ["id"],
    )

    for table_name in (
        "customers",
        "leads",
        "site_surveys",
        "installations",
        "dispatches",
        "service_tickets",
    ):
        column_name = "assigned_user_id"
        op.add_column(table_name, sa.Column(column_name, sa.Integer(), nullable=True))
        op.create_index(
            f"ix_{table_name}_assigned_user_id",
            table_name,
            [column_name],
        )
        op.create_foreign_key(
            f"fk_{table_name}_assigned_user_id_users",
            table_name,
            "users",
            [column_name],
            ["id"],
        )

    departments = sa.table(
        "departments",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String()),
    )
    op.bulk_insert(
        departments,
        [{"id": index, "name": name} for index, name in enumerate(DEPARTMENTS, start=1)],
    )
    op.execute(
        "SELECT setval(pg_get_serial_sequence('departments', 'id'), "
        "(SELECT COALESCE(MAX(id), 1) FROM departments))"
    )

    roles = sa.table(
        "roles",
        sa.column("name", sa.String()),
        sa.column("department_id", sa.Integer()),
        sa.column("description", sa.String()),
    )
    department_ids = {name: index for index, name in enumerate(DEPARTMENTS, start=1)}
    op.bulk_insert(
        roles,
        [
            {"name": name, "department_id": department_ids[department], "description": description}
            for name, department, description in ROLE_DEPARTMENTS
        ],
    )

    permissions = sa.table(
        "permissions",
        sa.column("resource", sa.String()),
        sa.column("action", sa.String()),
    )
    op.bulk_insert(
        permissions,
        [{"resource": resource, "action": action} for resource in RESOURCES for action in ACTIONS],
    )

    op.execute(
        """
        UPDATE users
        SET role = CASE role
            WHEN 'Director / Admin' THEN 'Director / Super Admin'
            WHEN 'Director' THEN 'Director / Super Admin'
            WHEN 'Admin' THEN 'Director / Super Admin'
            WHEN 'Sales Representative' THEN 'Sales Executive'
            WHEN 'Site Surveyor' THEN 'Site Survey Engineer'
            WHEN 'Survey Technician' THEN 'Site Survey Engineer'
            WHEN 'Installation Engineer' THEN 'Solar Technician'
            WHEN 'Installation Technician' THEN 'Solar Technician'
            WHEN 'Service Coordinator' THEN 'Support Executive'
            WHEN 'Finance / Accounts' THEN 'Finance Manager'
            ELSE role
        END
        """
    )
    op.execute(
        """
        UPDATE users
        SET department_id = roles.department_id,
            employee_id = 'AARKA-EMP-' || lpad(users.id::text, 6, '0')
        FROM roles
        WHERE users.role = roles.name
        """
    )
    op.execute(
        """
        UPDATE users
        SET employee_id = 'AARKA-EMP-' || lpad(id::text, 6, '0')
        WHERE role <> 'Customer' AND employee_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE leads
        SET assigned_user_id = users.id
        FROM users
        WHERE leads.assigned_user_id IS NULL
          AND users.role = 'Sales Executive'
          AND (
            lower(users.name) = lower(leads.assigned_sales_rep)
            OR lower(users.email) = lower(leads.assigned_sales_rep)
          )
        """
    )
    op.execute(
        """
        UPDATE customers
        SET assigned_user_id = (
            SELECT leads.assigned_user_id
            FROM leads
            WHERE leads.customer_id = customers.id
              AND leads.assigned_user_id IS NOT NULL
            ORDER BY leads.id
            LIMIT 1
        )
        WHERE customers.assigned_user_id IS NULL
          AND EXISTS (
            SELECT 1 FROM leads
            WHERE leads.customer_id = customers.id
              AND leads.assigned_user_id IS NOT NULL
          )
        """
    )
    for table_name, role_name in (
        ("site_surveys", "Site Survey Engineer"),
        ("installations", "Solar Technician"),
    ):
        op.execute(
            f"""
            UPDATE {table_name}
            SET assigned_user_id = users.id
            FROM technicians
            JOIN users ON lower(users.email) = lower(technicians.email)
            WHERE {table_name}.technician_id = technicians.id
              AND {table_name}.assigned_user_id IS NULL
              AND users.role = '{role_name}'
            """
        )
    op.execute(
        """
        UPDATE dispatches
        SET assigned_user_id = users.id
        FROM users
        WHERE dispatches.assigned_user_id IS NULL
          AND (
            lower(users.name) = lower(dispatches.dispatched_by)
            OR lower(users.email) = lower(dispatches.dispatched_by)
          )
        """
    )
    op.execute(
        """
        UPDATE service_tickets
        SET assigned_user_id = users.id
        FROM technicians
        JOIN users ON lower(users.email) = lower(technicians.email)
        WHERE service_tickets.technician_id = technicians.id
          AND service_tickets.assigned_user_id IS NULL
          AND users.role = 'Support Executive'
        """
    )


def downgrade() -> None:
    for table_name in (
        "service_tickets",
        "dispatches",
        "installations",
        "site_surveys",
        "leads",
        "customers",
    ):
        op.drop_constraint(
            f"fk_{table_name}_assigned_user_id_users",
            table_name,
            type_="foreignkey",
        )
        op.drop_index(f"ix_{table_name}_assigned_user_id", table_name=table_name)
        op.drop_column(table_name, "assigned_user_id")

    op.drop_constraint("fk_users_reporting_manager_id_users", "users", type_="foreignkey")
    op.drop_constraint("fk_users_department_id_departments", "users", type_="foreignkey")
    op.drop_index("ix_users_employee_id", table_name="users")
    op.drop_column("users", "reporting_manager_id")
    op.drop_column("users", "department_id")
    op.drop_column("users", "employee_id")
    op.drop_table("user_permissions")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("departments")
