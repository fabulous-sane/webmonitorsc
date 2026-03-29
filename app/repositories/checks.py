import uuid
from typing import List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.check_result import CheckResult
from app.monitoring.status import SiteStatus


class ChecksRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_result(
        self,
        *,
        site_id: uuid.UUID,
        status: SiteStatus,
        status_code: int | None,
        response_time_ms: int | None,
    ) -> CheckResult:
        result = CheckResult(
            site_id=site_id,
            status=status,
            status_code=status_code,
            response_time_ms=response_time_ms,
        )
        self.session.add(result)
        await self.session.flush()
        return result

    async def get_last_by_site(
        self,
        site_id: uuid.UUID,
    ) -> Optional[CheckResult]:
        stmt = (
            select(CheckResult)
            .where(CheckResult.site_id == site_id)
            .order_by(desc(CheckResult.checked_at))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_recent_by_site(
        self,
        site_id: uuid.UUID,
        limit: int = 100,
    ) -> List[CheckResult]:
        stmt = (
            select(CheckResult)
            .where(CheckResult.site_id == site_id)
            .order_by(desc(CheckResult.checked_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_last_statuses(
            self,
            *,
            site_id: uuid.UUID,
            limit: int,
    ) -> list[SiteStatus]:
        stmt = (
            select(CheckResult.status)
            .where(CheckResult.site_id == site_id)
            .order_by(CheckResult.checked_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]
