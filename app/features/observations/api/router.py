"""API router for observations feature"""
import logging
from typing import Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_user
from app.features.auth.domain.entities import User
from app.features.observations.service import ObservationService
from app.features.observations.domain.schemas import (
    ObservationCreate,
    ObservationUpdate,
    ObservationResponse,
    ObservationListResponse,
    ObservationBulkCreate,
    ObservationQueryRequest,
    ObservationQueryResponse,
    ObservationQueryGroupedResponse,
    ObservationQueryItem,
)
from app.features.observations.repository import ObservationRepository


router = APIRouter()


@router.post("", response_model=ObservationResponse, status_code=status.HTTP_201_CREATED)
def create_observation(
    request: ObservationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new observation"""
    service = ObservationService(db)
    try:
        return service.create_observation(current_user.id, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/bulk", response_model=list[ObservationResponse], status_code=status.HTTP_201_CREATED)
def bulk_create_observations(
    request: ObservationBulkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create multiple observations at once (max 100)"""
    service = ObservationService(db)
    try:
        return service.bulk_create_observations(current_user.id, request.observations)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/upsert", response_model=ObservationResponse)
def upsert_observation(
    request: ObservationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update an observation based on unique constraint (user, code, variant, effective_at, source_id)"""
    service = ObservationService(db)
    try:
        return service.upsert_observation(current_user.id, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/query")
def query_observations(
    request: ObservationQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Query observations by multiple codes and date range.

    This is an optimized endpoint for fetching observations efficiently.
    Supports filtering by codes, date range, variants, and data sources.

    Returns either a flat list or grouped by code based on the `group_by_code` parameter.
    """
    repo = ObservationRepository(db)

    if request.group_by_code:
        grouped_results = repo.get_by_codes_and_date_range_grouped(
            user_id=current_user.id,
            codes=request.codes,
            start_date=request.start_date,
            end_date=request.end_date,
            variants=request.variants,
            data_sources=request.data_sources,
            limit_per_code=request.limit_per_code,
        )

        # Convert to response format
        observations_dict = {}
        total_count = 0
        for code, rows in grouped_results.items():
            observations_dict[code] = [
                ObservationQueryItem(
                    id=row.id,
                    code=row.code,
                    variant=row.variant,
                    value_integer=row.value_integer,
                    value_decimal=row.value_decimal,
                    value_string=row.value_string,
                    value_boolean=row.value_boolean,
                    effective_at=row.effective_at,
                    unit=row.unit,
                    data_source=row.data_source,
                    icon=row.icon,
                    status=row.status,
                    description=row.description,
                )
                for row in rows
            ]
            total_count += len(rows)

        return ObservationQueryGroupedResponse(
            observations=observations_dict,
            count=total_count,
        )
    else:
        results = repo.get_by_codes_and_date_range(
            user_id=current_user.id,
            codes=request.codes,
            start_date=request.start_date,
            end_date=request.end_date,
            variants=request.variants,
            data_sources=request.data_sources,
            limit_per_code=request.limit_per_code,
        )

        observations = [
            ObservationQueryItem(
                id=row.id,
                code=row.code,
                variant=row.variant,
                value_integer=row.value_integer,
                value_decimal=row.value_decimal,
                value_string=row.value_string,
                value_boolean=row.value_boolean,
                effective_at=row.effective_at,
                unit=row.unit,
                data_source=row.data_source,
                icon=row.icon,
                status=row.status,
                description=row.description,
            )
            for row in results
        ]

        return ObservationQueryResponse(
            observations=observations,
            count=len(observations),
        )


@router.get("", response_model=ObservationListResponse)
def list_observations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    code: Optional[str] = Query(default=None, description="Filter by observation code"),
    variant: Optional[str] = Query(default=None, description="Filter by variant"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    start_date: Optional[datetime] = Query(default=None, description="Filter from this date"),
    end_date: Optional[datetime] = Query(default=None, description="Filter until this date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get paginated list of observations with optional filters"""
    service = ObservationService(db)
    return service.list_observations(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        code=code,
        variant=variant,
        category=category,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/latest/{code}", response_model=Optional[ObservationResponse])
def get_latest_observation(
    code: str,
    variant: Optional[str] = Query(default=None, description="Filter by variant"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the most recent observation for a given code and optional variant"""
    service = ObservationService(db)
    observation = service.get_latest_observation(current_user.id, code, variant)

    if not observation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No observation found for code '{code}'",
        )

    return observation


@router.get("/{observation_id}", response_model=ObservationResponse)
def get_observation(
    observation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific observation by ID"""
    service = ObservationService(db)

    try:
        return service.get_observation(current_user.id, observation_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/{observation_id}", response_model=ObservationResponse)
def update_observation(
    observation_id: UUID,
    request: ObservationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an observation"""
    service = ObservationService(db)

    try:
        return service.update_observation(current_user.id, observation_id, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{observation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_observation(
    observation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an observation"""
    service = ObservationService(db)

    try:
        service.delete_observation(current_user.id, observation_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
