from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Juli Backend"
    VERSION: str = "1.0.0"
    DATABASE_URL: str

    # JWT Settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Environment API Keys
    OPENWEATHERMAP_API_KEY: Optional[str] = None
    AMBEE_API_KEY: Optional[str] = None

    # Push Notifications - APNs (iOS)
    APNS_PEM_FILE: Optional[str] = None
    APNS_USE_SANDBOX: bool = True

    # Push Notifications - FCM (Android)
    FCM_SERVICE_ACCOUNT_FILE: Optional[str] = None

    # Email (Postmark)
    POSTMARK_API_TOKEN: Optional[str] = None
    POSTMARK_EMAIL_FROM: str = "info@juli.co"
    BACKEND_PUBLIC_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()
