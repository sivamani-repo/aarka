"""add stock movement quantity snapshots

Revision ID: ed0b3e4c1a6f
Revises: 2d43cbd7a81f
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ed0b3e4c1a6f"
down_revision: Union[str, Sequence[str], None] = "2d43cbd7a81f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "stock_movements",
        sa.Column("quantity_before", sa.Integer(), nullable=True),
    )
    op.add_column(
        "stock_movements",
        sa.Column("quantity_after", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("stock_movements", "quantity_after")
    op.drop_column("stock_movements", "quantity_before")
