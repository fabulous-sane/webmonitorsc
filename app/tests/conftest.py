import pytest_asyncio
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.site import Site
from app.models.user import User

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(DATABASE_URL, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def user(session):
    user = User(
        id=uuid4(),
        email="test@test.com",
        password_hash="test",
        is_active=True,
        is_verified=True,
    )

    session.add(user)
    await session.flush()  # ← КЛЮЧЕВОЙ МОМЕНТ

    return user


@pytest_asyncio.fixture
async def site(session, user):
    site = Site(
        id=uuid4(),
        user_id=user.id,
        name="test",
        url="https://example.com",
        check_interval=60,
        is_active=True,
        last_status=None,
    )

    session.add(site)
    await session.commit()

    return site