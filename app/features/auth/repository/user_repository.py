"""Repository for user database operations"""
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from app.features.auth.domain import User
from app.features.auth.domain.entities.user_settings import UserSettings


class UserRepository:
    """Handles all database operations for users"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with conditions eagerly loaded"""
        return self.db.query(User).options(
            joinedload(User.settings),
            joinedload(User.conditions)
        ).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email with conditions eagerly loaded"""
        return self.db.query(User).options(
            joinedload(User.settings),
            joinedload(User.conditions)
        ).filter(User.email == email).first()

    def create(
        self,
        email: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        terms_accepted: bool = False,
        age_confirmed: bool = False,
        store_country: Optional[str] = None,
        store_region: Optional[str] = None,
    ) -> User:
        """Create a new user with optional initial settings"""
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            terms_accepted=terms_accepted,
            age_confirmed=age_confirmed
        )
        self.db.add(user)
        self.db.flush()  # Get user.id without committing

        # Create UserSettings if store location is provided
        if store_country or store_region:
            settings = UserSettings(
                user_id=user.id,
                store_country=store_country,
                store_region=store_region,
            )
            self.db.add(settings)

        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        """Update user information"""
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        """Delete a user"""
        self.db.delete(user)
        self.db.commit()

    def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        return self.db.query(User).filter(User.email == email).first() is not None