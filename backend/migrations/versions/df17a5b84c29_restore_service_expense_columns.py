"""restore expense fields used by warranty service workflows

Revision ID: df17a5b84c29
Revises: c2f68a91d103
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "df17a5b84c29"
down_revision: Union[str, Sequence[str], None] = "c2f68a91d103"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


EXPENSE_COLUMNS = {
    "gst_amount": sa.Float(),
    "supplier_id": sa.Integer(),
    "vendor_name": sa.String(length=150),
    "invoice_reference": sa.String(length=100),
    "payment_method": sa.String(length=50),
    "approval_status": sa.String(length=50),
    "document_url": sa.String(length=255),
}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing_columns = {
        column["name"] for column in inspector.get_columns("project_expenses")
    }

    for column_name, column_type in EXPENSE_COLUMNS.items():
        if column_name not in existing_columns:
            op.add_column(
                "project_expenses",
                sa.Column(column_name, column_type, nullable=True),
            )

    inspector = sa.inspect(op.get_bind())
    has_supplier_foreign_key = any(
        foreign_key["constrained_columns"] == ["supplier_id"]
        and foreign_key["referred_table"] == "suppliers"
        for foreign_key in inspector.get_foreign_keys("project_expenses")
    )
    if not has_supplier_foreign_key:
        op.create_foreign_key(
            "fk_project_expenses_supplier_id_suppliers",
            "project_expenses",
            "suppliers",
            ["supplier_id"],
            ["id"],
        )

    op.execute(
        """
        UPDATE project_expenses
        SET gst_amount = COALESCE(gst_amount, 0),
            payment_method = COALESCE(payment_method, 'BANK_TRANSFER'),
            approval_status = COALESCE(approval_status, 'APPROVED')
        """
    )


def downgrade() -> None:
    # These fields belong to the earlier finance-model revision; keep them on downgrade.
    pass
