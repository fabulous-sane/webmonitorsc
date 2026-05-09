from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import Sequence, Mapping, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo


async def get_checks_for_export(
    *,
    session: AsyncSession,
    site_id: UUID,
    user_id: UUID,
    time_range: str,
) -> Sequence[Mapping[str, Any]]:

    now = datetime.now(timezone.utc)

    if time_range == "24h":
        cutoff = now - timedelta(hours=24)
    elif time_range == "7d":
        cutoff = now - timedelta(days=7)
    elif time_range == "30d":
        cutoff = now - timedelta(days=30)
    else:
        raise ValueError("Invalid range")
    stmt = text("""
WITH grouped AS (
  SELECT
    date_trunc('hour', cr.checked_at) AS hour,
    MAX(cr.checked_at) AS max_checked_at
  FROM check_results cr
  JOIN sites s ON s.id = cr.site_id
  WHERE
    cr.site_id = :site_id
    AND s.user_id = :user_id
    AND cr.checked_at >= :cutoff
  GROUP BY hour
)

SELECT
  g.hour AS checked_at,
  cr.status::text,
  cr.status_code,
  cr.response_time_ms AS avg_response_time_ms,
  cr.ssl_valid,
  cr.ssl_days_left,
  cr.ssl_warning,
  cr.ssl_error

FROM grouped g
JOIN check_results cr
  ON cr.site_id = :site_id
 AND cr.checked_at = g.max_checked_at
 AND cr.id = (
     SELECT id FROM check_results
     WHERE site_id = :site_id
     AND checked_at = g.max_checked_at
     ORDER BY id DESC
     LIMIT 1
 )

ORDER BY checked_at ASC
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
