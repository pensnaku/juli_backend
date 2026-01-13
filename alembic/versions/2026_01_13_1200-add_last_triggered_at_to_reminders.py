"""Add last_triggered_at to user_reminders

Revision ID: add_last_triggered_at
Revises: add_journal_source_fields
Create Date: 2026-01-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_last_triggered_at'
down_revision: Union[str, None] = 'add_journal_source_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user_reminders',
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('user_reminders', 'last_triggered_at')
