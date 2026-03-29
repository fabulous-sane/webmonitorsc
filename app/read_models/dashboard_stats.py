# app/read_models/dashboard_stats.py

from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_overview(
    session: AsyncSession,
    user_id: UUID,
) -> list[dict]:

    stmt = text("""
        SELECT
            s.id AS site_id,
            s.name,
            s.url,
            s.last_status,
            s.check_interval,
            s.is_active,
            cr.checked_at AS last_checked_at,

            stats_24.uptime_24h,
            stats_7.uptime_7d,
            stats_30.uptime_30d

        FROM sites s

        LEFT JOIN LATERAL (
            SELECT checked_at
            FROM check_results
            WHERE site_id = s.id
            ORDER BY checked_at DESC
            LIMIT 1
        ) cr ON true

        LEFT JOIN (
            SELECT
                site_id,
                COUNT(*) FILTER (WHERE status = 'UP') * 100.0 /
                NULLIF(COUNT(*), 0) AS uptime_24h
            FROM check_results
            WHERE checked_at >= now() - interval '24 hours'
            GROUP BY site_id
        ) stats_24 ON stats_24.site_id = s.id

        LEFT JOIN (
            SELECT
                site_id,
                COUNT(*) FILTER (WHERE status = 'UP') * 100.0 /
                NULLIF(COUNT(*), 0) AS uptime_7d
            FROM check_results
            WHERE checked_at >= now() - interval '7 days'
            GROUP BY site_id
        ) stats_7 ON stats_7.site_id = s.id

        LEFT JOIN (
            SELECT
                site_id,
                COUNT(*) FILTER (WHERE status = 'UP') * 100.0 /
                NULLIF(COUNT(*), 0) AS uptime_30d
            FROM check_results
            WHERE checked_at >= now() - interval '30 days'
            GROUP BY site_id
        ) stats_30 ON stats_30.site_id = s.id

        WHERE
            s.user_id = :user_id

        ORDER BY s.created_at;
    """)

    result = await session.execute(
        stmt,
        {
            "user_id": user_id,
        },
    )

    return [dict(row) for row in result.mappings().all()]

async def get_site_checks(
    session: AsyncSession,
    *,
    site_id: UUID,
    user_id: UUID,
    range: str,
) -> list[dict]:

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
            cr.status,
            cr.checked_at,
            cr.response_time_ms
        FROM check_results cr
        JOIN sites s ON s.id = cr.site_id
        WHERE
            cr.site_id = :site_id
            AND s.user_id = :user_id
            AND cr.checked_at >= :cutoff
        ORDER BY cr.checked_at ASC;
    """)

    result = await session.execute(
        stmt,
        {
            "site_id": site_id,
            "user_id": user_id,
            "cutoff": cutoff,
        },
    )

    return [dict(row) for row in result.mappings().all()]
