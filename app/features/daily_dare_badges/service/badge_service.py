"""
Badge Service for Daily Dares

Provides high-level operations for badge management:
- Getting user badges
- Dashboard overview (last earned, next to earn)
- Triggering badge evaluation
"""
from datetime import date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.features.daily_dare_badges.repository.daily_dare_badge_repository import DailyDareBadgeRepository
from app.features.daily_dare_badges.repository.user_daily_dare_badge_repository import UserDailyDareBadgeRepository
from app.features.daily_dare_badges.service.badge_evaluator import BadgeEvaluator


class DailyDareBadgeService:
    """Service for badge-related operations"""

    def __init__(self, db: Session):
        self.db = db
        self.badge_repo = DailyDareBadgeRepository(db)
        self.user_badge_repo = UserDailyDareBadgeRepository(db)
        self.evaluator = BadgeEvaluator(db)

    # ==================== Badge Evaluation ====================

    def evaluate_badges_for_user(self, user_id: int, completion_date: date) -> List[str]:
        """
        Evaluate all badges for a user after completing a dare.
        Called after a user marks a dare as completed.

        Returns:
            List of badge slugs that were newly earned
        """
        return self.evaluator.evaluate_all_badges(user_id, completion_date)

    def assign_warrior_badge(self, user_id: int) -> Optional[str]:
        """
        Assign The Warrior badge to a new user.
        Called when user first accesses the app.
        """
        return self.evaluator.assign_warrior_badge(user_id)

    # ==================== User Badges ====================

    def get_user_badges(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all badges earned by a user.

        Returns list of badges with earning details:
        - badge info (name, slug, level, etc.)
        - earned_at timestamp
        - times_earned count
        """
        user_badges = self.user_badge_repo.get_user_badges(user_id)

        # Group by badge and count earnings
        badge_data = {}
        for user_badge in user_badges:
            badge = user_badge.badge
            if badge.id not in badge_data:
                badge_data[badge.id] = {
                    'id': badge.id,
                    'name': badge.name,
                    'slug': badge.slug,
                    'description': badge.description,
                    'type': badge.type,
                    'level': badge.level,
                    'image_earned': badge.image_earned,
                    'first_earned_at': user_badge.earned_at,
                    'last_earned_at': user_badge.earned_at,
                    'times_earned': 1,
                }
            else:
                badge_data[badge.id]['times_earned'] += 1
                badge_data[badge.id]['last_earned_at'] = user_badge.earned_at

        return list(badge_data.values())

    # ==================== Dashboard ====================

    def get_dashboard_overview(self, user_id: int) -> Dict[str, Any]:
        """
        Get badge dashboard overview for a user.

        Returns:
        - last_earned_regular: Most recently earned regular badge
        - last_earned_monthly: Most recently earned monthly badge
        - next_regular: Next regular badge to earn (by priority)
        - next_monthly: Current month's badge (if not earned)
        """
        # Get last earned badges
        last_regular = self.user_badge_repo.get_last_earned_badge(user_id, badge_type='regular')
        last_monthly = self.user_badge_repo.get_last_earned_badge(user_id, badge_type='monthly')

        # Get next regular badge (by priority)
        next_regular = self._get_next_regular_badge(user_id, last_regular)

        # Get current month's badge
        today = date.today()
        current_monthly = self.badge_repo.get_by_month_and_year(today.month, today.year)
        next_monthly = None
        if current_monthly:
            if not self.user_badge_repo.has_badge(user_id, current_monthly.id):
                next_monthly = current_monthly

        return {
            'last_earned_regular': self._format_user_badge(last_regular) if last_regular else None,
            'last_earned_monthly': self._format_user_badge(last_monthly) if last_monthly else None,
            'next_regular': self._format_badge(next_regular) if next_regular else None,
            'next_monthly': self._format_badge(next_monthly) if next_monthly else None,
        }

    def get_all_badges_with_status(self, user_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all badges with user's achievement status.

        Returns:
        - regular_badges: All regular badges with earned status
        - monthly_badges: All monthly badges with earned status
        """
        # Get all badges
        regular_badges = self.badge_repo.get_regular_badges()
        monthly_badges = self.badge_repo.get_monthly_badges()

        # Get user's earned badges
        user_badges = self.user_badge_repo.get_user_badges(user_id)
        earned_badge_ids = {ub.badge_id for ub in user_badges}

        # Count earnings per badge
        earnings_count = {}
        for ub in user_badges:
            earnings_count[ub.badge_id] = earnings_count.get(ub.badge_id, 0) + 1

        # Format regular badges
        formatted_regular = []
        for badge in regular_badges:
            formatted_regular.append({
                **self._format_badge(badge),
                'is_earned': badge.id in earned_badge_ids,
                'times_earned': earnings_count.get(badge.id, 0),
            })

        # Format monthly badges
        formatted_monthly = []
        for badge in monthly_badges:
            formatted_monthly.append({
                **self._format_badge(badge),
                'is_earned': badge.id in earned_badge_ids,
                'times_earned': earnings_count.get(badge.id, 0),
            })

        return {
            'regular_badges': formatted_regular,
            'monthly_badges': formatted_monthly,
        }

    # ==================== Helper Methods ====================

    def _get_next_regular_badge(self, user_id: int, last_earned) -> Optional[Any]:
        """Find the next regular badge user can earn (by priority)."""
        current_priority = 0
        if last_earned and last_earned.badge:
            current_priority = last_earned.badge.priority or 0

        # Look for the next unearned badge by priority
        all_regular = self.badge_repo.get_regular_badges()

        for badge in all_regular:
            if badge.priority and badge.priority > current_priority:
                if not self.user_badge_repo.has_badge(user_id, badge.id):
                    return badge

        return None

    def _format_badge(self, badge) -> Dict[str, Any]:
        """Format a badge entity for API response."""
        return {
            'id': badge.id,
            'name': badge.name,
            'slug': badge.slug,
            'description': badge.description,
            'pre_text': badge.pre_text,
            'post_text': badge.post_text,
            'type': badge.type,
            'level': badge.level,
            'priority': badge.priority,
            'month': badge.month,
            'year': badge.year,
            'image_earned': badge.image_earned,
            'image_not_earned': badge.image_not_earned,
        }

    def _format_user_badge(self, user_badge) -> Dict[str, Any]:
        """Format a user badge for API response."""
        return {
            **self._format_badge(user_badge.badge),
            'earned_at': user_badge.earned_at.isoformat() if user_badge.earned_at else None,
        }
