"""Service layer for observation business logic"""
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session

from app.features.observations.repository import ObservationRepository
from app.features.observations.domain.schemas import (
    ObservationCreate,
    ObservationUpdate,
    ObservationResponse,
    ObservationListResponse,
)


class ObservationService:
    """Service for managing observations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ObservationRepository(db)

    def create_observation(
        self, user_id: int, data: ObservationCreate
    ) -> ObservationResponse:
        """Create a new observation"""
        observation = self.repo.create(
            user_id=user_id,
            code=data.code,
            variant=data.variant,
            value_integer=data.value_integer,
            value_decimal=data.value_decimal,
            value_string=data.value_string,
            value_boolean=data.value_boolean,
            effective_at=data.effective_at,
            period_start=data.period_start,
            period_end=data.period_end,
            category=data.category,
            data_source=data.data_source,
            unit=data.unit,
            source_id=data.source_id,
        )
        self.db.commit()
        return ObservationResponse.model_validate(observation)

    def bulk_create_observations(
        self, user_id: int, observations_data: List[ObservationCreate]
    ) -> List[ObservationResponse]:
        """Create multiple observations at once"""
        data_dicts = [
            {
                "code": obs.code,
                "variant": obs.variant,
                "value_integer": obs.value_integer,
                "value_decimal": obs.value_decimal,
                "value_string": obs.value_string,
                "value_boolean": obs.value_boolean,
                "effective_at": obs.effective_at,
                "period_start": obs.period_start,
                "period_end": obs.period_end,
                "category": obs.category,
                "data_source": obs.data_source,
                "unit": obs.unit,
                "source_id": obs.source_id,
            }
            for obs in observations_data
        ]
        observations = self.repo.bulk_create(user_id, data_dicts)
        self.db.commit()
        return [ObservationResponse.model_validate(obs) for obs in observations]

    def get_observation(
        self, user_id: int, observation_id: UUID
    ) -> ObservationResponse:
        """Get a specific observation"""
        observation = self.repo.get_by_id(observation_id)

        if not observation:
            raise ValueError("Observation not found")

        if observation.user_id != user_id:
            raise ValueError("This observation does not belong to you")

        return ObservationResponse.model_validate(observation)

    def list_observations(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        code: Optional[str] = None,
        variant: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> ObservationListResponse:
        """Get paginated list of observations for a user"""
        observations, total = self.repo.get_by_user_paginated(
            user_id=user_id,
            page=page,
            page_size=page_size,
            code=code,
            variant=variant,
            category=category,
            start_date=start_date,
            end_date=end_date,
        )

        return ObservationListResponse(
            observations=[ObservationResponse.model_validate(o) for o in observations],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_latest_observation(
        self,
        user_id: int,
        code: str,
        variant: Optional[str] = None,
    ) -> Optional[ObservationResponse]:
        """Get the most recent observation for a code/variant"""
        observation = self.repo.get_latest_by_code(user_id, code, variant)

        if not observation:
            return None

        return ObservationResponse.model_validate(observation)

    def update_observation(
        self, user_id: int, observation_id: UUID, data: ObservationUpdate
    ) -> ObservationResponse:
        """Update an observation"""
        observation = self.repo.get_by_id(observation_id)

        if not observation:
            raise ValueError("Observation not found")

        if observation.user_id != user_id:
            raise ValueError("This observation does not belong to you")

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(observation, field, value)

        updated_observation = self.repo.update(observation)
        self.db.commit()
        return ObservationResponse.model_validate(updated_observation)

    def delete_observation(self, user_id: int, observation_id: UUID) -> None:
        """Delete an observation"""
        observation = self.repo.get_by_id(observation_id)

        if not observation:
            raise ValueError("Observation not found")

        if observation.user_id != user_id:
            raise ValueError("This observation does not belong to you")

        self.repo.delete(observation)
        self.db.commit()

    def upsert_observation(
        self, user_id: int, data: ObservationCreate
    ) -> ObservationResponse:
        """Create or update an observation based on unique constraint"""
        existing = self.repo.get_by_code_and_time(
            user_id=user_id,
            code=data.code,
            variant=data.variant,
            effective_at=data.effective_at,
            source_id=data.source_id,
        )

        if existing:
            # Update existing observation
            existing.value_integer = data.value_integer
            existing.value_decimal = data.value_decimal
            existing.value_string = data.value_string
            existing.value_boolean = data.value_boolean
            existing.period_start = data.period_start
            existing.period_end = data.period_end
            existing.category = data.category
            existing.data_source = data.data_source
            existing.unit = data.unit

            observation = self.repo.update(existing)
        else:
            observation = self.repo.create(
                user_id=user_id,
                code=data.code,
                variant=data.variant,
                value_integer=data.value_integer,
                value_decimal=data.value_decimal,
                value_string=data.value_string,
                value_boolean=data.value_boolean,
                effective_at=data.effective_at,
                period_start=data.period_start,
                period_end=data.period_end,
                category=data.category,
                data_source=data.data_source,
                unit=data.unit,
                source_id=data.source_id,
            )

        self.db.commit()
        return ObservationResponse.model_validate(observation)
