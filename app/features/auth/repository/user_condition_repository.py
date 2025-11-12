"""Repository for user condition database operations"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.features.auth.domain import UserCondition
from app.features.auth.domain.schemas import UserConditionCreate, UserConditionUpdate


class UserConditionRepository:
    """Handles all database operations for user conditions"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, condition_id: int) -> Optional[UserCondition]:
        """Get user condition by ID"""
        return self.db.query(UserCondition).filter(UserCondition.id == condition_id).first()

    def get_by_user_id(self, user_id: int) -> List[UserCondition]:
        """Get all conditions for a user"""
        return self.db.query(UserCondition).filter(UserCondition.user_id == user_id).all()

    def get_by_user_and_condition(
        self, user_id: int, condition_code: str
    ) -> Optional[UserCondition]:
        """Get a specific condition for a user"""
        return (
            self.db.query(UserCondition)
            .filter(
                UserCondition.user_id == user_id,
                UserCondition.condition_code == condition_code,
            )
            .first()
        )

    def create(self, user_id: int, condition_data: UserConditionCreate) -> UserCondition:
        """Create a new user condition"""
        condition = UserCondition(user_id=user_id, **condition_data.model_dump())
        self.db.add(condition)
        self.db.commit()
        self.db.refresh(condition)
        return condition

    def update(
        self, condition: UserCondition, update_data: UserConditionUpdate
    ) -> UserCondition:
        """Update user condition information"""
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(condition, field, value)
        self.db.commit()
        self.db.refresh(condition)
        return condition

    def upsert(self, user_id: int, condition_data: UserConditionCreate) -> UserCondition:
        """Create or update a user condition based on user_id and condition_code"""
        existing = self.get_by_user_and_condition(user_id, condition_data.condition_code)

        if existing:
            # Convert to update schema and update
            update_data = UserConditionUpdate(**condition_data.model_dump(exclude={"condition_code"}))
            return self.update(existing, update_data)
        else:
            # Create new
            return self.create(user_id, condition_data)

    def delete(self, condition: UserCondition) -> None:
        """Delete a user condition"""
        self.db.delete(condition)
        self.db.commit()

    def delete_by_user_and_condition(self, user_id: int, condition_code: str) -> bool:
        """Delete a specific condition for a user. Returns True if deleted, False if not found"""
        condition = self.get_by_user_and_condition(user_id, condition_code)
        if condition:
            self.delete(condition)
            return True
        return False