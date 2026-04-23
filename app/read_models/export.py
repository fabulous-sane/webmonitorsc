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
  date_trunc('minute', cr.checked_at) AS bucket,
  AVG(cr.response_time_ms) AS response_time_ms,
  (
  ARRAY_AGG(cr.status ORDER BY cr.checked_at DESC)
)[1] AS status,
  BOOL_OR(cr.ssl_valid) AS ssl_valid,
  MIN(cr.ssl_days_left) AS ssl_days_left,
  MAX(cr.ssl_warning) AS ssl_warning,

  CASE
  WHEN MAX(cr.ssl_warning) = 'critical' THEN 'critical'
  WHEN MAX(cr.ssl_warning) = 'warning' THEN 'warning'
  WHEN BOOL_OR(cr.ssl_valid = false) THEN 'invalid'
  WHEN BOOL_OR(cr.ssl_valid = true) THEN 'ok'
  ELSE 'no_data'
END AS ssl_state,

CASE
  WHEN MAX(cr.ssl_warning) = 'critical' THEN 'bad'
  WHEN BOOL_OR(cr.ssl_valid) = false THEN 'bad'
  WHEN MAX(cr.ssl_warning) = 'warning' THEN 'warn'
  WHEN BOOL_OR(cr.ssl_valid) = true THEN 'good'
  ELSE 'warn'
END AS ssl_severity

FROM check_results cr
JOIN sites s ON s.id = cr.site_id

WHERE
  cr.site_id = :site_id
  AND s.user_id = :user_id
  AND cr.checked_at >= :cutoff

GROUP BY bucket
ORDER BY bucket ASC
        LIMIT 50000
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
