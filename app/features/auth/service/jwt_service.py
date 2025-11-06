"""JWT token service for authentication"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings
from app.features.auth.domain.schemas import TokenData


class JWTService:
    """Service for creating and validating JWT tokens"""

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token

        Args:
            data: Dictionary containing claims to encode in the token
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        now = datetime.now(timezone.utc)

        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": now,
            "type": "access"
        })

        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> Optional[dict]:
        """
        Decode and verify a JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded payload dictionary or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError:
            return None

    @staticmethod
    def extract_token_data(token: str) -> Optional[TokenData]:
        """
        Extract and validate token data

        Args:
            token: JWT token string

        Returns:
            TokenData object or None if invalid
        """
        payload = JWTService.decode_access_token(token)
        if payload is None:
            return None

        email: Optional[str] = payload.get("sub")
        user_id: Optional[int] = payload.get("user_id")

        if email is None:
            return None

        return TokenData(email=email, user_id=user_id)

    @staticmethod
    def create_user_token(user_id: int, email: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create an access token for a specific user

        Args:
            user_id: User's database ID
            email: User's email address
            expires_delta: Optional custom expiration time

        Returns:
            JWT access token
        """
        token_data = {
            "sub": email,
            "user_id": user_id
        }
        return JWTService.create_access_token(token_data, expires_delta)