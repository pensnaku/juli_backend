"""Unit tests for authentication service"""
import pytest
from sqlalchemy.orm import Session
from app.features.auth.service import AuthService
from app.features.auth.domain.schemas import UserCreate
from app.shared.test_base import db


@pytest.mark.unit
@pytest.mark.auth
class TestAuthService:
    """Test authentication service logic"""

    def test_register_user_success(self, db: Session):
        """Test successful user registration"""
        # Arrange
        auth_service = AuthService(db)
        user_data = UserCreate(
            email="test@example.com",
            password="securepass123",
            full_name="Test User"
        )

        # Act
        user = auth_service.register_user(user_data)

        # Assert
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.hashed_password != "securepass123"  # Password should be hashed

    def test_register_user_duplicate_email(self, db: Session):
        """Test registration with duplicate email"""
        # Arrange
        auth_service = AuthService(db)
        user_data = UserCreate(
            email="test@example.com",
            password="securepass123",
            full_name="Test User"
        )
        auth_service.register_user(user_data)

        # Act & Assert
        with pytest.raises(ValueError, match="Email already registered"):
            auth_service.register_user(user_data)

    def test_authenticate_success(self, db: Session):
        """Test successful authentication"""
        # Arrange
        auth_service = AuthService(db)
        user_data = UserCreate(
            email="test@example.com",
            password="securepass123",
            full_name="Test User"
        )
        auth_service.register_user(user_data)

        # Act
        user = auth_service.authenticate("test@example.com", "securepass123")

        # Assert
        assert user is not None
        assert user.email == "test@example.com"

    def test_authenticate_wrong_password(self, db: Session):
        """Test authentication with wrong password"""
        # Arrange
        auth_service = AuthService(db)
        user_data = UserCreate(
            email="test@example.com",
            password="securepass123",
            full_name="Test User"
        )
        auth_service.register_user(user_data)

        # Act
        user = auth_service.authenticate("test@example.com", "wrongpassword")

        # Assert
        assert user is None

    def test_authenticate_nonexistent_user(self, db: Session):
        """Test authentication with non-existent user"""
        # Arrange
        auth_service = AuthService(db)

        # Act
        user = auth_service.authenticate("notexist@example.com", "password")

        # Assert
        assert user is None

    def test_create_access_token(self, db: Session):
        """Test JWT token creation"""
        # Arrange
        auth_service = AuthService(db)
        user_data = UserCreate(
            email="test@example.com",
            password="securepass123",
            full_name="Test User"
        )
        user = auth_service.register_user(user_data)

        # Act
        token = auth_service.create_access_token(user)

        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0