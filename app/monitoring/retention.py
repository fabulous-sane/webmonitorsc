# app/monitoring/retention.py
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

async def cleanup_old_checks(
    *,
    session: AsyncSession,
    keep_days: int = 30,
    batch_size: int = 1000,
) -> int:

    if keep_days <= 0:
        raise ValueError("keep_days must be positive")

    if batch_size > 5000:
        raise ValueError("batch_size too large")

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=keep_days)

    total_deleted = 0


    while True:
        stmt = text("""
            DELETE FROM check_results
            WHERE id IN (
                SELECT id FROM check_results
                WHERE checked_at < :cutoff
                ORDER BY checked_at ASC
                LIMIT :batch_size
            )
        """)

        result = await session.execute(
            stmt,
            {"cutoff": cutoff, "batch_size": batch_size},
        )

        deleted = result.rowcount or 0
        if deleted < 0:
            deleted = 0

        total_deleted += deleted
        logger.info(f"Retention deleted batch: {deleted}, total: {total_deleted}")

        if deleted < batch_size or total_deleted >= settings.MAX_DELETE:
            break

        await asyncio.sleep(0.1)

    deleted_value = total_deleted if total_deleted > 0 else None

    if total_deleted == 0:
        logger.info("Retention: nothing to delete")

    await session.execute(
        text("""
            INSERT INTO retention_meta (id, last_run_at, last_deleted_count)
            VALUES (1, :now, :deleted)
            ON CONFLICT (id)
            DO UPDATE SET
                last_run_at = :now,
                last_deleted_count = :deleted
        """),
        {"now": now, "deleted": deleted_value},
    )

    return total_deleted





