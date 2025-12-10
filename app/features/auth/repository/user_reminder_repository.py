"""Repository for user reminder database operations"""
from typing import Optional, List
from datetime import time
from sqlalchemy.orm import Session
from app.features.auth.domain import UserReminder
from app.features.auth.domain.schemas import UserReminderCreate, UserReminderUpdate


class UserReminderRepository:
    """Handles all database operations for user reminders"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, reminder_id: int) -> Optional[UserReminder]:
        """Get user reminder by ID"""
        return self.db.query(UserReminder).filter(UserReminder.id == reminder_id).first()

    def get_by_user_id(self, user_id: int) -> List[UserReminder]:
        """Get all reminders for a user"""
        return self.db.query(UserReminder).filter(UserReminder.user_id == user_id).all()

    def get_active_by_user_id(self, user_id: int) -> List[UserReminder]:
        """Get all active reminders for a user"""
        return (
            self.db.query(UserReminder)
            .filter(UserReminder.user_id == user_id, UserReminder.is_active == True)
            .all()
        )

    def get_by_user_and_type(
        self, user_id: int, reminder_type: str
    ) -> List[UserReminder]:
        """Get all reminders of a specific type for a user"""
        return (
            self.db.query(UserReminder)
            .filter(
                UserReminder.user_id == user_id,
                UserReminder.reminder_type == reminder_type,
            )
            .all()
        )

    def create(self, user_id: int, reminder_data: UserReminderCreate) -> UserReminder:
        """Create a new user reminder"""
        reminder = UserReminder(user_id=user_id, **reminder_data.model_dump())
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    def create_many(
        self, user_id: int, reminders_data: List[UserReminderCreate]
    ) -> List[UserReminder]:
        """Create multiple reminders for a user"""
        reminders = [
            UserReminder(user_id=user_id, **reminder_data.model_dump())
            for reminder_data in reminders_data
        ]
        self.db.add_all(reminders)
        self.db.commit()
        for reminder in reminders:
            self.db.refresh(reminder)
        return reminders

    def update(
        self, reminder: UserReminder, update_data: UserReminderUpdate
    ) -> UserReminder:
        """Update user reminder information"""
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(reminder, field, value)
        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    def delete(self, reminder: UserReminder) -> None:
        """Delete a user reminder"""
        self.db.delete(reminder)
        self.db.commit()

    def delete_by_user_and_type(self, user_id: int, reminder_type: str) -> int:
        """Delete all reminders of a specific type for a user. Returns count of deleted reminders"""
        reminders = self.get_by_user_and_type(user_id, reminder_type)
        count = len(reminders)
        for reminder in reminders:
            self.db.delete(reminder)
        self.db.commit()
        return count

    def replace_reminders_by_type(
        self, user_id: int, reminder_type: str, new_reminders: List[UserReminderCreate]
    ) -> List[UserReminder]:
        """Replace all reminders of a type with new ones (useful for updating reminder times)"""
        # Delete existing reminders of this type
        self.delete_by_user_and_type(user_id, reminder_type)
        # Create new reminders
        return self.create_many(user_id, new_reminders)

    def get_by_medication_id(self, medication_id: int) -> List[UserReminder]:
        """Get all reminders for a specific medication"""
        return (
            self.db.query(UserReminder)
            .filter(UserReminder.medication_id == medication_id)
            .all()
        )

    def delete_by_medication_id(self, medication_id: int) -> int:
        """Delete all reminders for a specific medication. Returns count of deleted reminders"""
        reminders = self.get_by_medication_id(medication_id)
        count = len(reminders)
        for reminder in reminders:
            self.db.delete(reminder)
        self.db.flush()
        return count

    def create_medication_reminders(
        self, user_id: int, medication_id: int, times: List
    ) -> List[UserReminder]:
        """Create medication reminders for specific times"""
        from datetime import time as time_type
        reminders = []
        for t in times:
            reminder = UserReminder(
                user_id=user_id,
                medication_id=medication_id,
                reminder_type="medication_reminder",
                time=t,
                is_active=True,
            )
            self.db.add(reminder)
            reminders.append(reminder)
        self.db.flush()
        return reminders