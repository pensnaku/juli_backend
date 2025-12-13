"""Repository for user medications"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.features.auth.domain.entities import UserMedication


class UserMedicationRepository:
    """Repository for managing user medications"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, medication_id: int) -> Optional[UserMedication]:
        """Get a medication by ID"""
        return self.db.query(UserMedication).filter(UserMedication.id == medication_id).first()

    def get_by_user_id(self, user_id: int, active_only: bool = True) -> List[UserMedication]:
        """Get all medications for a user"""
        query = self.db.query(UserMedication).filter(UserMedication.user_id == user_id)
        if active_only:
            query = query.filter(UserMedication.is_active == True)
        return query.all()

    def create(
        self,
        user_id: int,
        medication_name: str,
        dosage: Optional[str] = None,
        times_per_day: Optional[int] = None,
        notes: Optional[str] = None,
        reminder_enabled: bool = True,
    ) -> UserMedication:
        """Create a new medication"""
        medication = UserMedication(
            user_id=user_id,
            medication_name=medication_name,
            dosage=dosage,
            times_per_day=times_per_day,
            notes=notes,
            is_active=True,
            reminder_enabled=reminder_enabled,
        )
        self.db.add(medication)
        self.db.flush()
        return medication

    def update(self, medication_id: int, **kwargs) -> Optional[UserMedication]:
        """Update a medication"""
        medication = self.get_by_id(medication_id)
        if medication:
            for key, value in kwargs.items():
                if hasattr(medication, key):
                    setattr(medication, key, value)
            self.db.flush()
        return medication

    def deactivate(self, medication_id: int) -> bool:
        """Deactivate a medication"""
        medication = self.get_by_id(medication_id)
        if medication:
            medication.is_active = False
            self.db.flush()
            return True
        return False

    def delete(self, medication_id: int) -> bool:
        """Delete a medication"""
        medication = self.get_by_id(medication_id)
        if medication:
            self.db.delete(medication)
            self.db.flush()
            return True
        return False