from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.repositories.sites import SitesRepository
from app.repositories.check_results import CheckResultsRepository
from app.services.monitoring_service import MonitoringService
from sqlalchemy.exc import IntegrityError
from app.services.exceptions import (
    SiteLimitExceeded,
    SiteAlreadyExists,
    SiteNotFound,
)

class SiteService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        monitoring_service: MonitoringService | None = None,
    ) -> None:
        self._session = session
        self._repo = SitesRepository(session)
        self._monitoring = monitoring_service

    async def create_site(
            self,
            *,
            user_id: UUID,
            name: str,
            url: str,
            check_interval: int,
    ):
        count = await self._repo.count_active_by_user(user_id)
        if count >= settings.MAX_SITES_PER_USER:
            raise SiteLimitExceeded()

        # ищем по name
        existing_by_name = await self._repo.get_by_user_and_name(
            user_id=user_id,
            name=name,
        )

        if existing_by_name:
            if not existing_by_name.is_active:
                existing_by_name.is_active = True
                existing_by_name.url = url
                existing_by_name.check_interval = check_interval
                existing_by_name.last_status = None
                await self._session.commit()

                if self._monitoring:
                    self._monitoring.activate_site(
                        site_id=existing_by_name.id,
                        interval_seconds=existing_by_name.check_interval,
                    )

                return existing_by_name

            raise SiteAlreadyExists()

        existing_by_url = await self._repo.get_by_user_and_url(
            user_id=user_id,
            url=url,
        )

        if existing_by_url:
            if not existing_by_url.is_active:
                existing_by_url.is_active = True
                existing_by_url.name = name
                existing_by_url.check_interval = check_interval
                existing_by_url.last_status = None
                await self._session.commit()

                if self._monitoring:
                    self._monitoring.activate_site(
                        site_id=existing_by_url.id,
                        interval_seconds=existing_by_url.check_interval, # type: ignore[arg-type]
                    )

                return existing_by_url

            raise SiteAlreadyExists()

        try:
            site = await self._repo.create(
                user_id=user_id,
                name=name,
                url=url,
                check_interval=check_interval,
            )
            await self._session.commit()

        except IntegrityError:
            await self._session.rollback()
            raise SiteAlreadyExists()

        if self._monitoring:
            self._monitoring.activate_site(
                site_id=site.id,
                interval_seconds=site.check_interval,
            )

        return site

    async def list_active_sites(self, user_id: UUID):
        return await self._repo.get_active_by_user(user_id)

    async def update_interval(
            self,
            *,
            site_id: UUID,
            user_id: UUID,
            check_interval: int,
    ) -> None:
        site = await self._repo.get_by_id(site_id)

        if not site or site.user_id != user_id:
            raise SiteNotFound()

        site.check_interval = check_interval
        await self._session.commit()

        if self._monitoring:
            self._monitoring.deactivate_site(site_id=site.id)
            self._monitoring.activate_site(
                site_id=site.id,
                interval_seconds=site.check_interval, # type: ignore[arg-type]
            )

    async def deactivate(
            self,
            *,
            site_id: UUID,
            user_id: UUID,
    ) -> None:
        site = await self._repo.get_by_id(site_id)

        if not site or site.user_id != user_id:
            raise SiteNotFound()

        await self._repo.deactivate(site)
        await self._session.commit()

        if self._monitoring:
            self._monitoring.deactivate_site(site_id=site.id)

    async def reactivate(
            self,
            *,
            site_id: UUID,
            user_id: UUID,
    ) -> None:

        site = await self._repo.get_by_id(site_id)

        if not site or site.user_id != user_id:
            raise SiteNotFound()

        if site.is_active:
            return

        site.is_active = True
        await self._session.commit()

        if self._monitoring:
            self._monitoring.activate_site(
                site_id=site.id,
                interval_seconds=site.check_interval,
            )

    async def get_site_uptime(
        self,
        *,
        site_id: UUID,
        user_id: UUID,
        hours: int = 24,
    ) -> float:
        site = await self._repo.get_by_id(site_id)

        if not site or site.user_id != user_id:
            raise SiteNotFound()

        repo = CheckResultsRepository(self._session)

        return await repo.get_uptime_percent(
            site_id=site_id,
            hours=hours,
        )

    async def get_history(
        self,
        *,
        site_id: UUID,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ):
        site = await self._repo.get_by_id(site_id)

        if not site or site.user_id != user_id:
            raise SiteNotFound()

        repo = CheckResultsRepository(self._session)

        return await repo.get_history(
            site_id=site_id,
            limit=limit,
            offset=offset,
        )

    async def get_sites_for_telegram(
            self,
            *,
            telegram_chat_id: int,
    ):
        from app.repositories.users import UsersRepository

        users_repo = UsersRepository(self._session)
        user = await users_repo.get_by_telegram_chat_id(telegram_chat_id)

        if not user:
            return None, []

        sites = await self._repo.get_active_by_user(user.id)
        return user, sites

    async def get_site_details_for_telegram(
            self,
            *,
            telegram_chat_id: int,
            site_id: UUID,
    ):
        from app.repositories.users import UsersRepository

        users_repo = UsersRepository(self._session)
        user = await users_repo.get_by_telegram_chat_id(telegram_chat_id)

        if not user:
            return None, None

        site = await self._repo.get_by_id_and_user(site_id, user.id)
        if not site:
            return None, None

        results_repo = CheckResultsRepository(self._session)

        uptime_24 = await results_repo.get_uptime_percent(site_id=site.id, hours=24)
        uptime_7d = await results_repo.get_uptime_percent(site_id=site.id, hours=168)
        uptime_30d = await results_repo.get_uptime_percent(site_id=site.id, hours=720)
        last_checks = await results_repo.get_last_checks(site_id=site.id, limit=5)

        return site, {
            "uptime_24": uptime_24,
            "uptime_7d": uptime_7d,
            "uptime_30d": uptime_30d,
            "last_checks": last_checks,
        }