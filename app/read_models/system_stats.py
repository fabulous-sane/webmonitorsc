from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_system_status(session: AsyncSession) -> dict:

    stmt = text("""
        SELECT
            (SELECT COUNT(*) FROM sites WHERE is_active = true) AS active_sites,
            (SELECT COUNT(*) FROM sites WHERE is_active = false) AS archived_sites,
            (SELECT COUNT(*) FROM check_results
                WHERE checked_at >= now() - interval '24 hours') AS checks_24h
    """)

    result = await session.execute(stmt)
    row = result.mappings().first()

    return dict(row) if row else {}