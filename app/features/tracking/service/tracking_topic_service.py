"""Service layer for tracking topics business logic"""
from typing import List, Optional
import re
import secrets
from sqlalchemy.orm import Session

from app.features.auth.repository import UserTrackingTopicRepository
from app.features.auth.domain.schemas import (
    UserTrackingTopicCreate,
    TrackingTopicUpdate,
    TrackingTopicResponse,
    TrackingTopicListResponse,
)
from app.shared.constants import TRACKING_TOPICS


def generate_topic_code(label: str, length: int = 6) -> str:
    """
    Generate a unique topic code from a label.

    Converts label to lowercase slug and adds random suffix for uniqueness.

    Args:
        label: Human-readable label (e.g., "Water Intake")
        length: Length of random suffix (default: 6)

    Returns:
        Topic code (e.g., "water-intake-a3b9f2")

    Example:
        >>> generate_topic_code("Water Intake")
        'water-intake-a3b9f2'
    """
    # Convert to lowercase and replace spaces with dashes
    slug = label.lower().strip()
    # Replace multiple spaces/special chars with single dash
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    # Remove leading/trailing dashes
    slug = slug.strip('-')

    # Generate random suffix for uniqueness
    random_suffix = secrets.token_hex(length // 2)

    return f"{slug}-{random_suffix}"


class TrackingTopicService:
    """Service for managing user tracking topics"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = UserTrackingTopicRepository(db)

    def get_all_topics(self, user_id: int) -> TrackingTopicListResponse:
        """
        Get all tracking topics for a user.
        Default topics are always included first, followed by any custom user topics.
        No duplicates - if a default topic is activated, it only appears once.
        """
        # Get user's activated topics from database
        user_topics = self.repo.get_by_user_id(user_id, active_only=False)
        user_topic_codes = {t.topic_code: t for t in user_topics}

        topics: List[TrackingTopicResponse] = []

        # Add default topics first (always included)
        for code, info in TRACKING_TOPICS.items():
            user_topic = user_topic_codes.get(code)
            is_active = user_topic.is_active if user_topic else False

            topics.append(TrackingTopicResponse(
                topic_code=code,
                label=info["label"],
                question=info["question"],
                data_type=info["data_type"],
                unit=info["unit"],
                emoji=info["emoji"],
                min=info["min"],
                max=info["max"],
                is_active=is_active,
                is_default=True,
            ))

        # Add any custom user topics (not in defaults)
        for topic in user_topics:
            if topic.topic_code not in TRACKING_TOPICS and topic.is_active:
                topics.append(TrackingTopicResponse(
                    topic_code=topic.topic_code,
                    label=topic.topic_label,
                    question=topic.question or f"How much {topic.topic_label.lower()} yesterday?",
                    data_type=topic.data_type or "number",
                    unit=topic.unit,
                    emoji=topic.emoji,
                    min=topic.min_value,
                    max=topic.max_value,
                    is_active=True,
                    is_default=False,
                ))

        return TrackingTopicListResponse(topics=topics)

    def activate_topic(
        self,
        user_id: int,
        request: UserTrackingTopicCreate,
    ) -> TrackingTopicResponse:
        """
        Activate a tracking topic for a user.
        For default topics, only topic_code is needed.
        For custom topics, label, question, and data_type are required.
        """
        topic_code = request.topic_code
        default_info = TRACKING_TOPICS.get(topic_code)

        if default_info:
            # Activating a default topic - store all default values
            topic = self.repo.upsert(
                user_id=user_id,
                topic_code=topic_code,
                topic_label=default_info["label"],
                question=default_info["question"],
                data_type=default_info["data_type"],
                unit=default_info["unit"],
                emoji=default_info["emoji"],
                min_value=default_info["min"],
                max_value=default_info["max"],
            )
            self.db.commit()

            return TrackingTopicResponse(
                topic_code=topic_code,
                label=default_info["label"],
                question=default_info["question"],
                data_type=default_info["data_type"],
                unit=default_info["unit"],
                emoji=default_info["emoji"],
                min=default_info["min"],
                max=default_info["max"],
                is_active=True,
                is_default=True,
            )
        else:
            # Creating a custom topic - validate required fields
            if not request.label:
                raise ValueError("label is required for custom topics")
            if not request.question:
                raise ValueError("question is required for custom topics")
            if not request.data_type:
                raise ValueError("data_type is required for custom topics")

            # Generate unique topic code if not provided or if it conflicts
            final_topic_code = topic_code

            # If user provided a topic_code, use it as-is (they take responsibility)
            # Otherwise, generate one from the label
            if not topic_code or topic_code == request.label.lower().replace(' ', '-'):
                final_topic_code = generate_topic_code(request.label)

                # Ensure uniqueness across all users
                max_attempts = 10
                for _ in range(max_attempts):
                    existing = self.repo.get_by_user_and_topic(user_id, final_topic_code)
                    if not existing:
                        break
                    final_topic_code = generate_topic_code(request.label)
                else:
                    raise ValueError("Could not generate unique topic code. Please try again.")

            # Create the custom topic with metadata
            topic = self.repo.upsert(
                user_id=user_id,
                topic_code=final_topic_code,
                topic_label=request.label,
                question=request.question,
                data_type=request.data_type,
                unit=request.unit,
                emoji=request.emoji,
                min_value=request.min,
                max_value=request.max,
            )
            self.db.commit()

            return TrackingTopicResponse(
                topic_code=final_topic_code,
                label=request.label,
                question=request.question,
                data_type=request.data_type,
                unit=request.unit,
                emoji=request.emoji,
                min=request.min,
                max=request.max,
                is_active=True,
                is_default=False,
            )

    def update_topic(
        self,
        user_id: int,
        topic_code: str,
        request: TrackingTopicUpdate,
    ) -> TrackingTopicResponse:
        """
        Update a tracking topic for a user.
        For default topics, only is_active can be changed.
        For custom topics, all fields can be updated.
        If changing from boolean to number, min and max must be provided.
        If changing from number to boolean, min and max are nullified.
        """
        is_default = topic_code in TRACKING_TOPICS
        default_info = TRACKING_TOPICS.get(topic_code)

        # Get the existing topic
        topic = self.repo.get_by_user_and_topic(user_id, topic_code)

        if is_default:
            # For default topics, only allow is_active changes
            # Always upsert to ensure metadata is populated
            topic = self.repo.upsert(
                user_id=user_id,
                topic_code=topic_code,
                topic_label=default_info["label"],
                question=default_info["question"],
                data_type=default_info["data_type"],
                unit=default_info["unit"],
                emoji=default_info["emoji"],
                min_value=default_info["min"],
                max_value=default_info["max"],
            )

            if request.is_active is not None:
                topic.is_active = request.is_active

            self.db.commit()

            return TrackingTopicResponse(
                topic_code=topic_code,
                label=default_info["label"],
                question=default_info["question"],
                data_type=default_info["data_type"],
                unit=default_info["unit"],
                emoji=default_info["emoji"],
                min=default_info["min"],
                max=default_info["max"],
                is_active=topic.is_active,
                is_default=True,
            )
        else:
            # Custom topic
            if topic is None:
                raise ValueError("Tracking topic not found")

            # Check if data_type is changing
            current_data_type = topic.data_type or "number"
            new_data_type = request.data_type if request.data_type is not None else current_data_type

            # If changing from boolean to number, require min and max
            if current_data_type == "boolean" and new_data_type == "number":
                if request.min is None or request.max is None:
                    raise ValueError("min and max are required when changing from boolean to number")

            # If changing from number to boolean, nullify min and max
            if current_data_type == "number" and new_data_type == "boolean":
                topic.min_value = None
                topic.max_value = None
                topic.unit = None

            # Update fields if provided
            if request.label is not None:
                topic.topic_label = request.label
            if request.question is not None:
                topic.question = request.question
            if request.data_type is not None:
                topic.data_type = request.data_type
            if request.is_active is not None:
                topic.is_active = request.is_active
            if request.emoji is not None:
                topic.emoji = request.emoji

            # Only update min/max/unit for number types
            if new_data_type == "number":
                if request.unit is not None:
                    topic.unit = request.unit
                if request.min is not None:
                    topic.min_value = request.min
                if request.max is not None:
                    topic.max_value = request.max

            self.db.commit()

            return TrackingTopicResponse(
                topic_code=topic_code,
                label=topic.topic_label,
                question=topic.question,
                data_type=topic.data_type,
                unit=topic.unit,
                emoji=topic.emoji,
                min=topic.min_value,
                max=topic.max_value,
                is_active=topic.is_active,
                is_default=False,
            )

    def delete_topic(self, user_id: int, topic_code: str) -> bool:
        """
        Delete a tracking topic for a user.
        Default topics cannot be deleted, only deactivated.
        """
        if topic_code in TRACKING_TOPICS:
            raise ValueError("Cannot delete default topics. Use deactivate instead.")

        topic = self.repo.get_by_user_and_topic(user_id, topic_code)
        if topic:
            self.repo.delete(topic.id)
            self.db.commit()
            return True
        return False

    def deactivate_topic(self, user_id: int, topic_code: str) -> bool:
        """Deactivate a tracking topic for a user"""
        topic = self.repo.get_by_user_and_topic(user_id, topic_code)
        if topic:
            topic.is_active = False
            self.db.commit()
            return True
        return False