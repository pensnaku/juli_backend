"""API router for medications feature"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_user
from app.features.auth.domain.entities import User
from app.features.auth.domain.schemas import (
    UserMedicationCreate,
    UserMedicationUpdate,
    UserMedicationResponse,
)
from app.features.medication.service import MedicationService


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