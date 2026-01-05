"""Add composite index for observations query optimization

Revision ID: add_obs_query_index
Revises: add_badges_tables
Create Date: 2026-01-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'add_obs_query_index'
down_revision: Union[str, None] = 'add_badges_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create composite index for optimized observation queries
    # This index supports queries filtering by user_id, code, and effective_at
    op.create_index(
        'ix_observations_user_code_effective',
        'observations',
        ['user_id', 'code', 'effective_at'],
        postgresql_ops={'effective_at': 'DESC'}
    )


def downgrade() -> None:
    op.drop_index('ix_observations_user_code_effective', table_name='observations')
