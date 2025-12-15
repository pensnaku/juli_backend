"""Repository for observation database operations"""
from typing import List, Optional, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.features.observations.domain.entities import Observation


class ObservationRepository:
    """Repository for managing observations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, **kwargs) -> Observation:
        """Create a new observation"""
        observation = Observation(user_id=user_id, **kwargs)
        self.db.add(observation)
        self.db.flush()
        return observation

    def bulk_create(self, user_id: int, observations_data: List[dict]) -> List[Observation]:
        """Create multiple observations at once"""
        observations = [
            Observation(user_id=user_id, **data)
            for data in observations_data
        ]
        self.db.add_all(observations)
        self.db.flush()
        return observations

    def get_by_id(self, observation_id: UUID) -> Optional[Observation]:
        """Get an observation by ID"""
        return (
            self.db.query(Observation)
            .filter(Observation.id == observation_id)
            .first()
        )

    def get_by_user_paginated(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        code: Optional[str] = None,
        variant: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[List[Observation], int]:
        """Get paginated observations for a user with optional filters"""
        query = self.db.query(Observation).filter(Observation.user_id == user_id)

        if code:
            query = query.filter(Observation.code == code)

        if variant:
            query = query.filter(Observation.variant == variant)

        if category:
            query = query.filter(Observation.category == category)

        if start_date:
            query = query.filter(Observation.effective_at >= start_date)

        if end_date:
            query = query.filter(Observation.effective_at <= end_date)

        query = query.order_by(Observation.effective_at.desc())

        total = query.count()
        offset = (page - 1) * page_size
        observations = query.offset(offset).limit(page_size).all()

        return observations, total

    def get_by_code_and_time(
        self,
        user_id: int,
        code: str,
        variant: Optional[str],
        effective_at: datetime,
        source_id: Optional[str] = None,
    ) -> Optional[Observation]:
        """Get observation by unique constraint fields (for upsert logic)"""
        filters = [
            Observation.user_id == user_id,
            Observation.code == code,
            Observation.effective_at == effective_at,
        ]

        if variant is not None:
            filters.append(Observation.variant == variant)
        else:
            filters.append(Observation.variant.is_(None))

        if source_id is not None:
            filters.append(Observation.source_id == source_id)
        else:
            filters.append(Observation.source_id.is_(None))

        return self.db.query(Observation).filter(and_(*filters)).first()

    def get_latest_by_code(
        self,
        user_id: int,
        code: str,
        variant: Optional[str] = None,
    ) -> Optional[Observation]:
        """Get the most recent observation for a given code and optional variant"""
        query = (
            self.db.query(Observation)
            .filter(Observation.user_id == user_id)
            .filter(Observation.code == code)
        )

        if variant:
            query = query.filter(Observation.variant == variant)

        return query.order_by(Observation.effective_at.desc()).first()

    def update(self, observation: Observation) -> Observation:
        """Update an observation"""
        self.db.flush()
        return observation

    def delete(self, observation: Observation) -> None:
        """Delete an observation"""
        self.db.delete(observation)
        self.db.flush()

    def delete_by_user_and_code(
        self,
        user_id: int,
        code: str,
        variant: Optional[str] = None,
    ) -> int:
        """Delete all observations for a user with given code and optional variant"""
        query = (
            self.db.query(Observation)
            .filter(Observation.user_id == user_id)
            .filter(Observation.code == code)
        )

        if variant:
            query = query.filter(Observation.variant == variant)

        count = query.delete()
        self.db.flush()
        return count
