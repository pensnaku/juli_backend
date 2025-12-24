"""Add questionnaire_completion_id FK to observations table

Revision ID: add_obs_questionnaire_fk
Revises: add_completion_date
Create Date: 2025-12-23 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_obs_questionnaire_fk'
down_revision: Union[str, None] = 'add_completion_date'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add questionnaire_completion_id column to observations
    op.add_column(
        'observations',
        sa.Column('questionnaire_completion_id', sa.Integer(), nullable=True)
    )

    # Create index for efficient lookups
    op.create_index(
        op.f('ix_observations_questionnaire_completion_id'),
        'observations',
        ['questionnaire_completion_id'],
        unique=False
    )

    # Create foreign key constraint
    op.create_foreign_key(
        'fk_observations_questionnaire_completion',
        'observations',
        'questionnaire_completions',
        ['questionnaire_completion_id'],
        ['id']
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint(
        'fk_observations_questionnaire_completion',
        'observations',
        type_='foreignkey'
    )

    # Drop index
    op.drop_index(
        op.f('ix_observations_questionnaire_completion_id'),
        table_name='observations'
    )

    # Drop column
    op.drop_column('observations', 'questionnaire_completion_id')
