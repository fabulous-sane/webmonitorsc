# app/monitoring/retention.py
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def cleanup_old_checks(
    *,
    session: AsyncSession,
    keep_days: int = 30,
    batch_size: int = 1000,
) -> int:

    if keep_days <= 0:
        raise ValueError("keep_days must be positive")

    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)

    total_deleted = 0

    while True:
        stmt = text("""
            DELETE FROM check_results
            WHERE id IN (
                SELECT id FROM check_results
                WHERE checked_at < :cutoff
                LIMIT :batch_size
            )
        """)

        result = await session.execute(
            stmt,
            {"cutoff": cutoff, "batch_size": batch_size},
        )

        deleted = result.rowcount or 0
        total_deleted += deleted

        if deleted < batch_size:
            break

    return total_deleted