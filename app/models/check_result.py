import uuid
from datetime import datetime
from sqlalchemy import Enum as SQLEnum, desc, Text
from sqlalchemy import (
    Integer,
    ForeignKey,
    TIMESTAMP,
    Boolean,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.models.base import Base
from app.monitoring.status import SiteStatus

class CheckResult(Base):
    __tablename__ = "check_results"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    site_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[SiteStatus] = mapped_column(
        SQLEnum(SiteStatus, name="site_status"),
        nullable=False,
    )

    status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    response_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    checked_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    ssl_expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    ssl_valid: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True
    )

    ssl_days_left: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ssl_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    ssl_warning: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index(
            "idx_check_results_site_checked_at",
            "site_id",
            desc("checked_at"),
        ),
        Index("ix_check_site_status", "site_id", "status"),
        Index("ix_check_time_only", "checked_at")
    )
