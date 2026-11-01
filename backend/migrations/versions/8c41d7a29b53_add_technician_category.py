"""add technician category

Revision ID: 8c41d7a29b53
Revises: f2c9a13d6b40
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c41d7a29b53"
down_revision: Union[str, Sequence[str], None] = "f2c9a13d6b40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("technicians")}
    if "category" not in columns:
        op.add_column(
            "technicians",
            sa.Column(
                "category",
                sa.String(length=50),
                nullable=False,
                server_default="Technician",
            ),
        )
        op.alter_column("technicians", "category", server_default=None)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "category" in {
        column["name"] for column in inspector.get_columns("technicians")
    }:
        op.drop_column("technicians", "category")
