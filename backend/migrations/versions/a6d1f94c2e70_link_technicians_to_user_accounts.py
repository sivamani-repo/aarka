"""link technician profiles to employee accounts

Revision ID: a6d1f94c2e70
Revises: cc2349f1d0ab
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a6d1f94c2e70"
down_revision: Union[str, Sequence[str], None] = "cc2349f1d0ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "technicians",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_technicians_user_id_users",
        "technicians",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_technicians_user_id",
        "technicians",
        ["user_id"],
    )
    op.add_column(
        "technicians",
        sa.Column(
            "availability_updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("technicians", "availability_updated_at")
    op.drop_constraint("uq_technicians_user_id", "technicians", type_="unique")
    op.drop_constraint("fk_technicians_user_id_users", "technicians", type_="foreignkey")
    op.drop_column("technicians", "user_id")
