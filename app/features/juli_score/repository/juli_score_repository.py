"""Repository for Juli Score data operations"""
from typing import Optional, List, Tuple
from datetime import datetime, date, timedelta
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, distinct, select

from app.features.juli_score.domain.entities import JuliScore
from app.features.observations.domain.entities import Observation
from app.features.auth.domain.entities import UserCondition
from app.features.juli_score.constants import SUPPORTED_CONDITION_CODES


class JuliScoreRepository:
    """Repository for Juli Score operations"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Observation Queries ====================

    def get_observation_value_for_date(
        self,
        user_id: int,
        code: str,
        target_date: date,
        variant: Optional[str] = None,
    ) -> Optional[Decimal]:
        """Get the most recent observation value for a specific code on a given date"""
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        query = self.db.query(Observation).filter(
            Observation.user_id == user_id,
            Observation.code == code,
            Observation.effective_at >= start_of_day,
            Observation.effective_at <= end_of_day,
        )

        # Add variant filter if specified
        if variant is not None:
            query = query.filter(Observation.variant == variant)

        observation = query.order_by(Observation.effective_at.desc()).first()

        if observation:
            if observation.value_decimal is not None:
                return observation.value_decimal
            if observation.value_integer is not None:
                return Decimal(observation.value_integer)
        return None

    def get_observation_string_for_date(
        self,
        user_id: int,
        code: str,
        target_date: date,
        variant: Optional[str] = None,
    ) -> Optional[str]:
        """Get string observation value (e.g., mood)"""
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        query = self.db.query(Observation).filter(
            Observation.user_id == user_id,
            Observation.code == code,
            Observation.effective_at >= start_of_day,
            Observation.effective_at <= end_of_day,
        )

        # Add variant filter if specified
        if variant is not None:
            query = query.filter(Observation.variant == variant)

        observation = query.order_by(Observation.effective_at.desc()).first()

        return observation.value_string if observation else None

    def get_average_value_for_period(
        self,
        user_id: int,
        code: str,
        days: int,
        end_date: date,
        variant: Optional[str] = None,
    ) -> Optional[Decimal]:
        """Get average observation value over a period"""
        start_date = end_date - timedelta(days=days)
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        query = self.db.query(
            func.avg(func.coalesce(Observation.value_decimal, Observation.value_integer))
        ).filter(
            Observation.user_id == user_id,
            Observation.code == code,
            Observation.effective_at >= start_dt,
            Observation.effective_at <= end_dt,
        )

        # Add variant filter if specified
        if variant is not None:
            query = query.filter(Observation.variant == variant)

        result = query.scalar()

        return Decimal(str(result)) if result else None

    def get_latest_value_in_period(
        self,
        user_id: int,
        code: str,
        days: int,
        end_date: date,
        variant: Optional[str] = None,
    ) -> Optional[Decimal]:
        """Get the most recent value within a time period"""
        start_date = end_date - timedelta(days=days)
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        query = self.db.query(Observation).filter(
            Observation.user_id == user_id,
            Observation.code == code,
            Observation.effective_at >= start_dt,
            Observation.effective_at <= end_dt,
        )

        # Add variant filter if specified
        if variant is not None:
            query = query.filter(Observation.variant == variant)

        observation = query.order_by(Observation.effective_at.desc()).first()

        if observation:
            if observation.value_decimal is not None:
                return observation.value_decimal
            if observation.value_integer is not None:
                return Decimal(observation.value_integer)
        return None

    def get_hrv_values_for_period(
        self,
        user_id: int,
        code: str,
        days: int,
        end_date: date,
        variant: Optional[str] = None,
    ) -> List[Decimal]:
        """Get all HRV values for a period (for calculating diff from average)"""
        start_date = end_date - timedelta(days=days)
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        query = self.db.query(Observation).filter(
            Observation.user_id == user_id,
            Observation.code == code,
            Observation.effective_at >= start_dt,
            Observation.effective_at <= end_dt,
        )

        # Add variant filter if specified
        if variant is not None:
            query = query.filter(Observation.variant == variant)

        observations = query.order_by(Observation.effective_at.desc()).all()

        values = []
        for obs in observations:
            if obs.value_decimal is not None:
                values.append(obs.value_decimal)
            elif obs.value_integer is not None:
                values.append(Decimal(obs.value_integer))
        return values

    # ==================== Juli Score Queries ====================

    def get_latest_juli_score(
        self,
        user_id: int,
        condition_code: str,
    ) -> Optional[JuliScore]:
        """Get the most recent Juli Score for a condition"""
        return (
            self.db.query(JuliScore)
            .filter(
                JuliScore.user_id == user_id,
                JuliScore.condition_code == condition_code,
            )
            .order_by(JuliScore.effective_at.desc())
            .first()
        )

    def get_juli_score_for_date(
        self,
        user_id: int,
        condition_code: str,
        target_date: date,
    ) -> Optional[JuliScore]:
        """Get Juli Score for a specific date"""
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        return (
            self.db.query(JuliScore)
            .filter(
                JuliScore.user_id == user_id,
                JuliScore.condition_code == condition_code,
                JuliScore.effective_at >= start_of_day,
                JuliScore.effective_at <= end_of_day,
            )
            .order_by(JuliScore.effective_at.desc())
            .first()
        )

    def get_juli_score_history(
        self,
        user_id: int,
        condition_code: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[JuliScore], int]:
        """Get paginated Juli Score history"""
        query = (
            self.db.query(JuliScore)
            .filter(
                JuliScore.user_id == user_id,
                JuliScore.condition_code == condition_code,
            )
            .order_by(JuliScore.effective_at.desc())
        )

        total = query.count()
        offset = (page - 1) * page_size
        scores = query.offset(offset).limit(page_size).all()

        return scores, total

    def save_juli_score(self, juli_score: JuliScore) -> JuliScore:
        """Save a new Juli Score"""
        self.db.add(juli_score)
        self.db.flush()
        return juli_score

    # ==================== User/Condition Queries ====================

    def get_active_users_with_conditions(
        self,
        active_days: int = 2,
    ) -> List[Tuple[int, str]]:
        """
        Get user IDs and their supported condition codes for users
        who have been active (have observations) in the last N days.

        Returns list of (user_id, condition_code) tuples.
        """
        cutoff_date = datetime.now() - timedelta(days=active_days)

        # Get active user IDs (users with recent observations)
        active_user_ids = (
            select(distinct(Observation.user_id))
            .where(Observation.created_at >= cutoff_date)
            .scalar_subquery()
        )

        # Get conditions for active users that are supported
        results = (
            self.db.query(UserCondition.user_id, UserCondition.condition_code)
            .filter(
                UserCondition.user_id.in_(active_user_ids),
                UserCondition.condition_code.in_(SUPPORTED_CONDITION_CODES),
            )
            .all()
        )

        return [(r.user_id, r.condition_code) for r in results]

    def get_user_conditions(
        self,
        user_id: int,
    ) -> List[str]:
        """Get supported condition codes for a user"""
        conditions = (
            self.db.query(UserCondition.condition_code)
            .filter(
                UserCondition.user_id == user_id,
                UserCondition.condition_code.in_(SUPPORTED_CONDITION_CODES),
            )
            .all()
        )
        return [c.condition_code for c in conditions]
