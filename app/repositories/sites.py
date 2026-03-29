import uuid
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.site import Site

class SitesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, site_id: uuid.UUID) -> Optional[Site]:
        result = await self.session.execute(
            select(Site).where(Site.id == site_id)
        )
        return result.scalar_one_or_none()

    async def get_active_by_user(
        self,
        user_id: uuid.UUID,
    ) -> List[Site]:
        stmt = select(Site).where(
            Site.user_id == user_id,
            Site.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_and_url(
        self,
        user_id: uuid.UUID,
        url: str,
    ) -> Optional[Site]:
        stmt = select(Site).where(
            Site.user_id == user_id,
            Site.url == url,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_and_name(self, user_id: uuid.UUID, name: str):
        stmt = select(Site).where(
            Site.user_id == user_id,
            Site.name == name,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        name: str,
        url: str,
        check_interval: int,
    ) -> Site:
        site = Site(
            user_id=user_id,
            name=name,
            url=url,
            check_interval=check_interval,
        )
        self.session.add(site)
        await self.session.flush()
        return site

    async def deactivate(self, site: Site) -> None:
        site.is_active = False

    async def get_active_sites_for_scheduler(self) -> list[Site]:
        stmt = select(Site).where(Site.is_active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_active_by_user(
            self,
            user_id: uuid.UUID,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Site)
            .where(
                Site.user_id == user_id,
                Site.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_id_for_update(self, site_id: uuid.UUID) -> Optional[Site]:
        stmt = (
            select(Site)
            .options(selectinload(Site.user))
            .where(Site.id == site_id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_user(
            self,
            site_id: uuid.UUID,
            user_id: uuid.UUID,
    ):
        result = await self.session.execute(
            select(Site).where(
                Site.id == site_id,
                Site.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()