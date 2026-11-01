"""restore warranty columns if an existing database was stamped ahead of its schema

Revision ID: c2f68a91d103
Revises: 8c41d7a29b53
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2f68a91d103"
down_revision: Union[str, Sequence[str], None] = "8c41d7a29b53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


WARRANTY_COLUMNS = {
    "warranty_type": sa.String(length=50),
    "manufacturer": sa.String(length=100),
    "model_number": sa.String(length=100),
    "duration_months": sa.Integer(),
    "certificate_url": sa.String(length=255),
    "notes": sa.Text(),
    "expiry_alert_90d_sent": sa.Boolean(),
    "expiry_alert_30d_sent": sa.Boolean(),
    "expiry_alert_7d_sent": sa.Boolean(),
    "updated_at": sa.DateTime(timezone=True),
}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing_columns = {
        column["name"] for column in inspector.get_columns("warranty_records")
    }

    for column_name, column_type in WARRANTY_COLUMNS.items():
        if column_name not in existing_columns:
            op.add_column(
                "warranty_records",
                sa.Column(column_name, column_type, nullable=True),
            )

    op.execute(
        """
        UPDATE warranty_records
        SET warranty_type = COALESCE(warranty_type, 'PRODUCT'),
            manufacturer = COALESCE(manufacturer, 'Aarka Tech'),
            duration_months = COALESCE(duration_months, 24),
            expiry_alert_90d_sent = COALESCE(expiry_alert_90d_sent, FALSE),
            expiry_alert_30d_sent = COALESCE(expiry_alert_30d_sent, FALSE),
            expiry_alert_7d_sent = COALESCE(expiry_alert_7d_sent, FALSE),
            updated_at = COALESCE(updated_at, NOW())
        """
    )


def downgrade() -> None:
    # These columns belong to the earlier warranty-model revision; keep them on downgrade.
    pass
