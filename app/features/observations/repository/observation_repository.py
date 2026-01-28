"""Repository for observation database operations"""
from typing import List, Optional, Tuple, Dict
from datetime import datetime
from uuid import UUID
from collections import defaultdict
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
        data_source: Optional[str] = None,
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

        if data_source:
            query = query.filter(Observation.data_source == data_source)

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

    def get_by_questionnaire_completion_id(
        self,
        questionnaire_completion_id: int,
    ) -> List[Observation]:
        """Get all observations linked to a questionnaire completion"""
        return (
            self.db.query(Observation)
            .filter(Observation.questionnaire_completion_id == questionnaire_completion_id)
            .all()
        )

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

    def get_by_codes_and_date_range(
        self,
        user_id: int,
        codes: List[str],
        start_date: datetime,
        end_date: datetime,
        variants: Optional[List[str]] = None,
        data_sources: Optional[List[str]] = None,
        limit_per_code: Optional[int] = None,
    ) -> List[Observation]:
        """
        Optimized query for fetching observations by multiple codes and date range.

        Uses IN clause for codes and BETWEEN for date range for optimal index usage.
        Results are ordered by effective_at DESC.

        Args:
            user_id: User ID
            codes: List of observation codes to query
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            variants: Optional list of variants to filter by
            data_sources: Optional list of data sources to filter by
            limit_per_code: Optional limit per code (requires post-query filtering)

        Returns:
            List of observations matching the criteria
        """
        query = (
            self.db.query(
                Observation.id,
                Observation.code,
                Observation.variant,
                Observation.value_integer,
                Observation.value_decimal,
                Observation.value_string,
                Observation.value_boolean,
                Observation.effective_at,
                Observation.unit,
                Observation.data_source,
                Observation.icon,
                Observation.status,
                Observation.description,
            )
            .filter(Observation.user_id == user_id)
            .filter(Observation.code.in_(codes))
            .filter(Observation.effective_at.between(start_date, end_date))
        )

        if variants:
            query = query.filter(Observation.variant.in_(variants))

        if data_sources:
            query = query.filter(Observation.data_source.in_(data_sources))

        query = query.order_by(Observation.effective_at.desc())

        results = query.all()

        # Apply limit_per_code if specified (post-query filtering)
        if limit_per_code:
            code_counts: Dict[str, int] = defaultdict(int)
            filtered_results = []
            for row in results:
                if code_counts[row.code] < limit_per_code:
                    filtered_results.append(row)
                    code_counts[row.code] += 1
            return filtered_results

        return results

    def get_by_codes_and_date_range_grouped(
        self,
        user_id: int,
        codes: List[str],
        start_date: datetime,
        end_date: datetime,
        variants: Optional[List[str]] = None,
        data_sources: Optional[List[str]] = None,
        limit_per_code: Optional[int] = None,
    ) -> Dict[str, List]:
        """
        Same as get_by_codes_and_date_range but returns results grouped by code.

        Args:
            user_id: User ID
            codes: List of observation codes to query
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            variants: Optional list of variants to filter by
            data_sources: Optional list of data sources to filter by
            limit_per_code: Optional limit per code

        Returns:
            Dictionary mapping code -> list of observations
        """
        results = self.get_by_codes_and_date_range(
            user_id=user_id,
            codes=codes,
            start_date=start_date,
            end_date=end_date,
            variants=variants,
            data_sources=data_sources,
            limit_per_code=limit_per_code,
        )

        grouped: Dict[str, List] = defaultdict(list)
        for row in results:
            grouped[row.code].append(row)

        return dict(grouped)
