from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, token: RefreshToken) -> None:
        self.session.add(token)

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        stmt = (
            select(RefreshToken)
            .where(RefreshToken.jti == jti)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, token: RefreshToken) -> None:
        token.is_revoked = True
