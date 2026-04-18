import logging
from uuid import UUID
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from app.monitoring.scheduler import add_site_job
from app.repositories.sites import SitesRepository
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class MonitoringService:
    def __init__(
        self,
        scheduler: AsyncIOScheduler,
        notification_service: NotificationService,
    ) -> None:
        self._scheduler = scheduler
        self._notification_service = notification_service

    def activate_site(self, *, site_id: UUID, interval_seconds: int) -> None:
        job_id = f"site_{site_id}"

        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)

        add_site_job(
            scheduler=self._scheduler,
            site_id=site_id,
            interval_seconds=interval_seconds,
            notification_service=self._notification_service,
        )

    def deactivate_site(self, *, site_id: UUID) -> None:
        job_id = f"site_{site_id}"
        job = self._scheduler.get_job(job_id)
        if job:
            self._scheduler.remove_job(job_id)

    async def bootstrap_active_sites(
        self,
        *,
        session: AsyncSession,
    ) -> None:
        repo = SitesRepository(session)
        sites = await repo.get_active_sites_for_scheduler()
        logger.info("Bootstrapping %d active sites", len(sites))
        for site in sites:
            try:
                self.activate_site(
                site_id=site.id,
                interval_seconds=site.check_interval,
            )
            except Exception:
                logger.exception("Failed to activate site %s", site.id)