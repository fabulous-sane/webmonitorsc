import random
from uuid import UUID
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
from app.core.database import AsyncSessionLocal
from app.monitoring.check_runner import CheckSiteUseCase
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

def add_site_job(
    *,
    scheduler: AsyncIOScheduler,
    site_id: UUID,
    interval_seconds: int,
    notification_service: NotificationService,
) -> None:
    async def job():
        try:
            async with AsyncSessionLocal() as session:
                use_case = CheckSiteUseCase(
                    session=session,
                    notification_service=notification_service,
                )
                await use_case.execute(site_id=site_id)
        except Exception:
            logger.exception("Check job failed for %s", site_id)

    scheduler.add_job(
        job,
        trigger="interval",
        seconds=interval_seconds + random.randint(0, interval_seconds // 5),
        id=f"site_{site_id}",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
        misfire_grace_time=30
    )