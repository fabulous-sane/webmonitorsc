from uuid import UUID
from pydantic import BaseModel, HttpUrl, field_validator, Field
from app.core.config import settings

class SiteCreate(BaseModel):
    name: str = Field(max_length=100)
    url: HttpUrl
    check_interval: int

    @field_validator("name")
    def normalize_name(cls, v):
        v = " ".join(v.strip().split())
        if not v:
            raise ValueError("Name cannot be empty")
        return v

    @field_validator("url")
    def normalize_url(cls, v: HttpUrl):
        return HttpUrl(str(v).rstrip("/"))

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