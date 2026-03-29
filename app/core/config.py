from pydantic_settings import BaseSettings
from typing import ClassVar
class Settings(BaseSettings):
    FRONTEND_URL: str = "http://localhost:5173"
    DATABASE_URL: str
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    SENDGRID_API_KEY: str
    EMAIL_FROM: str
    RETRY_COUNT: ClassVar[int] = 2
    MAX_RETRIES: ClassVar[int] = 3
    BACKOFF_BASE: float = 0.5
    MIN_CHECK_INTERVAL: int = 60
    MAX_CHECK_INTERVAL: int = 3600
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 360
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MAX_SITES_PER_USER: int = 20
    MAX_CONCURRENT_CHECKS: int = 10
    FLAP_UP_THRESHOLD: int = 2
    FLAP_DOWN_THRESHOLD: int = 2
    RETENTION_DAYS: int = 10

    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: int

    ENV: str = "dev"
    DEBUG: bool = True
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    class Settings(BaseSettings):
        model_config = {
            "env_file": ".env",
            "extra": "ignore",
        }

settings = Settings()
