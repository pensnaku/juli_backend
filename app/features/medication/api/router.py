"""API router for medications feature"""
from typing import List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_user
from app.features.auth.domain.entities import User
from app.features.auth.domain.schemas import (
    UserMedicationCreate,
    UserMedicationUpdate,
    UserMedicationResponse,
)
from app.features.medication.service import MedicationService, MedicationAdherenceService
from app.features.medication.domain.schemas import (
    MedicationAdherenceUpdate,
    MedicationAdherenceResponse,
    DailyAdherenceResponse,
    AdherenceHistoryResponse,
    BulkAdherenceUpdate,
)


router = APIRouter()


@router.get("", response_model=List[UserMedicationResponse])
def get_medications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all medications for the current user (both active and inactive)"""
    service = MedicationService(db)
    return service.get_all(current_user.id)


@router.get("/{medication_id}", response_model=UserMedicationResponse)
def get_medication(
    medication_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific medication by ID"""
    service = MedicationService(db)
    medication = service.get_by_id(current_user.id, medication_id)

    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )

    return medication


@router.post("", response_model=UserMedicationResponse, status_code=status.HTTP_201_CREATED)
def create_medication(
    request: UserMedicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new medication for the current user"""
    service = MedicationService(db)
    return service.create(current_user.id, request)


@router.patch("/{medication_id}", response_model=UserMedicationResponse)
def update_medication(
    medication_id: int,
    request: UserMedicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a medication"""
    service = MedicationService(db)
    medication = service.update(current_user.id, medication_id, request)

    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )

    return medication


@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    medication_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a medication"""
    service = MedicationService(db)
    success = service.delete(current_user.id, medication_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )


# ============== Adherence Endpoints ==============


@router.get("/adherence/daily/{target_date}", response_model=DailyAdherenceResponse)
def get_daily_adherence(
    target_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get adherence status for all active medications for a specific date.

    Returns all medications with their adherence status for the given date.
    Medications without an existing adherence record will be initialized as NOT_SET.
    """
    service = MedicationAdherenceService(db)
    return service.get_daily_adherence(current_user.id, target_date)


@router.put("/adherence/{medication_id}/{target_date}", response_model=MedicationAdherenceResponse)
def update_medication_adherence(
    medication_id: int,
    target_date: date,
    request: MedicationAdherenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update adherence status for a specific medication on a specific date.

    Status options:
    - taken: Medication was taken as prescribed
    - not_taken: Medication was not taken
    - partly_taken: Medication was partially taken
    - not_set: Status not yet recorded (default)
    """
    service = MedicationAdherenceService(db)
    result = service.update_adherence(
        user_id=current_user.id,
        medication_id=medication_id,
        target_date=target_date,
        status=request.status,
        notes=request.notes,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )

    return result


@router.put("/adherence/bulk", response_model=DailyAdherenceResponse)
def bulk_update_adherence(
    request: BulkAdherenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update adherence status for multiple medications at once.

    Useful for updating all medications for a day in a single request.
    """
    service = MedicationAdherenceService(db)

    updates = [
        {
            "medication_id": item.medication_id,
            "status": item.status,
            "notes": item.notes,
        }
        for item in request.updates
    ]

    return service.bulk_update_adherence(
        user_id=current_user.id,
        target_date=request.target_date,
        updates=updates,
    )


@router.get("/adherence/history", response_model=AdherenceHistoryResponse)
def get_adherence_history(
    days: int = Query(default=7, ge=1, le=30, description="Number of days of history (max 30)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get adherence history for the past N days.

    Returns daily adherence records with summary statistics.
    """
    service = MedicationAdherenceService(db)
    return service.get_adherence_history(current_user.id, days)