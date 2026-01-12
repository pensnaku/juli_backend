"""Add weather fields to observations

Revision ID: add_weather_fields
Revises: populate_tracking_qs
Create Date: 2026-01-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_weather_fields'
down_revision: Union[str, None] = 'populate_tracking_qs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add weather-specific fields to observations table
    op.add_column('observations', sa.Column('icon', sa.String(20), nullable=True))
    op.add_column('observations', sa.Column('status', sa.String(50), nullable=True))
    op.add_column('observations', sa.Column('description', sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column('observations', 'description')
    op.drop_column('observations', 'status')
    op.drop_column('observations', 'icon')
