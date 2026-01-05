"""Add daily dare badges tables

Revision ID: add_badges_tables
Revises: add_obs_questionnaire_fk
Create Date: 2025-12-29 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_badges_tables'
down_revision: Union[str, None] = 'add_obs_questionnaire_fk'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create daily_dare_badges table
    op.create_table(
        'daily_dare_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('pre_text', sa.Text(), nullable=True),
        sa.Column('post_text', sa.Text(), nullable=True),
        sa.Column('type', sa.String(20), nullable=False, server_default='regular'),
        sa.Column('level', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('can_be_multiple', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('month', sa.Integer(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('criteria_category', sa.String(50), nullable=True),
        sa.Column('criteria_expected_count', sa.Integer(), nullable=True),
        sa.Column('criteria_expected_point_sum', sa.Integer(), nullable=True),
        sa.Column('criteria_unique_day_count', sa.Integer(), nullable=True),
        sa.Column('image_earned', sa.String(500), nullable=True),
        sa.Column('image_not_earned', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index('ix_daily_dare_badges_slug', 'daily_dare_badges', ['slug'])
    op.create_index('ix_daily_dare_badges_type', 'daily_dare_badges', ['type'])

    # Create user_daily_dare_badges table
    op.create_table(
        'user_daily_dare_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('badge_id', sa.Integer(), nullable=False),
        sa.Column('earned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['badge_id'], ['daily_dare_badges.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_daily_dare_badges_user_id', 'user_daily_dare_badges', ['user_id'])
    op.create_index('ix_user_daily_dare_badges_badge_id', 'user_daily_dare_badges', ['badge_id'])
    op.create_index('ix_user_daily_dare_badges_earned_at', 'user_daily_dare_badges', ['earned_at'])


def downgrade() -> None:
    op.drop_index('ix_user_daily_dare_badges_earned_at', table_name='user_daily_dare_badges')
    op.drop_index('ix_user_daily_dare_badges_badge_id', table_name='user_daily_dare_badges')
    op.drop_index('ix_user_daily_dare_badges_user_id', table_name='user_daily_dare_badges')
    op.drop_table('user_daily_dare_badges')

    op.drop_index('ix_daily_dare_badges_type', table_name='daily_dare_badges')
    op.drop_index('ix_daily_dare_badges_slug', table_name='daily_dare_badges')
    op.drop_table('daily_dare_badges')
