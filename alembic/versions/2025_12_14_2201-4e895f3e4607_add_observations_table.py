"""Add observations table

Revision ID: 4e895f3e4607
Revises: a4bd667d17ec
Create Date: 2025-12-14 22:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4e895f3e4607'
down_revision: Union[str, None] = 'a4bd667d17ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create observations table
    op.create_table(
        'observations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('variant', sa.String(100), nullable=True),
        sa.Column('value_integer', sa.Integer(), nullable=True),
        sa.Column('value_decimal', sa.Numeric(10, 4), nullable=True),
        sa.Column('value_string', sa.String(500), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.Column('effective_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('data_source', sa.String(50), nullable=True),
        sa.Column('unit', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('source_id', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'code', 'variant', 'effective_at', 'source_id', name='uq_observation_user_code_variant_time_source'),
    )

    # Create indexes for efficient querying
    op.create_index('idx_obs_user_id', 'observations', ['user_id'], unique=False)
    op.create_index('idx_obs_user_code', 'observations', ['user_id', 'code', sa.text('effective_at DESC')], unique=False)
    op.create_index('idx_obs_user_code_variant', 'observations', ['user_id', 'code', 'variant', sa.text('effective_at DESC')], unique=False)


def downgrade() -> None:
    op.drop_index('idx_obs_user_code_variant', table_name='observations')
    op.drop_index('idx_obs_user_code', table_name='observations')
    op.drop_index('idx_obs_user_id', table_name='observations')
    op.drop_table('observations')
