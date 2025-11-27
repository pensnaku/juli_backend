"""Repository for daily dare assignments"""
from typing import List, Optional, Set
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.features.dares.domain.entities import DailyDareAssignment


class DailyDareAssignmentRepository:
    """Repository for managing daily dare assignments"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, assignment_id: int) -> Optional[DailyDareAssignment]:
        """Get an assignment by ID"""
        return (
            self.db.query(DailyDareAssignment)
            .filter(DailyDareAssignment.id == assignment_id)
            .first()
        )

    def get_by_user_and_date(self, user_id: int, assigned_date: date) -> List[DailyDareAssignment]:
        """Get all dare assignments for a user on a specific date"""
        return (
            self.db.query(DailyDareAssignment)
            .filter(
                DailyDareAssignment.user_id == user_id,
                DailyDareAssignment.assigned_date == assigned_date
            )
            .all()
        )

    def get_recent_dare_ids(self, user_id: int, days: int = 7) -> Set[int]:
        """Get IDs of dares assigned to user in the last N days"""
        cutoff_date = date.today() - timedelta(days=days)
        results = (
            self.db.query(DailyDareAssignment.dare_id)
            .filter(
                DailyDareAssignment.user_id == user_id,
                DailyDareAssignment.assigned_date >= cutoff_date
            )
            .all()
        )
        return {r[0] for r in results}

    def create(self, user_id: int, dare_id: int, assigned_date: date) -> DailyDareAssignment:
        """Create a new dare assignment"""
        assignment = DailyDareAssignment(
            user_id=user_id,
            dare_id=dare_id,
            assigned_date=assigned_date,
            is_completed=False,
            points_earned=0
        )
        self.db.add(assignment)
        self.db.flush()
        return assignment

    def mark_completed(self, assignment_id: int, points: int) -> Optional[DailyDareAssignment]:
        """Mark a dare assignment as completed"""
        assignment = self.get_by_id(assignment_id)
        if assignment and not assignment.is_completed:
            assignment.is_completed = True
            assignment.completed_at = datetime.utcnow()
            assignment.points_earned = points
            self.db.flush()
        return assignment

    def mark_uncompleted(self, assignment_id: int) -> Optional[DailyDareAssignment]:
        """Mark a dare assignment as uncompleted"""
        assignment = self.get_by_id(assignment_id)
        if assignment and assignment.is_completed:
            assignment.is_completed = False
            assignment.completed_at = None
            assignment.points_earned = 0
            self.db.flush()
        return assignment

    def get_history(self, user_id: int, days: int = 7) -> List[DailyDareAssignment]:
        """Get dare assignments for the past N days"""
        cutoff_date = date.today() - timedelta(days=days)
        return (
            self.db.query(DailyDareAssignment)
            .filter(
                DailyDareAssignment.user_id == user_id,
                DailyDareAssignment.assigned_date >= cutoff_date
            )
            .order_by(DailyDareAssignment.assigned_date.desc())
            .all()
        )

    def get_seven_day_total_points(self, user_id: int, end_date: date) -> int:
        """Get total points earned for the 7-day period ending on end_date (inclusive)"""
        from sqlalchemy import func

        start_date = end_date - timedelta(days=6)  # 7 days including end_date

        result = (
            self.db.query(func.sum(DailyDareAssignment.points_earned))
            .filter(
                DailyDareAssignment.user_id == user_id,
                DailyDareAssignment.assigned_date >= start_date,
                DailyDareAssignment.assigned_date <= end_date
            )
            .scalar()
        )

        return result or 0

    def get_user_stats(self, user_id: int) -> dict:
        """Get aggregated stats for a user"""
        from sqlalchemy import func

        result = (
            self.db.query(
                func.count(DailyDareAssignment.id).label('total_assigned'),
                func.sum(
                    func.cast(DailyDareAssignment.is_completed, Integer)
                ).label('total_completed'),
                func.sum(DailyDareAssignment.points_earned).label('total_points')
            )
            .filter(DailyDareAssignment.user_id == user_id)
            .first()
        )

        return {
            'total_assigned': result.total_assigned or 0,
            'total_completed': result.total_completed or 0,
            'total_points': result.total_points or 0
        }


# Import for type hint
from sqlalchemy import Integer
