"""Populate default tracking topic questions

Revision ID: populate_tracking_qs
Revises: add_obs_query_index
Create Date: 2026-01-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'populate_tracking_qs'
down_revision: Union[str, None] = 'add_obs_query_index'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Default tracking topics with their questions
TRACKING_TOPICS = {
    "coffee-consumption": {
        "label": "Coffee Consumption",
        "question": "How many cups of coffee did you drink yesterday?",
        "data_type": "number",
        "unit": "cups-of-coffee",
        "emoji": "☕",
        "min": 0,
        "max": 10,
    },
    "smoking": {
        "label": "Smoking",
        "question": "How many cigarettes did you smoke yesterday?",
        "data_type": "number",
        "unit": "number-of-cigarettes",
        "emoji": "🚬",
        "min": 0,
        "max": 20,
    },
    "alcohol-consumption": {
        "label": "Alcohol Consumption",
        "question": "How many glasses of alcohol did you drink yesterday?",
        "data_type": "number",
        "unit": "glasses-of-alcohol",
        "emoji": "🍷",
        "min": 0,
        "max": 5,
    },
    "hours-spent-outside": {
        "label": "Hours Spent Outside",
        "question": "How many hours did you spend outside yesterday?",
        "data_type": "number",
        "unit": "hours-spent-outside",
        "emoji": "☀",
        "min": 0,
        "max": 5,
    },
}


def upgrade() -> None:
    """
    Populate question metadata for default tracking topics.

    This migration updates existing tracking topic records with their
    question data from TRACKING_TOPICS constants. Only updates records
    where the question field is currently NULL.
    """
    connection = op.get_bind()
    user_tracking_topics = sa.table(
        'user_tracking_topics',
        sa.column('topic_code', sa.String),
        sa.column('question', sa.String),
        sa.column('data_type', sa.String),
        sa.column('unit', sa.String),
        sa.column('emoji', sa.String),
        sa.column('min_value', sa.Integer),
        sa.column('max_value', sa.Integer),
    )

    # Update each default tracking topic
    for topic_code, metadata in TRACKING_TOPICS.items():
        connection.execute(
            user_tracking_topics.update()
            .where(user_tracking_topics.c.topic_code == topic_code)
            .where(user_tracking_topics.c.question.is_(None))
            .values(
                question=metadata["question"],
                data_type=metadata["data_type"],
                unit=metadata["unit"],
                emoji=metadata["emoji"],
                min_value=metadata["min"],
                max_value=metadata["max"],
            )
        )


def downgrade() -> None:
    """
    Remove populated question metadata for default tracking topics.

    This sets the metadata fields back to NULL for default topics.
    Custom topics (created by users) are not affected.
    """
    connection = op.get_bind()
    user_tracking_topics = sa.table(
        'user_tracking_topics',
        sa.column('topic_code', sa.String),
        sa.column('question', sa.String),
        sa.column('data_type', sa.String),
        sa.column('unit', sa.String),
        sa.column('emoji', sa.String),
        sa.column('min_value', sa.Integer),
        sa.column('max_value', sa.Integer),
    )

    # Clear metadata for default topics only
    default_topic_codes = list(TRACKING_TOPICS.keys())
    connection.execute(
        user_tracking_topics.update()
        .where(user_tracking_topics.c.topic_code.in_(default_topic_codes))
        .values(
            question=None,
            data_type=None,
            unit=None,
            emoji=None,
            min_value=None,
            max_value=None,
        )
    )
