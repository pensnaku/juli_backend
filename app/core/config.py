from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Juli Backend"
    VERSION: str = "1.0.0"
    DATABASE_URL: str

    # JWT Settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 260000

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
