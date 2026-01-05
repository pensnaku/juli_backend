"""Repository for DailyDareBadge data access"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.features.daily_dare_badges.domain.entities.daily_dare_badge import DailyDareBadge


class DailyDareBadgeRepository:
    """Repository for DailyDareBadge operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, badge_id: int) -> Optional[DailyDareBadge]:
        """Get a badge by ID"""
        return self.db.query(DailyDareBadge).filter(DailyDareBadge.id == badge_id).first()

    def get_by_slug(self, slug: str) -> Optional[DailyDareBadge]:
        """Get a badge by slug"""
        return self.db.query(DailyDareBadge).filter(DailyDareBadge.slug == slug).first()

    def get_by_priority(self, priority: int) -> Optional[DailyDareBadge]:
        """Get a badge by priority"""
        return self.db.query(DailyDareBadge).filter(DailyDareBadge.priority == priority).first()

    def get_by_month_and_year(self, month: int, year: int) -> Optional[DailyDareBadge]:
        """Get a monthly badge by month and year"""
        return (
            self.db.query(DailyDareBadge)
            .filter(
                DailyDareBadge.type == 'monthly',
                DailyDareBadge.month == month,
                DailyDareBadge.year == year
            )
            .first()
        )

    def get_all(self, badge_type: Optional[str] = None) -> List[DailyDareBadge]:
        """Get all badges, optionally filtered by type"""
        query = self.db.query(DailyDareBadge)
        if badge_type:
            query = query.filter(DailyDareBadge.type == badge_type)
        return query.order_by(DailyDareBadge.priority).all()

    def get_regular_badges(self) -> List[DailyDareBadge]:
        """Get all regular badges sorted by priority"""
        return (
            self.db.query(DailyDareBadge)
            .filter(DailyDareBadge.type == 'regular')
            .order_by(DailyDareBadge.priority)
            .all()
        )

    def get_monthly_badges(self) -> List[DailyDareBadge]:
        """Get all monthly badges sorted by year and month"""
        return (
            self.db.query(DailyDareBadge)
            .filter(DailyDareBadge.type == 'monthly')
            .order_by(DailyDareBadge.year, DailyDareBadge.month)
            .all()
        )

    def create(self, **kwargs) -> DailyDareBadge:
        """Create a new badge"""
        badge = DailyDareBadge(**kwargs)
        self.db.add(badge)
        self.db.flush()
        return badge

    def bulk_create(self, badges_data: List[dict]) -> List[DailyDareBadge]:
        """Create multiple badges at once"""
        badges = [DailyDareBadge(**data) for data in badges_data]
        self.db.add_all(badges)
        self.db.flush()
        return badges
