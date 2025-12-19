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
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type for adherence status
    adherence_status = sa.Enum('not_set', 'taken', 'not_taken', 'partly_taken', name='adherencestatus')
    adherence_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'medication_adherence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('medication_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('status', adherence_status, nullable=False, server_default='not_set'),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['medication_id'], ['user_medications.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'medication_id', 'date', name='uq_user_medication_date'),
    )
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
