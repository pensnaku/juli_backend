"""
Badge Evaluator for Daily Dares

This module handles the evaluation and assignment of badges when users complete daily dares.

Badge Types:
- Points Badges: Earned by accumulating total points (Decade=10, Century=100, Millenium=1000)
- Strong Start: Earned by completing ANY dare for consecutive days (2, 5, 10, 15 days)
- Daredevil: Earned by completing ALL 4 dares for consecutive days (1, 7, 14, 30, 60 days)
- Streak: Earned by completing ANY dare for long periods (20, 50, 100, 180, 365 days)
- Monthly: Earned by meeting monthly challenge criteria
- The Warrior: Earned on first app access
"""
from datetime import date, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.features.daily_dare_badges.repository.daily_dare_badge_repository import DailyDareBadgeRepository
from app.features.daily_dare_badges.repository.user_daily_dare_badge_repository import UserDailyDareBadgeRepository
from app.features.dares.domain.entities.daily_dare_assignment import DailyDareAssignment


class BadgeConfig:
    """Configuration constants for badge evaluation"""

    # Badge slug prefixes
    STRONG_START = 'strong-start'
    DAREDEVIL = 'daredevil'
    STREAK = 'streak'
    DECADE = 'decade'
    CENTURY = 'century'
    MILLENIUM = 'millenium'
    THE_WARRIOR = 'the-warrior'

    # How many consecutive days needed for each badge level
    STRONG_START_DAYS = {
        1: 2,    # Level 1: 2 consecutive days
        2: 5,    # Level 2: 5 consecutive days
        3: 10,   # Level 3: 10 consecutive days
        4: 15,   # Level 4: 15 consecutive days
    }

    DAREDEVIL_DAYS = {
        1: 1,    # Level 1: 1 day (all 4 dares)
        2: 7,    # Level 2: 7 consecutive days
        3: 14,   # Level 3: 14 consecutive days
        4: 30,   # Level 4: 30 consecutive days
        5: 60,   # Level 5: 60 consecutive days
    }

    STREAK_DAYS = {
        1: 20,   # Level 1: 20 consecutive days
        2: 50,   # Level 2: 50 consecutive days
        3: 100,  # Level 3: 100 consecutive days
        4: 180,  # Level 4: 180 consecutive days
        5: 365,  # Level 5: 365 consecutive days (1 year!)
    }

    # Points needed for points-based badges
    POINTS_BADGES = {
        'decade': 10,
        'century': 100,
        'millenium': 1000,
    }


class BadgeEvaluator:
    """
    Evaluates and assigns badges to users based on their daily dare activity.

    Usage:
        evaluator = BadgeEvaluator(db)
        earned = evaluator.evaluate_all_badges(user_id, today)
    """

    def __init__(self, db: Session):
        self.db = db
        self.badge_repo = DailyDareBadgeRepository(db)
        self.user_badge_repo = UserDailyDareBadgeRepository(db)

    # ==================== Main Entry Point ====================

    def evaluate_all_badges(self, user_id: int, completion_date: date) -> List[str]:
        """
        Main method: Check all possible badges after a user completes a dare.

        Args:
            user_id: The user who completed a dare
            completion_date: The date the dare was completed

        Returns:
            List of badge slugs that were newly earned
        """
        earned_badges = []

        # 1. Check points-based badges (Decade, Century, Millenium)
        earned_badges.extend(self._check_points_badges(user_id))

        # 2. Check Strong Start badges (levels 1-4)
        for level in [1, 2, 3, 4]:
            if badge := self._check_strong_start(user_id, level, completion_date):
                earned_badges.append(badge)

        # 3. Check Daredevil badges (levels 1-5)
        for level in [1, 2, 3, 4, 5]:
            if badge := self._check_daredevil(user_id, level, completion_date):
                earned_badges.append(badge)

        # 4. Check Streak badges (levels 1-5)
        for level in [1, 2, 3, 4, 5]:
            if badge := self._check_streak(user_id, level, completion_date):
                earned_badges.append(badge)

        # 5. Check Monthly badge
        if badge := self._check_monthly_badge(user_id, completion_date):
            earned_badges.append(badge)

        # Save all changes
        if earned_badges:
            self.db.commit()

        return earned_badges

    # ==================== Points-Based Badges ====================

    def _check_points_badges(self, user_id: int) -> List[str]:
        """
        Check if user qualifies for Decade (10pts), Century (100pts), or Millenium (1000pts).
        """
        earned = []

        # Calculate total points earned by user
        total_points = self._get_total_points(user_id)

        # Check each points threshold
        for badge_slug, points_needed in BadgeConfig.POINTS_BADGES.items():
            if total_points >= points_needed:
                if self._try_assign_badge(user_id, badge_slug):
                    earned.append(badge_slug)

        return earned

    def _get_total_points(self, user_id: int) -> int:
        """Get the total points a user has earned from completed dares."""
        result = (
            self.db.query(func.sum(DailyDareAssignment.points_earned))
            .filter(
                DailyDareAssignment.user_id == user_id,
                DailyDareAssignment.is_completed == True
            )
            .scalar()
        )
        return result or 0

    # ==================== Strong Start Badges ====================

    def _check_strong_start(self, user_id: int, level: int, completion_date: date) -> Optional[str]:
        """
        Check Strong Start badge: Complete ANY dare for consecutive days.

        - Level 1: 2 consecutive days
        - Level 2: 5 consecutive days
        - Level 3: 10 consecutive days
        - Level 4: 15 consecutive days
        """
        days_needed = BadgeConfig.STRONG_START_DAYS.get(level)
        if not days_needed:
            return None

        badge_slug = f"{BadgeConfig.STRONG_START}{level}"

        # Check if user has the required consecutive days (at least 1 dare per day)
        has_streak = self._has_consecutive_days(
            user_id=user_id,
            end_date=completion_date,
            days_required=days_needed,
            min_dares_per_day=1  # At least 1 dare
        )

        if has_streak and self._try_assign_badge(user_id, badge_slug):
            return badge_slug

        return None

    # ==================== Daredevil Badges ====================

    def _check_daredevil(self, user_id: int, level: int, completion_date: date) -> Optional[str]:
        """
        Check Daredevil badge: Complete ALL 4 dares for consecutive days.

        - Level 1: 1 day with all 4 dares
        - Level 2: 7 consecutive days
        - Level 3: 14 consecutive days
        - Level 4: 30 consecutive days
        - Level 5: 60 consecutive days
        """
        days_needed = BadgeConfig.DAREDEVIL_DAYS.get(level)
        if not days_needed:
            return None

        badge_slug = f"{BadgeConfig.DAREDEVIL}{level}"

        # Check if user has the required consecutive days (ALL 4 dares per day)
        has_streak = self._has_consecutive_days(
            user_id=user_id,
            end_date=completion_date,
            days_required=days_needed,
            min_dares_per_day=4  # Must complete all 4 dares
        )

        if has_streak and self._try_assign_badge(user_id, badge_slug):
            return badge_slug

        return None

    # ==================== Streak Badges ====================

    def _check_streak(self, user_id: int, level: int, completion_date: date) -> Optional[str]:
        """
        Check Streak badge: Complete ANY dare for long consecutive periods.

        - Level 1: 20 consecutive days
        - Level 2: 50 consecutive days
        - Level 3: 100 consecutive days
        - Level 4: 180 consecutive days
        - Level 5: 365 consecutive days
        """
        days_needed = BadgeConfig.STREAK_DAYS.get(level)
        if not days_needed:
            return None

        badge_slug = f"{BadgeConfig.STREAK}{level}"

        # Check if user has the required consecutive days (at least 1 dare per day)
        has_streak = self._has_consecutive_days(
            user_id=user_id,
            end_date=completion_date,
            days_required=days_needed,
            min_dares_per_day=1  # At least 1 dare
        )

        if has_streak and self._try_assign_badge(user_id, badge_slug):
            return badge_slug

        return None

    # ==================== Monthly Badges ====================

    def _check_monthly_badge(self, user_id: int, completion_date: date) -> Optional[str]:
        """
        Check if user qualifies for this month's challenge badge.
        Monthly badges have custom criteria (category, count, points, etc.)
        """
        # Get the badge for this month
        badge = self.badge_repo.get_by_month_and_year(
            month=completion_date.month,
            year=completion_date.year
        )

        if not badge:
            return None

        # Get the date range for this month
        month_start = completion_date.replace(day=1)
        month_end = self._get_last_day_of_month(completion_date)

        # Get completed dares for this month
        completed_dares = self._get_completed_dares_in_range(
            user_id=user_id,
            start_date=month_start,
            end_date=month_end,
            category=badge.criteria_category
        )

        # Check if criteria is met
        if self._meets_monthly_criteria(badge, completed_dares):
            result = self.user_badge_repo.assign_badge(
                user_id=user_id,
                badge_id=badge.id,
                can_be_multiple=badge.can_be_multiple
            )
            if result:
                return badge.slug

        return None

    def _meets_monthly_criteria(self, badge, completed_dares: List) -> bool:
        """Check if the completed dares meet the monthly badge criteria."""
        dare_count = len(completed_dares)
        points_sum = sum(d.points_earned for d in completed_dares)
        unique_days = len(set(d.assigned_date for d in completed_dares))

        # Check each type of criteria
        if badge.criteria_expected_count and dare_count >= badge.criteria_expected_count:
            return True
        if badge.criteria_expected_point_sum and points_sum >= badge.criteria_expected_point_sum:
            return True
        if badge.criteria_unique_day_count and unique_days >= badge.criteria_unique_day_count:
            return True

        return False

    # ==================== The Warrior Badge ====================

    def assign_warrior_badge(self, user_id: int) -> Optional[str]:
        """
        Assign The Warrior badge to a new user (first app access).
        Called separately from the main evaluate method.
        """
        if self._try_assign_badge(user_id, BadgeConfig.THE_WARRIOR):
            self.db.commit()
            return BadgeConfig.THE_WARRIOR
        return None

    # ==================== Helper Methods ====================

    def _try_assign_badge(self, user_id: int, badge_slug: str) -> bool:
        """
        Try to assign a badge to a user.
        Returns True if badge was newly assigned, False if already had it.
        """
        badge = self.badge_repo.get_by_slug(badge_slug)
        if not badge:
            return False

        result = self.user_badge_repo.assign_badge(
            user_id=user_id,
            badge_id=badge.id,
            can_be_multiple=badge.can_be_multiple
        )
        return result is not None

    def _has_consecutive_days(
        self,
        user_id: int,
        end_date: date,
        days_required: int,
        min_dares_per_day: int
    ) -> bool:
        """
        Check if user has consecutive days of activity.

        Args:
            user_id: The user to check
            end_date: The last day to check (usually today)
            days_required: How many consecutive days needed
            min_dares_per_day: Minimum dares to count (1 for any, 4 for all)

        Returns:
            True if user has the required consecutive days
        """
        start_date = end_date - timedelta(days=days_required - 1)

        # Get count of completed dares for each day in the range
        daily_counts = (
            self.db.query(
                DailyDareAssignment.assigned_date,
                func.count(DailyDareAssignment.id).label('completed_count')
            )
            .filter(
                DailyDareAssignment.user_id == user_id,
                DailyDareAssignment.is_completed == True,
                DailyDareAssignment.assigned_date >= start_date,
                DailyDareAssignment.assigned_date <= end_date
            )
            .group_by(DailyDareAssignment.assigned_date)
            .all()
        )

        # Convert to dictionary: {date: count}
        counts_by_day = {row.assigned_date: row.completed_count for row in daily_counts}

        # Check each day going backwards from end_date
        current_date = end_date
        consecutive = 0

        while current_date >= start_date:
            dares_on_day = counts_by_day.get(current_date, 0)

            if dares_on_day >= min_dares_per_day:
                consecutive += 1
            else:
                break  # Streak broken!

            current_date -= timedelta(days=1)

        return consecutive >= days_required

    def _get_completed_dares_in_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        category: Optional[str] = None
    ) -> List[DailyDareAssignment]:
        """Get all completed dares for a user in a date range, optionally filtered by category."""
        query = (
            self.db.query(DailyDareAssignment)
            .filter(
                DailyDareAssignment.user_id == user_id,
                DailyDareAssignment.is_completed == True,
                DailyDareAssignment.assigned_date >= start_date,
                DailyDareAssignment.assigned_date <= end_date
            )
        )

        if category:
            from app.features.dares.domain.entities.dare import Dare
            query = query.join(Dare).filter(
                func.lower(Dare.category) == category.lower()
            )

        return query.all()

    def _get_last_day_of_month(self, ref_date: date) -> date:
        """Get the last day of the month for a given date."""
        if ref_date.month == 12:
            next_month = ref_date.replace(year=ref_date.year + 1, month=1, day=1)
        else:
            next_month = ref_date.replace(month=ref_date.month + 1, day=1)
        return next_month - timedelta(days=1)
