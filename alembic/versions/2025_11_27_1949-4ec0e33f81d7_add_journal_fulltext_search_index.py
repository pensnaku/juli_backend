"""add_journal_fulltext_search_index

Revision ID: 4ec0e33f81d7
Revises: 6a6bc043dc74
Create Date: 2025-11-27 19:49:39.521731

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ec0e33f81d7'
down_revision: Union[str, None] = '6a6bc043dc74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create GIN index for full-text search on journal_entries.content
    op.execute("""
        CREATE INDEX ix_journal_entries_content_fts
        ON journal_entries
        USING GIN (to_tsvector('english', content))
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_journal_entries_content_fts")
