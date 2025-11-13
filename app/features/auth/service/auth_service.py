"""Authentication service - contains business logic"""
from typing import Optional
from datetime import timedelta
from sqlalchemy.orm import Session
from app.features.auth.domain import User, UserCreate, UserUpdate
from app.features.auth.repository import UserRepository
from app.features.auth.service.jwt_service import JWTService
from app.core.security import verify_password, get_password_hash
from app.core.config import settings


class AuthService:
    """Service for authentication and user management operations"""

    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def register_user(self, user_data: UserCreate) -> User:
        """
        Register a new user

        Args:
            user_data: User registration data

        Returns:
            Created user

        Raises:
            ValueError: If email already exists or validations fail
        """
        # Check if user already exists
        if self.repository.exists_by_email(user_data.email):
            raise ValueError("Email already registered")

        # Validate terms and age confirmation
        if not user_data.terms_accepted:
            raise ValueError("You must accept the terms and conditions")

        if not user_data.age_confirmed:
            raise ValueError("You must confirm you meet the minimum age requirement")

        # Hash password
        hashed_password = get_password_hash(user_data.password)

        # Create user
        user = self.repository.create(
            email=user_data.email,
            hashed_password=hashed_password,
            terms_accepted=user_data.terms_accepted,
            age_confirmed=user_data.age_confirmed
        )

        return user

    def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password

        Args:
            email: User email
            password: Plain text password

        Returns:
            User if authentication successful, None otherwise
        """
        user = self.repository.get_by_email(email)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user

    def create_access_token(self, user: User) -> str:
        """
        Create JWT access token for user

        Args:
            user: User to create token for

        Returns:
            JWT access token
        """
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = JWTService.create_user_token(
            user_id=user.id,
            email=user.email,
            expires_delta=access_token_expires
        )
        return access_token

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.repository.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.repository.get_by_email(email)

    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """
        Update user information

        Args:
            user_id: User ID
            user_data: Updated user data

        Returns:
            Updated user or None if not found
        """
        user = self.repository.get_by_id(user_id)

        if not user:
            return None

        # Update fields
        if user_data.email:
            # Check if new email already exists
            existing = self.repository.get_by_email(user_data.email)
            if existing and existing.id != user_id:
                raise ValueError("Email already in use")
            user.email = user_data.email

        if user_data.full_name is not None:
            user.full_name = user_data.full_name

        if user_data.password:
            user.hashed_password = get_password_hash(user_data.password)

        return self.repository.update(user)

    def validate_email(self, email: str) -> dict:
        """
        Validate email format and availability

        Args:
            email: Email address to validate

        Returns:
            Dictionary with validation results:
                - is_valid: Whether email format is valid (always True if this method is called after Pydantic validation)
                - is_available: Whether email is not already registered
                - message: Descriptive message
        """
        # Check if email already exists
        exists = self.repository.exists_by_email(email)

        if exists:
            return {
                "is_valid": True,
                "is_available": False,
                "message": "This email address is already registered"
            }
        else:
            return {
                "is_valid": True,
                "is_available": True,
                "message": "This email address is available"
            }