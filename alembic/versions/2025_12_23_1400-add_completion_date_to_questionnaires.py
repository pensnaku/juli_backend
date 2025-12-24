"""Add completion_date to questionnaire_completions for daily questionnaires

Revision ID: add_completion_date
Revises: b5f8e2a3c9d1
Create Date: 2025-12-23 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_completion_date'
down_revision: Union[str, None] = 'add_medication_adherence'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add completion_date column (nullable for non-daily questionnaires like onboarding)
    op.add_column(
        'questionnaire_completions',
        sa.Column('completion_date', sa.Date(), nullable=True)
    )

    # Create index on completion_date for efficient date-based queries
    op.create_index(
        op.f('ix_questionnaire_completions_completion_date'),
        'questionnaire_completions',
        ['completion_date'],
        unique=False
    )

    # Drop existing unique constraint
    op.drop_constraint(
        'uq_user_questionnaire',
        'questionnaire_completions',
        type_='unique'
    )

    # Create new unique constraint including completion_date
    # This allows multiple records per user per questionnaire type (for daily/recurring)
    # while still preventing duplicates for the same date
    op.create_unique_constraint(
        'uq_user_questionnaire_date',
        'questionnaire_completions',
        ['user_id', 'questionnaire_id', 'completion_date']
    )


def downgrade() -> None:
    # Drop new unique constraint
    op.drop_constraint(
        'uq_user_questionnaire_date',
        'questionnaire_completions',
        type_='unique'
    )

    # Restore original unique constraint
    op.create_unique_constraint(
        'uq_user_questionnaire',
        'questionnaire_completions',
        ['user_id', 'questionnaire_id']
    )

    # Drop index
    op.drop_index(
        op.f('ix_questionnaire_completions_completion_date'),
        table_name='questionnaire_completions'
    )

    # Drop column
    op.drop_column('questionnaire_completions', 'completion_date')
