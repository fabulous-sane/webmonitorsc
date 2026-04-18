from pydantic_settings import BaseSettings
class Settings(BaseSettings):

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

    FRONTEND_URL: str = "http://localhost:5173"
    DATABASE_URL: str
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    SENDGRID_API_KEY: str | None = None
    EMAIL_FROM: str | None = None
    RETRY_COUNT: int = 2
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
    SSL_WARNING_DAYS: int = 7
    SSL_CRITICAL_DAYS: int = 3

    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: int | None = None

    ENV: str = "prod"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "https://webmonitorsc.vercel.app",
    ]

settings = Settings()
