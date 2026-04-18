# app/monitoring/check_runner.py

import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.sites import SitesRepository
from app.monitoring.run_check import run_check
from app.monitoring.process_result import process_check_result
from app.services.notification_service import NotificationService
from app.monitoring.concurrency import check_semaphore
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class CheckSiteUseCase:
    def __init__(
        self,
        *,
        session: AsyncSession,
        notification_service: NotificationService,
    ) -> None:
        self._session = session
        self._notification_service = notification_service

    async def execute(self, *, site_id: UUID) -> None:
        async with check_semaphore:
            try:
                logger.info("Starting check for site %s", site_id)

                sites_repo = SitesRepository(self._session)
                site = await sites_repo.get_by_id_for_update(site_id)

                if site is None or not site.is_active:
                    logger.warning("Site %s skipped", site_id)
                    return

                now = datetime.now(timezone.utc)

                if site.last_checked_at is not None:
                    delta = (now - site.last_checked_at).total_seconds()

                    if delta < site.check_interval * 0.8:
                        logger.debug("Skipped duplicate check for site %s", site_id)
                        return

                raw = await run_check(url=site.url)

                result = await process_check_result(
                    session=self._session,
                    site=site,
                    raw=raw,
                )

                site.last_checked_at = now
                await self._session.commit()

                if (
                        self._notification_service
                        and result.notify_payload
                        and site.user.telegram_chat_id
                ):
                    try:
                        await self._notification_service.notify(
                        payload=result.notify_payload,
                        chat_id=site.user.telegram_chat_id,
                        session=self._session,
                        )
                    except Exception:
                        logger.exception("Notification failed AFTER commit (site_id=%s, payload=%s)",
                            site_id,
                            result.notify_payload
                            )

                logger.info("Finished check for site %s (status_changed=%s)", site_id, result.status_changed)

            except Exception:
                logger.exception("Check failed for site %s", site_id)
                await self._session.rollback()