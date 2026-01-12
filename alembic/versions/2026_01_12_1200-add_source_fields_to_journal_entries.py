"""Add source fields to journal entries

Revision ID: add_journal_source_fields
Revises: add_weather_fields
Create Date: 2026-01-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_journal_source_fields'
down_revision: Union[str, None] = 'add_weather_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add source tracking fields to journal_entries table
    op.add_column('journal_entries', sa.Column('source', sa.String(50), nullable=True))
    op.add_column('journal_entries', sa.Column('questionnaire_completion_id', sa.Integer(), nullable=True))
    op.create_index(
        'ix_journal_entries_questionnaire_completion_id',
        'journal_entries',
        ['questionnaire_completion_id']
    )
    op.create_foreign_key(
        'fk_journal_entries_questionnaire_completion_id',
        'journal_entries',
        'questionnaire_completions',
        ['questionnaire_completion_id'],
        ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_journal_entries_questionnaire_completion_id', 'journal_entries', type_='foreignkey')
    op.drop_index('ix_journal_entries_questionnaire_completion_id', 'journal_entries')
    op.drop_column('journal_entries', 'questionnaire_completion_id')
    op.drop_column('journal_entries', 'source')
