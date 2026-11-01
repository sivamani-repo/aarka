"""record public enquiry consent

Revision ID: cc2349f1d0ab
Revises: ed0b3e4c1a6f
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "cc2349f1d0ab"
down_revision: Union[str, Sequence[str], None] = "ed0b3e4c1a6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column("privacy_consent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("leads", "privacy_consent_at")
