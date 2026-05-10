# app/read_models/dashboard_stats.py

from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.monitoring.health_calc import compute_health
from app.utils.ssl_state import resolve_ssl_state
from app.monitoring.status import SiteStatus

async def get_overview(
    session: AsyncSession,
    user_id: UUID,
) -> list[dict]:
    stmt = text("""
    SELECT
        s.id AS site_id,
        s.name,
        s.url,
        UPPER(cr.status::text) AS last_status,
        s.check_interval,
        s.is_active,

        cr.checked_at AS last_checked_at,
        cr.ssl_valid,
        cr.ssl_days_left,
        cr.ssl_warning,
        cr.ssl_error,        -- FIX
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
        ssl_error,
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
          AND checked_at >= NOW() - INTERVAL '24 hours'
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
        status = r.get("last_status")

        ssl_state = resolve_ssl_state(
            r.get("ssl_valid"),
            r.get("ssl_warning"),
            r.get("url"),
            r.get("ssl_error"),
        )

        r["ssl_state"] = ssl_state

        if status not in ("UP", "DOWN", "ERROR", "TIMEOUT"):
            r["health"] = "no_data"
        else:
            r["health"] = compute_health(status, ssl_state) or "no_data"

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
WITH bucketed AS (
  SELECT
    (
      date_trunc('minute', cr.checked_at)
      - (EXTRACT(MINUTE FROM cr.checked_at)::int %
          CASE
              WHEN :range = '24h' THEN 1
              WHEN :range = '7d' THEN 5
              ELSE 15
          END
        ) * INTERVAL '1 minute'
    ) AS bucket,
    cr.*
  FROM check_results cr
  JOIN sites s ON s.id = cr.site_id
  WHERE
    cr.site_id = :site_id
    AND s.user_id = :user_id
    AND cr.checked_at >= :cutoff
),

latest AS (
  SELECT DISTINCT ON (bucket)
    bucket,
    status,
    ssl_valid,
    ssl_warning,
    ssl_error,
    checked_at
  FROM bucketed
  ORDER BY bucket, checked_at DESC
),

agg AS (
  SELECT
    bucket,
    AVG(response_time_ms) FILTER (WHERE response_time_ms IS NOT NULL) AS avg_response_time_ms,
    MIN(ssl_days_left) AS ssl_days_left
  FROM bucketed
  GROUP BY bucket
)

SELECT
  l.bucket AS checked_at,
  COALESCE(a.avg_response_time_ms, 0) AS avg_response_time_ms,
  l.ssl_valid,
  a.ssl_days_left,
  l.ssl_warning,
  l.ssl_error,
  s.url,
  UPPER(l.status::text) AS status
FROM latest l
JOIN agg a ON a.bucket = l.bucket
JOIN sites s ON s.id = :site_id
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
        r["url"] = r.get("url") or ""
        status = (r.get("status") or "").upper()

        ssl_state = resolve_ssl_state(
            r.get("ssl_valid"),
            r.get("ssl_warning"),
            r.get("url"),
            r.get("ssl_error"),
        )

        r["ssl_state"] = ssl_state

        if status not in ("UP", "DOWN", "ERROR", "TIMEOUT"):
            r["health"] = "no_data"
        else:
            r["health"] = compute_health(status, ssl_state) or "no_data"

    return rows



