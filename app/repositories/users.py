import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UsersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, *, email: str, password_hash: str) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_email_confirm_token(
        self,
        token_hash: str,
    ) -> Optional[User]:
        stmt = select(User).where(User.email_confirm_token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_password_reset_token(
        self,
        token_hash: str,
    ) -> Optional[User]:
        stmt = select(User).where(
            User.password_reset_token_hash == token_hash
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users_with_telegram(self) -> list[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_chat_id.is_not(None))
        )
        return list(result.scalars().all())

    async def set_telegram_chat_id(
        self,
        *,
        user_id: uuid.UUID,
        chat_id: int,
    ) -> None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.telegram_chat_id = chat_id

    async def get_by_telegram_chat_id(self, chat_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_chat_id == chat_id)
        )
        return result.scalar_one_or_none()
