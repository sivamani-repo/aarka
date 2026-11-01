"""align assignment fields with current models

Revision ID: f2c9a13d6b40
Revises: 2d43cbd7a81f
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2c9a13d6b40"
down_revision: Union[str, Sequence[str], None] = "2d43cbd7a81f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


USER_COLUMNS = {
    "employee_id": sa.String(length=32),
    "department_id": sa.Integer(),
    "reporting_manager_id": sa.Integer(),
}
ASSIGNED_TABLES = (
    "customers",
    "leads",
    "site_surveys",
    "installations",
    "dispatches",
    "service_tickets",
)


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    inspector = sa.inspect(op.get_bind())
    if column.name not in {item["name"] for item in inspector.get_columns(table_name)}:
        op.add_column(table_name, column)


def _create_index_if_missing(index_name: str, table_name: str, column_name: str, unique: bool = False) -> None:
    inspector = sa.inspect(op.get_bind())
    if index_name not in {item["name"] for item in inspector.get_indexes(table_name)}:
        op.create_index(index_name, table_name, [column_name], unique=unique)


def _create_foreign_key_if_missing(
    constraint_name: str,
    table_name: str,
    column_name: str,
    referred_table: str,
) -> None:
    inspector = sa.inspect(op.get_bind())
    has_foreign_key = any(
        item["constrained_columns"] == [column_name]
        and item["referred_table"] == referred_table
        for item in inspector.get_foreign_keys(table_name)
    )
    if not has_foreign_key:
        op.create_foreign_key(
            constraint_name,
            table_name,
            referred_table,
            [column_name],
            ["id"],
        )


def upgrade() -> None:
    for column_name, column_type in USER_COLUMNS.items():
        _add_column_if_missing("users", sa.Column(column_name, column_type, nullable=True))
    _create_index_if_missing("ix_users_employee_id", "users", "employee_id", unique=True)
    _create_foreign_key_if_missing(
        "fk_users_department_id_departments", "users", "department_id", "departments"
    )
    _create_foreign_key_if_missing(
        "fk_users_reporting_manager_id_users", "users", "reporting_manager_id", "users"
    )

    for table_name in ASSIGNED_TABLES:
        _add_column_if_missing(table_name, sa.Column("assigned_user_id", sa.Integer(), nullable=True))
        _create_index_if_missing(
            f"ix_{table_name}_assigned_user_id", table_name, "assigned_user_id"
        )
        _create_foreign_key_if_missing(
            f"fk_{table_name}_assigned_user_id_users",
            table_name,
            "assigned_user_id",
            "users",
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
            employee_id = COALESCE(
                users.employee_id,
                'AARKA-EMP-' || lpad(users.id::text, 6, '0')
            )
        FROM roles
        WHERE users.role = roles.name
          AND (users.department_id IS NULL OR users.employee_id IS NULL)
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
    for table_name in reversed(ASSIGNED_TABLES):
        inspector = sa.inspect(op.get_bind())
        constraint_names = {
            item["name"]
            for item in inspector.get_foreign_keys(table_name)
            if item["name"] == f"fk_{table_name}_assigned_user_id_users"
        }
        for constraint_name in constraint_names:
            op.drop_constraint(constraint_name, table_name, type_="foreignkey")
        if f"ix_{table_name}_assigned_user_id" in {
            item["name"] for item in inspector.get_indexes(table_name)
        }:
            op.drop_index(f"ix_{table_name}_assigned_user_id", table_name=table_name)
        if "assigned_user_id" in {
            item["name"] for item in inspector.get_columns(table_name)
        }:
            op.drop_column(table_name, "assigned_user_id")

    inspector = sa.inspect(op.get_bind())
    for constraint_name in (
        "fk_users_reporting_manager_id_users",
        "fk_users_department_id_departments",
    ):
        if constraint_name in {
            item["name"] for item in inspector.get_foreign_keys("users")
        }:
            op.drop_constraint(constraint_name, "users", type_="foreignkey")
    if "ix_users_employee_id" in {
        item["name"] for item in inspector.get_indexes("users")
    }:
        op.drop_index("ix_users_employee_id", table_name="users")
    for column_name in reversed(tuple(USER_COLUMNS)):
        if column_name in {
            item["name"] for item in inspector.get_columns("users")
        }:
            op.drop_column("users", column_name)
