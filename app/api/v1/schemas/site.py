from uuid import UUID
from pydantic import BaseModel, HttpUrl, field_validator
from app.core.config import settings

class SiteCreate(BaseModel):
    name: str
    url: HttpUrl
    check_interval: int

    @field_validator("check_interval")
    @classmethod
    def validate_interval(cls, v: int) -> int:
        if not (settings.MIN_CHECK_INTERVAL <= v <= settings.MAX_CHECK_INTERVAL):
            raise ValueError(
                f"check_interval must be between "
                f"{settings.MIN_CHECK_INTERVAL} and {settings.MAX_CHECK_INTERVAL} seconds"
            )
        return v

class SiteOut(BaseModel):
    id: UUID
    name: str
    url: HttpUrl
    check_interval: int
    is_active: bool

    class Config:
        from_attributes = True

class SiteIntervalUpdate(BaseModel):
    check_interval: int

    @field_validator("check_interval")
    @classmethod
    def validate_interval(cls, v: int) -> int:
        if not (settings.MIN_CHECK_INTERVAL <= v <= settings.MAX_CHECK_INTERVAL):
            raise ValueError(
                f"check_interval must be between "
                f"{settings.MIN_CHECK_INTERVAL} and {settings.MAX_CHECK_INTERVAL} seconds"
            )
        return v