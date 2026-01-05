"""Service layer for dares business logic"""
import asyncio
from typing import List
from datetime import date
from sqlalchemy.orm import Session

from app.features.dares.repository import DareRepository, DailyDareAssignmentRepository
from app.features.dares.domain.entities import Dare, DailyDareAssignment
from app.features.dares.domain.schemas import (
    DareWithAssignment,
    DailySummary,
    DailyDaresResponse,
    UpdateDareCompletionResponse,
    DailyHistoryItem,
    DareHistoryResponse,
)
from app.features.auth.repository import UserConditionRepository
from app.features.daily_dare_badges.service.badge_service import DailyDareBadgeService


# The 4 categories for daily dares
DARE_CATEGORIES = ["Activity", "Nutrition", "Sleep", "Wellness"]


class DareService:
    """Service for managing daily dares"""

    def __init__(self, db: Session):
        self.db = db
        self.dare_repo = DareRepository(db)
        self.assignment_repo = DailyDareAssignmentRepository(db)
        self.condition_repo = UserConditionRepository(db)
        self.badge_service = DailyDareBadgeService(db)

    def get_dares_for_date(self, user_id: int, target_date: date) -> DailyDaresResponse:
        """
        Get dares for a specific date.
        Generates them if they don't exist (for today or past dates).
        """
        # Check if dares already exist for this date
        assignments = self.assignment_repo.get_by_user_and_date(user_id, target_date)

        # If we don't have 4 dares, generate them
        if len(assignments) < 4:
            assignments = self._generate_daily_dares(user_id, target_date)

        # Build response
        dares_with_assignments = []
        total_points = 0
        points_earned = 0
        completed_count = 0

        for assignment in assignments:
            dare = assignment.dare
            total_points += dare.points

            if assignment.is_completed:
                points_earned += assignment.points_earned
                completed_count += 1

            dares_with_assignments.append(
                DareWithAssignment(
                    assignment_id=assignment.id,
                    dare_id=dare.id,
                    text=dare.text,
                    category=dare.category,
                    subcategory=dare.subcategory,
                    points=dare.points,
                    is_completed=assignment.is_completed,
                    completed_at=assignment.completed_at
                )
            )

        # Get 7-day total (includes today)
        seven_day_total = self.assignment_repo.get_seven_day_total_points(user_id, target_date)

        return DailyDaresResponse(
            date=target_date,
            dares=dares_with_assignments,
            summary=DailySummary(
                total_points_possible=total_points,
                points_earned=points_earned,
                completed_count=completed_count
            ),
            seven_day_total_points=seven_day_total
        )

    def _generate_daily_dares(self, user_id: int, target_date: date) -> List[DailyDareAssignment]:
        """Generate 4 dares (one per category) for a user on a specific date"""
        # Get user's condition codes for filtering
        user_conditions = self.condition_repo.get_by_user_id(user_id)
        condition_codes = [c.condition_code for c in user_conditions]

        # Get recently assigned dare IDs to avoid repetition
        recent_dare_ids = self.assignment_repo.get_recent_dare_ids(user_id, days=7)

        # Check what we already have for this date
        existing = self.assignment_repo.get_by_user_and_date(user_id, target_date)
        existing_categories = {a.dare.category for a in existing}

        assignments = list(existing)

        # Generate one dare per missing category
        for category in DARE_CATEGORIES:
            if category in existing_categories:
                continue

            dare = self.dare_repo.get_random_for_user(
                category=category,
                exclude_ids=recent_dare_ids,
                user_condition_codes=condition_codes
            )

            if dare:
                assignment = self.assignment_repo.create(
                    user_id=user_id,
                    dare_id=dare.id,
                    assigned_date=target_date
                )
                assignments.append(assignment)
                recent_dare_ids.add(dare.id)  # Don't pick same dare twice

        self.db.commit()
        return assignments

    def update_dare_completion(self, user_id: int, assignment_id: int, completed: bool) -> UpdateDareCompletionResponse:
        """Update dare completion status (complete or uncomplete)"""
        assignment = self.assignment_repo.get_by_id(assignment_id)

        if not assignment:
            raise ValueError("Dare assignment not found")

        if assignment.user_id != user_id:
            raise ValueError("This dare does not belong to you")

        if completed:
            # Complete the dare
            if assignment.is_completed:
                raise ValueError("This dare is already completed")

            points = assignment.dare.points
            updated_assignment = self.assignment_repo.mark_completed(assignment_id, points)
            self.db.commit()

            # Evaluate badges (non-blocking)
            earned_badges = self.badge_service.evaluate_badges_for_user(
                user_id=user_id,
                completion_date=assignment.assigned_date
            )

            return UpdateDareCompletionResponse(
                success=True,
                assignment_id=assignment_id,
                is_completed=True,
                points_earned=points,
                completed_at=updated_assignment.completed_at,
                badges_earned=earned_badges
            )
        else:
            # Uncomplete the dare
            if not assignment.is_completed:
                raise ValueError("This dare is not completed")

            updated_assignment = self.assignment_repo.mark_uncompleted(assignment_id)
            self.db.commit()

            return UpdateDareCompletionResponse(
                success=True,
                assignment_id=assignment_id,
                is_completed=False,
                points_earned=0,
                completed_at=None
            )

    def get_history(self, user_id: int, days: int = 7) -> DareHistoryResponse:
        """Get dare history for past N days"""
        if days > 30:
            days = 30  # Cap at 30 days

        assignments = self.assignment_repo.get_history(user_id, days)

        # Group by date
        history_by_date = {}
        for assignment in assignments:
            date_key = assignment.assigned_date
            if date_key not in history_by_date:
                history_by_date[date_key] = []
            history_by_date[date_key].append(assignment)

        # Build history items
        history = []
        total_points = 0
        total_completed = 0

        for target_date in sorted(history_by_date.keys(), reverse=True):
            date_assignments = history_by_date[target_date]
            dares_list = []
            day_points = 0
            day_completed = 0

            for assignment in date_assignments:
                dare = assignment.dare
                if assignment.is_completed:
                    day_points += assignment.points_earned
                    day_completed += 1
                    total_points += assignment.points_earned
                    total_completed += 1

                dares_list.append(
                    DareWithAssignment(
                        assignment_id=assignment.id,
                        dare_id=dare.id,
                        text=dare.text,
                        category=dare.category,
                        subcategory=dare.subcategory,
                        points=dare.points,
                        is_completed=assignment.is_completed,
                        completed_at=assignment.completed_at
                    )
                )

            history.append(
                DailyHistoryItem(
                    date=target_date,
                    dares=dares_list,
                    completed_count=day_completed,
                    points_earned=day_points
                )
            )

        return DareHistoryResponse(
            history=history,
            total_points=total_points,
            total_completed=total_completed
        )