import uuid

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.models.telegram_link_token import TelegramLinkToken


class TelegramTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, *, user_id, token: str):
        obj = TelegramLinkToken(
            user_id=user_id,
            token=token,
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_by_token(self, token: str):
        result = await self.session.execute(
            select(TelegramLinkToken).where(
                TelegramLinkToken.token == token
            )
        )
        obj = result.scalar_one_or_none()

        if not obj:
            return None

        if obj.expires_at < datetime.now(timezone.utc):
            await self.delete(token)
            return None

        return obj

    async def delete(self, token: str):
        await self.session.execute(
            delete(TelegramLinkToken).where(
                TelegramLinkToken.token == token
            )
        )

    async def delete_by_user(self, user_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(TelegramLinkToken).where(
                TelegramLinkToken.user_id == user_id
            )
        )
