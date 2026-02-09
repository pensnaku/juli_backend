"""Repository for push subscription database operations"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.features.notifications.domain.entities import PushSubscription


class PushSubscriptionRepository:
    """Handles all database operations for push subscriptions"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, subscription_id: int) -> Optional[PushSubscription]:
        """Get subscription by ID"""
        return (
            self.db.query(PushSubscription)
            .filter(PushSubscription.id == subscription_id)
            .first()
        )

    def get_by_user_id(self, user_id: int) -> List[PushSubscription]:
        """Get all active subscriptions for a user"""
        return (
            self.db.query(PushSubscription)
            .filter(
                PushSubscription.user_id == user_id,
                PushSubscription.is_active == True
            )
            .all()
        )

    def get_by_device_token(self, device_token: str) -> Optional[PushSubscription]:
        """Get subscription by device token"""
        return (
            self.db.query(PushSubscription)
            .filter(PushSubscription.device_token == device_token)
            .first()
        )

    def create(
        self, user_id: int, device_token: str, device_type: str
    ) -> PushSubscription:
        """Create a new push subscription"""
        subscription = PushSubscription(
            user_id=user_id,
            device_token=device_token,
            device_type=device_type,
            is_active=True
        )
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def delete(self, subscription_id: int) -> bool:
        """Delete a subscription by ID"""
        subscription = self.get_by_id(subscription_id)
        if subscription:
            self.db.delete(subscription)
            self.db.commit()
            return True
        return False

    def delete_by_device_token(self, device_token: str) -> bool:
        """Delete a subscription by device token"""
        subscription = self.get_by_device_token(device_token)
        if subscription:
            self.db.delete(subscription)
            self.db.commit()
            return True
        return False

    def update_token(
        self, old_token: str, new_token: str
    ) -> Optional[PushSubscription]:
        """Update device token (for token refresh)"""
        subscription = self.get_by_device_token(old_token)
        if subscription:
            subscription.device_token = new_token
            self.db.commit()
            self.db.refresh(subscription)
            return subscription
        return None

    def deactivate(self, subscription_id: int) -> bool:
        """Deactivate a subscription (soft delete)"""
        subscription = self.get_by_id(subscription_id)
        if subscription:
            subscription.is_active = False
            self.db.commit()
            return True
        return False

    def get_all_active(self) -> List[PushSubscription]:
        """Get all active push subscriptions (for broadcast)"""
        return (
            self.db.query(PushSubscription)
            .filter(PushSubscription.is_active == True)
            .all()
        )

    def get_by_device_type(self, device_type: str) -> List[PushSubscription]:
        """Get all active subscriptions by device type (for platform-specific broadcast)"""
        return (
            self.db.query(PushSubscription)
            .filter(
                PushSubscription.is_active == True,
                PushSubscription.device_type == device_type
            )
            .all()
        )
