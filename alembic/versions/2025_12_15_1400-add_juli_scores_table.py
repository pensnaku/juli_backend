"""Add juli_scores table

Revision ID: b5f8e2a3c9d1
Revises: 4e895f3e4607
Create Date: 2025-12-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b5f8e2a3c9d1'
down_revision: Union[str, None] = '4e895f3e4607'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create juli_scores table
    op.create_table(
        'juli_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('condition_code', sa.String(20), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('effective_at', sa.DateTime(timezone=True), nullable=False),

        # Factor columns: _input = raw observation, _score = calculated contribution
        sa.Column('air_quality_input', sa.Numeric(10, 4), nullable=True),
        sa.Column('air_quality_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('sleep_input', sa.Numeric(10, 4), nullable=True),
        sa.Column('sleep_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('biweekly_input', sa.Numeric(10, 4), nullable=True),
        sa.Column('biweekly_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('active_energy_input', sa.Numeric(10, 4), nullable=True),
        sa.Column('active_energy_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('medication_input', sa.Numeric(10, 4), nullable=True),
        sa.Column('medication_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('mood_input', sa.Numeric(10, 4), nullable=True),
        sa.Column('mood_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('hrv_input', sa.Numeric(10, 4), nullable=True),
        sa.Column('hrv_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('pollen_input', sa.Numeric(10, 4), nullable=True),
        sa.Column('pollen_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('inhaler_input', sa.Numeric(10, 4), nullable=True),
        sa.Column('inhaler_score', sa.Numeric(10, 4), nullable=True),

        # Metadata
        sa.Column('data_points_used', sa.Integer(), nullable=False),
        sa.Column('total_weight', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),

        # Constraints
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'condition_code', 'effective_at', name='uq_juli_score_user_condition_time'),
    )

    # Create indexes for efficient querying
    op.create_index('idx_juli_score_user_id', 'juli_scores', ['user_id'], unique=False)
    op.create_index('idx_juli_score_condition', 'juli_scores', ['condition_code'], unique=False)
    op.create_index('idx_juli_score_user_condition', 'juli_scores', ['user_id', 'condition_code'], unique=False)
    op.create_index('idx_juli_score_effective', 'juli_scores', ['user_id', 'condition_code', sa.text('effective_at DESC')], unique=False)


def downgrade() -> None:
    op.drop_index('idx_juli_score_effective', table_name='juli_scores')
    op.drop_index('idx_juli_score_user_condition', table_name='juli_scores')
    op.drop_index('idx_juli_score_condition', table_name='juli_scores')
    op.drop_index('idx_juli_score_user_id', table_name='juli_scores')
    op.drop_table('juli_scores')
