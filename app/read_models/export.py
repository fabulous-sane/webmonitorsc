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
    range: str,
) -> Sequence[Mapping[str, Any]]:

    now = datetime.now(timezone.utc)

    if range == "24h":
        cutoff = datetime.now(ZoneInfo("Europe/Kyiv")).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).astimezone(timezone.utc)
    elif range == "7d":
        cutoff = now - timedelta(days=7)
    elif range == "30d":
        cutoff = now - timedelta(days=30)
    else:
        raise ValueError("Invalid range")

    stmt = text("""
SELECT
  date_trunc('minute', cr.checked_at) AS checked_at,
  COALESCE(
  AVG(cr.response_time_ms) FILTER (WHERE cr.response_time_ms IS NOT NULL),
  0
) AS avg_response_time_ms,
ARRAY_AGG(cr.status::text ORDER BY cr.checked_at DESC)
)[1] AS status,

(
ARRAY_AGG(cr.status_code ORDER BY cr.checked_at DESC)
)[1] AS status_code,
MIN(cr.ssl_days_left) AS ssl_days_left,
MAX(cr.ssl_warning) AS ssl_warning,
MAX(cr.ssl_error) AS ssl_error,
CASE
  WHEN BOOL_OR(cr.ssl_valid = false) THEN false
  WHEN BOOL_OR(cr.ssl_valid = true) THEN true
  ELSE NULL
END AS ssl_valid

FROM check_results cr
JOIN sites s ON s.id = cr.site_id

WHERE
  cr.site_id = :site_id
  AND s.user_id = :user_id
  AND cr.checked_at >= :cutoff

GROUP BY date_trunc('minute', cr.checked_at)
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
