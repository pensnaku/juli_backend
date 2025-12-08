"""add_custom_tracking_topic_fields

Revision ID: a1b2c3d4e5f6
Revises: 4ec0e33f81d7
Create Date: 2025-12-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '4ec0e33f81d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add custom topic metadata columns to user_tracking_topics
    op.add_column('user_tracking_topics', sa.Column('question', sa.String(), nullable=True))
    op.add_column('user_tracking_topics', sa.Column('data_type', sa.String(), nullable=True))
    op.add_column('user_tracking_topics', sa.Column('unit', sa.String(), nullable=True))
    op.add_column('user_tracking_topics', sa.Column('emoji', sa.String(), nullable=True))
    op.add_column('user_tracking_topics', sa.Column('min_value', sa.Integer(), nullable=True))
    op.add_column('user_tracking_topics', sa.Column('max_value', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('user_tracking_topics', 'max_value')
    op.drop_column('user_tracking_topics', 'min_value')
    op.drop_column('user_tracking_topics', 'emoji')
    op.drop_column('user_tracking_topics', 'unit')
    op.drop_column('user_tracking_topics', 'data_type')
    op.drop_column('user_tracking_topics', 'question')