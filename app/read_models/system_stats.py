from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_system_status(session: AsyncSession, user_id: UUID) -> dict:
    stmt = text("""
SELECT
    COUNT(*) FILTER (WHERE s.is_active = true)  AS active_sites,
    COUNT(*) FILTER (WHERE s.is_active = false) AS archived_sites,

    COUNT(DISTINCT s.id) FILTER (
        WHERE cr.ssl_warning = 'critical'
          AND s.url NOT LIKE 'http://%'
    ) AS ssl_critical_sites,

    COUNT(DISTINCT s.id) FILTER (
        WHERE cr.ssl_warning = 'warning'
          AND s.url NOT LIKE 'http://%'
    ) AS ssl_warning_sites,

    COUNT(DISTINCT s.id) FILTER (
        WHERE s.url LIKE 'http://%'
    ) AS ssl_no_ssl_sites,

    COUNT(DISTINCT s.id) FILTER (
        WHERE cr.ssl_valid = false
          AND cr.ssl_warning IS NULL
          AND s.url NOT LIKE 'http://%'
    ) AS ssl_invalid_sites,

    COUNT(DISTINCT s.id) FILTER (
        WHERE cr.ssl_valid IS NULL
          AND cr.ssl_warning IS NULL
          AND s.url NOT LIKE 'http://%'
    ) AS ssl_no_data_sites,

    COUNT(DISTINCT s.id) FILTER (
        WHERE cr.ssl_valid = true
          AND cr.ssl_warning IS NULL
          AND s.url NOT LIKE 'http://%'
    ) AS ssl_ok_sites,

    COUNT(DISTINCT s.id) FILTER (
        WHERE (
            cr.ssl_warning IN ('critical', 'warning')
            OR cr.ssl_valid = false
        )
        AND s.url NOT LIKE 'http://%'
    ) AS problematic_sites,

    (
        SELECT COUNT(*)
        FROM check_results cr
        JOIN sites s2 ON s2.id = cr.site_id
        WHERE s2.user_id = :user_id
          AND cr.checked_at >= NOW() - INTERVAL '24 hours'
    ) AS checks_24h,

    (
        SELECT COUNT(*)
        FROM check_results cr
        JOIN sites s2 ON s2.id = cr.site_id
        WHERE s2.user_id = :user_id
          AND cr.ssl_warning = 'critical'
          AND cr.checked_at >= NOW() - INTERVAL '24 hours'
    ) AS ssl_critical_events,

    (
        SELECT COUNT(*)
        FROM check_results cr
        JOIN sites s2 ON s2.id = cr.site_id
        WHERE s2.user_id = :user_id
          AND cr.ssl_warning = 'warning'
          AND cr.checked_at >= NOW() - INTERVAL '24 hours'
    ) AS ssl_warning_events,

    (
        SELECT COUNT(*)
        FROM check_results cr
        JOIN sites s2 ON s2.id = cr.site_id
        WHERE s2.user_id = :user_id
          AND cr.ssl_valid = false
          AND cr.checked_at >= NOW() - INTERVAL '24 hours'
    ) AS ssl_invalid_events,

    (
        SELECT COUNT(*)
        FROM check_results cr
        JOIN sites s2 ON s2.id = cr.site_id
        WHERE s2.user_id = :user_id
          AND cr.ssl_valid IS NULL
          AND cr.ssl_warning IS NULL
          AND s2.url NOT LIKE 'http://%'
          AND cr.checked_at >= NOW() - INTERVAL '24 hours'
    ) AS ssl_no_data_events

FROM sites s

LEFT JOIN LATERAL (
    SELECT ssl_warning, ssl_valid
    FROM check_results
    WHERE site_id = s.id
    AND checked_at >= NOW() - INTERVAL '1 hour'
    ORDER BY checked_at DESC
    LIMIT 1
) cr ON true

WHERE s.user_id = :user_id;
    """)

    result = await session.execute(stmt, {"user_id": user_id})
    row = result.mappings().first()

    return dict(row) if row else {}