"""Repository for UserDailyDareBadge data access"""
from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.features.daily_dare_badges.domain.entities.user_daily_dare_badge import UserDailyDareBadge
from app.features.daily_dare_badges.domain.entities.daily_dare_badge import DailyDareBadge


class UserDailyDareBadgeRepository:
    """Repository for UserDailyDareBadge operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_badge_id: int) -> Optional[UserDailyDareBadge]:
        """Get a user badge by ID"""
        return self.db.query(UserDailyDareBadge).filter(UserDailyDareBadge.id == user_badge_id).first()

    def get_user_badges(
        self,
        user_id: int,
        badge_type: Optional[str] = None
    ) -> List[UserDailyDareBadge]:
        """Get all badges earned by a user, optionally filtered by type"""
        query = (
            self.db.query(UserDailyDareBadge)
            .join(DailyDareBadge)
            .filter(UserDailyDareBadge.user_id == user_id)
        )

        if badge_type:
            query = query.filter(DailyDareBadge.type == badge_type)

        return query.order_by(UserDailyDareBadge.earned_at.desc()).all()

    def has_badge(self, user_id: int, badge_id: int) -> bool:
        """Check if a user has earned a specific badge"""
        count = (
            self.db.query(UserDailyDareBadge)
            .filter(
                UserDailyDareBadge.user_id == user_id,
                UserDailyDareBadge.badge_id == badge_id
            )
            .count()
        )
        return count > 0

    def has_badge_today(self, user_id: int, badge_id: int) -> bool:
        """Check if a user has earned a specific badge today"""
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())

        count = (
            self.db.query(UserDailyDareBadge)
            .filter(
                UserDailyDareBadge.user_id == user_id,
                UserDailyDareBadge.badge_id == badge_id,
                UserDailyDareBadge.earned_at >= today_start,
                UserDailyDareBadge.earned_at <= today_end
            )
            .count()
        )
        return count > 0

    def get_latest_badge(self, user_id: int, badge_id: int) -> Optional[UserDailyDareBadge]:
        """Get the most recent instance of a user earning a specific badge"""
        return (
            self.db.query(UserDailyDareBadge)
            .filter(
                UserDailyDareBadge.user_id == user_id,
                UserDailyDareBadge.badge_id == badge_id
            )
            .order_by(UserDailyDareBadge.earned_at.desc())
            .first()
        )

    def count_badge_earnings(self, user_id: int, badge_id: int) -> int:
        """Count how many times a user has earned a specific badge"""
        return (
            self.db.query(UserDailyDareBadge)
            .filter(
                UserDailyDareBadge.user_id == user_id,
                UserDailyDareBadge.badge_id == badge_id
            )
            .count()
        )

    def assign_badge(
        self,
        user_id: int,
        badge_id: int,
        can_be_multiple: bool = False
    ) -> Optional[UserDailyDareBadge]:
        """
        Assign a badge to a user.

        Args:
            user_id: The user to assign the badge to
            badge_id: The badge to assign
            can_be_multiple: If True, badge can be earned multiple times (but only once per day)

        Returns:
            UserDailyDareBadge if assigned, None if already earned
        """
        # Check if already has badge
        if self.has_badge(user_id, badge_id):
            if not can_be_multiple:
                return None  # Badge already earned and cannot be earned again
            if self.has_badge_today(user_id, badge_id):
                return None  # Badge already earned today

        # Create new user badge
        user_badge = UserDailyDareBadge(
            user_id=user_id,
            badge_id=badge_id
        )
        self.db.add(user_badge)
        self.db.flush()
        return user_badge

    def get_last_earned_badge(
        self,
        user_id: int,
        badge_type: Optional[str] = None
    ) -> Optional[UserDailyDareBadge]:
        """Get the most recently earned badge for a user"""
        query = (
            self.db.query(UserDailyDareBadge)
            .join(DailyDareBadge)
            .filter(UserDailyDareBadge.user_id == user_id)
        )

        if badge_type:
            query = query.filter(DailyDareBadge.type == badge_type)

        return query.order_by(UserDailyDareBadge.earned_at.desc()).first()
