# app/read_models/dashboard_stats.py

from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.monitoring.health_calc import compute_health
from app.utils.ssl_state import resolve_ssl_state

async def get_overview(
    session: AsyncSession,
    user_id: UUID,
) -> list[dict]:

    stmt = text("""
SELECT
    s.id AS site_id,
    s.name,
    s.url,
    cr.status::text AS last_status,
    s.check_interval,
    s.is_active,

    cr.checked_at AS last_checked_at,
    cr.ssl_valid,
    cr.ssl_days_left,
    cr.ssl_warning,
    cr.ssl_expires_at,

    COALESCE(stats_24.uptime_24h, 0) AS uptime_24h,
    COALESCE(stats_7.uptime_7d, 0) AS uptime_7d,
    COALESCE(stats_30.uptime_30d, 0) AS uptime_30d,

    stats_24.p95_latency AS p95_latency,
    stats_24.error_rate AS error_rate

FROM sites s

LEFT JOIN LATERAL (
    SELECT
        checked_at,
        status,
        ssl_valid,
        ssl_days_left,
        ssl_warning,
        ssl_expires_at
    FROM check_results
    WHERE check_results.site_id = s.id
    ORDER BY checked_at DESC
    LIMIT 1
) cr ON true

LEFT JOIN LATERAL (
    SELECT
        COUNT(*) FILTER (WHERE status = 'UP') * 100.0 / NULLIF(COUNT(*),0) AS uptime_24h,

        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms)
        FILTER (WHERE response_time_ms IS NOT NULL) AS p95_latency,

        COUNT(*) FILTER (
          WHERE status IN ('DOWN','ERROR','TIMEOUT')
        ) * 100.0 / NULLIF(COUNT(*),0) AS error_rate

    FROM check_results
    WHERE site_id = s.id
      AND checked_at >= now() - interval '24 hours'
) stats_24 ON true

LEFT JOIN (
    SELECT site_id,
           COUNT(*) FILTER (WHERE status = 'UP') * 100.0 / NULLIF(COUNT(*),0) AS uptime_7d
    FROM check_results
    WHERE checked_at >= now() - interval '7 days'
    GROUP BY site_id
) stats_7 ON stats_7.site_id = s.id

LEFT JOIN (
    SELECT site_id,
           COUNT(*) FILTER (WHERE status = 'UP') * 100.0 / NULLIF(COUNT(*),0) AS uptime_30d
    FROM check_results
    WHERE checked_at >= now() - interval '30 days'
    GROUP BY site_id
) stats_30 ON stats_30.site_id = s.id

WHERE s.user_id = :user_id
ORDER BY s.created_at DESC;
    """)

    result = await session.execute(stmt, {"user_id": user_id})
    rows = [dict(r) for r in result.mappings().all()]

    for r in rows:
        ssl_state = resolve_ssl_state(
            r.get("ssl_valid"),
            r.get("ssl_warning"),
            r.get("url"),
        )

        r["ssl_state"] = ssl_state

        r["health"] = compute_health(
            r.get("last_status"),
            ssl_state,
        ) or "no_data"

    return rows

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
  date_trunc('minute', cr.checked_at) AS checked_at,
  AVG(cr.response_time_ms)::float AS avg_response_time_ms,
  MIN(cr.ssl_valid) AS ssl_valid,
  MIN(cr.ssl_days_left) AS ssl_days_left,
  MAX(cr.ssl_warning) AS ssl_warning,
  MAX(s.url) AS url,
  (
ARRAY_AGG(cr.status::text ORDER BY cr.checked_at DESC)
)[1] AS status

FROM check_results cr
JOIN sites s ON s.id = cr.site_id

WHERE
  cr.site_id = :site_id
  AND s.user_id = :user_id
  AND cr.checked_at >= :cutoff

GROUP BY date_trunc('minute', cr.checked_at)
ORDER BY checked_at ASC
    """)

    result = await session.execute(
        stmt,
        {
            "site_id": site_id,
            "user_id": user_id,
            "cutoff": cutoff,
        },
    )

    rows = [dict(row) for row in result.mappings().all()]

    for r in rows:
        ssl_state = resolve_ssl_state(
            r.get("ssl_valid"),
            r.get("ssl_warning"),
            r.get("url"),
        )

        r["ssl_state"] = ssl_state

        r["health"] = compute_health(
            r.get("last_status"),
            ssl_state,
        ) or "no_data"

    return rows


