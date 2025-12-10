"""Service layer for medication business logic"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.features.auth.repository import UserMedicationRepository, UserReminderRepository
from app.features.auth.domain.schemas import (
    UserMedicationCreate,
    UserMedicationUpdate,
    UserMedicationResponse,
)


class MedicationService:
    """Service for managing user medications"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = UserMedicationRepository(db)
        self.reminder_repo = UserReminderRepository(db)

    def get_all(self, user_id: int, include_inactive: bool = False) -> List[UserMedicationResponse]:
        """Get all medications for a user"""
        medications = self.repo.get_by_user_id(user_id, active_only=not include_inactive)
        return [UserMedicationResponse.model_validate(med) for med in medications]

    def get_by_id(self, user_id: int, medication_id: int) -> Optional[UserMedicationResponse]:
        """Get a specific medication by ID"""
        medication = self.repo.get_by_id(medication_id)
        if medication and medication.user_id == user_id:
            return UserMedicationResponse.model_validate(medication)
        return None

    def create(self, user_id: int, request: UserMedicationCreate) -> UserMedicationResponse:
        """Create a new medication with optional notification reminders"""
        medication = self.repo.create(
            user_id=user_id,
            medication_name=request.medication_name,
            dosage=request.dosage,
            times_per_day=request.times_per_day,
            notes=request.notes,
        )

        # Create reminders for notification times
        if request.notification_times:
            self.reminder_repo.create_medication_reminders(
                user_id=user_id,
                medication_id=medication.id,
                times=request.notification_times,
            )

        self.db.commit()
        self.db.refresh(medication)
        return UserMedicationResponse.model_validate(medication)

    def update(
        self,
        user_id: int,
        medication_id: int,
        request: UserMedicationUpdate,
    ) -> Optional[UserMedicationResponse]:
        """Update a medication"""
        medication = self.repo.get_by_id(medication_id)
        if not medication or medication.user_id != user_id:
            return None

        # Handle notification_times separately
        update_data = request.model_dump(exclude_unset=True, exclude={"notification_times"})
        if update_data:
            self.repo.update(medication_id, **update_data)

        # Update reminders if notification_times is provided
        if request.notification_times is not None:
            # Delete existing reminders for this medication
            self.reminder_repo.delete_by_medication_id(medication_id)
            # Create new reminders
            if request.notification_times:
                self.reminder_repo.create_medication_reminders(
                    user_id=user_id,
                    medication_id=medication_id,
                    times=request.notification_times,
                )

        self.db.commit()
        self.db.refresh(medication)
        return UserMedicationResponse.model_validate(medication)

    def delete(self, user_id: int, medication_id: int) -> bool:
        """Delete a medication and its associated reminders"""
        medication = self.repo.get_by_id(medication_id)
        if not medication or medication.user_id != user_id:
            return False

        # Reminders are deleted via cascade, but let's be explicit
        self.reminder_repo.delete_by_medication_id(medication_id)
        self.repo.delete(medication_id)
        self.db.commit()
        return True