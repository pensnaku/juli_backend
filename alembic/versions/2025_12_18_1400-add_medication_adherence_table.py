"""Add medication adherence table

Revision ID: add_medication_adherence
Revises: 2025_12_15_1400-add_juli_scores_table
Create Date: 2025-12-18 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_medication_adherence'
down_revision: Union[str, None] = 'b5f8e2a3c9d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type using raw SQL to avoid SQLAlchemy's automatic creation
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'adherencestatus') THEN
                CREATE TYPE adherencestatus AS ENUM ('not_set', 'taken', 'not_taken', 'partly_taken');
            END IF;
        END $$;
    """))

    # Check if table already exists
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.tables WHERE table_name = 'medication_adherence'"
    ))
    table_exists = result.fetchone() is not None

    if not table_exists:
        # Create table using raw SQL to use the existing enum type
        conn.execute(sa.text("""
            CREATE TABLE medication_adherence (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                medication_id INTEGER NOT NULL REFERENCES user_medications(id),
                date DATE NOT NULL,
                status adherencestatus NOT NULL DEFAULT 'not_set',
                notes VARCHAR(500),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE,
                CONSTRAINT uq_user_medication_date UNIQUE (user_id, medication_id, date)
            );
        """))

        # Create indexes
        op.create_index(op.f('ix_medication_adherence_id'), 'medication_adherence', ['id'], unique=False)
        op.create_index(op.f('ix_medication_adherence_user_id'), 'medication_adherence', ['user_id'], unique=False)
        op.create_index(op.f('ix_medication_adherence_medication_id'), 'medication_adherence', ['medication_id'], unique=False)
        op.create_index(op.f('ix_medication_adherence_date'), 'medication_adherence', ['date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_medication_adherence_date'), table_name='medication_adherence')
    op.drop_index(op.f('ix_medication_adherence_medication_id'), table_name='medication_adherence')
    op.drop_index(op.f('ix_medication_adherence_user_id'), table_name='medication_adherence')
    op.drop_index(op.f('ix_medication_adherence_id'), table_name='medication_adherence')
    op.drop_table('medication_adherence')

    # Drop enum type
    sa.Enum(name='adherencestatus').drop(op.get_bind(), checkfirst=True)
