"""Repository for user tracking topics"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.features.auth.domain.entities import UserTrackingTopic


class UserTrackingTopicRepository:
    """Repository for managing user tracking topics"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, topic_id: int) -> Optional[UserTrackingTopic]:
        """Get a tracking topic by ID"""
        return self.db.query(UserTrackingTopic).filter(UserTrackingTopic.id == topic_id).first()

    def get_by_user_id(self, user_id: int, active_only: bool = True) -> List[UserTrackingTopic]:
        """Get all tracking topics for a user"""
        query = self.db.query(UserTrackingTopic).filter(UserTrackingTopic.user_id == user_id)
        if active_only:
            query = query.filter(UserTrackingTopic.is_active == True)
        return query.all()

    def get_by_user_and_topic(self, user_id: int, topic_code: str) -> Optional[UserTrackingTopic]:
        """Get a specific tracking topic for a user"""
        return (
            self.db.query(UserTrackingTopic)
            .filter(
                UserTrackingTopic.user_id == user_id,
                UserTrackingTopic.topic_code == topic_code
            )
            .first()
        )

    def create(self, user_id: int, topic_code: str, topic_label: str) -> Optional[UserTrackingTopic]:
        """Create a new tracking topic (returns None if already exists)"""
        try:
            topic = UserTrackingTopic(
                user_id=user_id,
                topic_code=topic_code,
                topic_label=topic_label,
                is_active=True
            )
            self.db.add(topic)
            self.db.flush()
            return topic
        except IntegrityError:
            self.db.rollback()
            return None

    def upsert(self, user_id: int, topic_code: str, topic_label: str) -> UserTrackingTopic:
        """Create or reactivate a tracking topic"""
        existing = self.get_by_user_and_topic(user_id, topic_code)
        if existing:
            existing.is_active = True
            existing.topic_label = topic_label  # Update label in case it changed
            self.db.flush()
            return existing
        else:
            topic = UserTrackingTopic(
                user_id=user_id,
                topic_code=topic_code,
                topic_label=topic_label,
                is_active=True
            )
            self.db.add(topic)
            self.db.flush()
            return topic

    def deactivate(self, topic_id: int) -> bool:
        """Deactivate a tracking topic"""
        topic = self.get_by_id(topic_id)
        if topic:
            topic.is_active = False
            self.db.flush()
            return True
        return False

    def delete(self, topic_id: int) -> bool:
        """Delete a tracking topic"""
        topic = self.get_by_id(topic_id)
        if topic:
            self.db.delete(topic)
            self.db.flush()
            return True
        return False

    def replace_all(self, user_id: int, topics: List[tuple]) -> List[UserTrackingTopic]:
        """
        Replace all tracking topics for a user.

        Args:
            user_id: User ID
            topics: List of (topic_code, topic_label) tuples

        Returns:
            List of tracking topics after replacement
        """
        # Deactivate all existing topics
        existing_topics = self.get_by_user_id(user_id, active_only=False)
        for topic in existing_topics:
            topic.is_active = False

        # Create/reactivate topics from the list
        result_topics = []
        for topic_code, topic_label in topics:
            topic = self.upsert(user_id, topic_code, topic_label)
            result_topics.append(topic)

        self.db.flush()
        return result_topics