from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import Sequence, Mapping, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def get_checks_for_export(
    *,
    session: AsyncSession,
    site_id: UUID,
    user_id: UUID,
    range: str,
) -> Sequence[Mapping[str, Any]]:

    now = datetime.now(timezone.utc)

    if range == "24h":
        cutoff = now - timedelta(hours=24)
    elif range == "7d":
        cutoff = now - timedelta(days=7)
    elif range == "30d":
        cutoff = now - timedelta(days=30)
    else:
        raise ValueError("Invalid range")

    stmt = text("""
        SELECT
            cr.checked_at,
            cr.status,
            cr.status_code,
            cr.response_time_ms
        FROM check_results cr
        JOIN sites s ON s.id = cr.site_id
        WHERE
            cr.site_id = :site_id
            AND s.user_id = :user_id
            AND cr.checked_at >= :cutoff
        ORDER BY cr.checked_at ASC
        LIMIT 10000
    """)

    result = await session.execute(
        stmt,
        {
            "site_id": site_id,
            "user_id": user_id,
            "cutoff": cutoff,
        },
    )

    return result.mappings().all()
