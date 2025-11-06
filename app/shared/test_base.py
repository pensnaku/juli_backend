"""Base classes and fixtures for testing"""

from typing import Generator, Dict
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.database import Base, get_db
from app.main import app
from app.features.auth.domain.models import User
from app.features.auth.service import AuthService, JWTService
from app.features.auth.domain.schemas import UserCreate

# Use in-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override"""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# === Authentication Test Fixtures ===


@pytest.fixture
def test_user(db: Session) -> User:
    """
    Create a test user in the database

    Returns:
        User object with credentials:
        - email: test@example.com
        - password: testpassword123
    """
    auth_service = AuthService(db)
    user_data = UserCreate(
        email="test@example.com",
        password="testpassword123",
        full_name="Test User"
    )
    return auth_service.register_user(user_data)


@pytest.fixture
def test_superuser(db: Session) -> User:
    """
    Create a test superuser in the database

    Returns:
        User object with admin privileges
    """
    auth_service = AuthService(db)
    user_data = UserCreate(
        email="admin@example.com",
        password="adminpassword123",
        full_name="Admin User"
    )
    user = auth_service.register_user(user_data)
    user.is_superuser = True
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """
    Create a JWT token for the test user

    Args:
        test_user: Test user fixture

    Returns:
        Valid JWT access token
    """
    return JWTService.create_user_token(
        user_id=test_user.id,
        email=test_user.email
    )


@pytest.fixture
def test_superuser_token(test_superuser: User) -> str:
    """
    Create a JWT token for the test superuser

    Args:
        test_superuser: Test superuser fixture

    Returns:
        Valid JWT access token for admin user
    """
    return JWTService.create_user_token(
        user_id=test_superuser.id,
        email=test_superuser.email
    )


@pytest.fixture
def auth_headers(test_user_token: str) -> Dict[str, str]:
    """
    Create authorization headers with bearer token for regular user

    Args:
        test_user_token: JWT token for test user

    Returns:
        Dictionary with Authorization header
    """
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def admin_auth_headers(test_superuser_token: str) -> Dict[str, str]:
    """
    Create authorization headers with bearer token for admin user

    Args:
        test_superuser_token: JWT token for admin user

    Returns:
        Dictionary with Authorization header
    """
    return {"Authorization": f"Bearer {test_superuser_token}"}


@pytest.fixture
def authenticated_client(client: TestClient, auth_headers: Dict[str, str]) -> TestClient:
    """
    Test client with authentication headers pre-configured

    Args:
        client: Base test client
        auth_headers: Authentication headers

    Returns:
        TestClient with default auth headers
    """
    client.headers.update(auth_headers)
    return client
