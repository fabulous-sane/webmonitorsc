from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.ssl_state import resolve_ssl_state
from app.monitoring.health_calc import compute_health


async def get_system_status(session: AsyncSession, user_id: UUID) -> dict:
    stmt = text("""
SELECT
    s.id,
    s.is_active,
    s.url,

    cr.status,
    cr.ssl_valid,
    cr.ssl_warning,
    cr.checked_at

FROM sites s

LEFT JOIN LATERAL (
    SELECT status, ssl_valid, ssl_warning, checked_at
    FROM check_results
    WHERE site_id = s.id
    ORDER BY checked_at DESC
    LIMIT 1
) cr ON true

WHERE s.user_id = :user_id
""")

    result = await session.execute(stmt, {"user_id": user_id})
    rows = result.mappings().all()

    stats = {
        "active_sites": 0,
        "archived_sites": 0,

        "ssl_critical_sites": 0,
        "ssl_warning_sites": 0,
        "ssl_invalid_sites": 0,
        "ssl_ok_sites": 0,
        "ssl_no_data_sites": 0,
        "ssl_no_ssl_sites": 0,

        "problematic_sites": 0,
    }

    for r in rows:
        is_active = r["is_active"]
        url = r["url"]

        status = r["status"]
        ssl_valid = r["ssl_valid"]
        ssl_warning = r["ssl_warning"]

        if is_active:
            stats["active_sites"] += 1
        else:
            stats["archived_sites"] += 1

        ssl_state = resolve_ssl_state(
            ssl_valid,
            ssl_warning,
            url,
        )

        status_str = r["status"]

        health = compute_health(status_str, ssl_state)

        if url.startswith("http://"):
            stats["ssl_no_ssl_sites"] += 1
        elif ssl_state == "critical":
            stats["ssl_critical_sites"] += 1
        elif ssl_state == "warning":
            stats["ssl_warning_sites"] += 1
        elif ssl_state == "invalid":
            stats["ssl_invalid_sites"] += 1
        elif ssl_state == "ok":
            stats["ssl_ok_sites"] += 1
        else:
            stats["ssl_no_data_sites"] += 1

        if health in ("critical", "warning"):
            stats["problematic_sites"] += 1

    events_stmt = text("""
    SELECT
    COUNT(*) AS checks_24h,

    COUNT(*) FILTER (WHERE status IN ('DOWN','ERROR')) AS critical_events,
    COUNT(*) FILTER (WHERE status = 'TIMEOUT') AS timeout_events,

    COUNT(*) FILTER (WHERE ssl_warning = 'critical') AS ssl_critical_events,
    COUNT(*) FILTER (WHERE ssl_warning = 'warning') AS ssl_warning_events,

    COUNT(*) FILTER (
        WHERE ssl_valid = false
        AND ssl_error IS DISTINCT FROM 'timeout'
        AND s.url NOT LIKE 'http://%'
    ) AS ssl_invalid_events,

    COUNT(*) FILTER (
        WHERE ssl_valid IS NULL
        AND ssl_warning IS NULL
        AND s.url NOT LIKE 'http://%'
    ) AS ssl_no_data_events

FROM check_results cr
JOIN sites s ON s.id = cr.site_id

WHERE s.user_id = :user_id
AND cr.checked_at >= NOW() - INTERVAL '24 hours'
    """)

    events = await session.execute(events_stmt, {"user_id": user_id})
    e = events.mappings().first() or {}

    stats.update({
        "checks_24h": e.get("checks_24h", 0),

        "ssl_critical_events": e.get("ssl_critical_events", 0),
        "ssl_warning_events": e.get("ssl_warning_events", 0),
        "ssl_invalid_events": e.get("ssl_invalid_events", 0),
        "ssl_no_data_events": e.get("ssl_no_data_events", 0),
    })

    return stats