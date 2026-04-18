from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


if settings.DATABASE_URL.startswith("postgresql://"):
    database_url = settings.DATABASE_URL.replace(
        "postgresql://",
        "postgresql+asyncpg://",
    )
else:
    database_url = settings.DATABASE_URL

engine = create_async_engine(
    database_url,
    isolation_level="READ COMMITTED",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
