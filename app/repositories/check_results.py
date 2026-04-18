import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.check_result import CheckResult

class CheckResultsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_uptime_percent(
            self,
            *,
            site_id: uuid.UUID,
            hours: int = 24,
    ) -> float:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        stmt = text("""
               SELECT
                   CASE
                       WHEN COUNT(*) = 0 THEN 0
                       ELSE ROUND(
                           COUNT(*) FILTER (WHERE status = 'UP') * 100.0 / COUNT(*),
                           2
                       )
                   END AS uptime
               FROM check_results
               WHERE site_id = :site_id
                 AND checked_at >= :cutoff
           """)

        result = await self.session.execute(
            stmt,
            {"site_id": site_id, "cutoff": cutoff},
        )

        value = result.scalar()
        return float(value or 0.0)

    async def get_history(
        self,
        *,
        site_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ):
        stmt = (
            select(CheckResult)
            .where(CheckResult.site_id == site_id)
            .order_by(CheckResult.checked_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_last_checks(
        self,
        *,
        site_id: uuid.UUID,
        limit: int = 5,
    ):
        stmt = (
            select(CheckResult)
            .where(CheckResult.site_id == site_id)
            .order_by(CheckResult.checked_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_ssl(
            self,
            *,
            site_id: uuid.UUID,
    ):
        stmt = (
            select(
                CheckResult.ssl_valid,
                CheckResult.ssl_days_left,
                CheckResult.ssl_warning,
            )
            .where(CheckResult.site_id == site_id)
            .order_by(CheckResult.checked_at.desc())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        row = result.first()

        if not row:
            return None

        return {
            "ssl_valid": row[0],
            "ssl_days_left": row[1],
            "ssl_warning": row[2],
        }

