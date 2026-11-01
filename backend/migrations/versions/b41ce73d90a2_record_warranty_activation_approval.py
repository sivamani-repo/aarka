"""record warranty activation approval

Revision ID: b41ce73d90a2
Revises: a6d1f94c2e70
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b41ce73d90a2"
down_revision: Union[str, Sequence[str], None] = "a6d1f94c2e70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "warranty_records",
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "warranty_records",
        sa.Column("activated_by", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_warranty_records_activated_by_users",
        "warranty_records",
        "users",
        ["activated_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute(sa.text(
        "UPDATE warranty_records "
        "SET status = 'PENDING_ACTIVATION' "
        "WHERE status IN ('ACTIVE', 'COVERED', 'EXPIRING_SOON')"
    ))


def downgrade() -> None:
    op.drop_constraint(
        "fk_warranty_records_activated_by_users",
        "warranty_records",
        type_="foreignkey",
    )
    op.drop_column("warranty_records", "activated_by")
    op.drop_column("warranty_records", "activated_at")
