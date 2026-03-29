import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Boolean,
    Integer,
    ForeignKey,
    TIMESTAMP,
    UniqueConstraint,
    CheckConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import Base
from app.monitoring.status import SiteStatus

if TYPE_CHECKING:
    from app.models.user import User


class Site(Base):
    __tablename__ = "sites"

    __table_args__ = (
        UniqueConstraint("user_id", "url", name="uq_sites_user_url"),
        UniqueConstraint("user_id", "name", name="uq_sites_user_name"),
        CheckConstraint(
            "check_interval >= 30 AND check_interval <= 3600",
            name="ck_site_check_interval_range"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="sites",
        lazy="selectin",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    check_interval: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    last_status: Mapped[SiteStatus | None] = mapped_column(
        SQLEnum(SiteStatus, name="site_status"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
