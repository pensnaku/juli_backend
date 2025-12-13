"""add_reminder_enabled_to_medications

Revision ID: a4bd667d17ec
Revises: b2c3d4e5f6g7
Create Date: 2025-12-10 11:12:18.809562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4bd667d17ec'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_medications', sa.Column('reminder_enabled', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    op.drop_column('user_medications', 'reminder_enabled')
