from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_system_status(session: AsyncSession) -> dict:
    stmt = text("""
        SELECT
            COUNT(*) FILTER (WHERE s.is_active = true) AS active_sites,
            COUNT(*) FILTER (WHERE s.is_active = false) AS archived_sites,

             COUNT(DISTINCT s.id) FILTER (
              WHERE cr.ssl_warning = 'critical'
            ) AS ssl_critical_sites,

            COUNT(DISTINCT s.id) FILTER (
              WHERE cr.ssl_warning = 'warning'
            ) AS ssl_warning_sites,

            COUNT(DISTINCT s.id) FILTER (
              WHERE cr.ssl_valid = false
              AND cr.ssl_warning IS NULL
            ) AS ssl_invalid_sites,

            COUNT(DISTINCT s.id) FILTER (
              WHERE cr.ssl_valid IS NULL
              AND cr.ssl_warning IS NULL
            ) AS ssl_no_data_sites,

            COUNT(DISTINCT s.id) FILTER (
              WHERE cr.ssl_valid = true
              AND cr.ssl_warning IS NULL
            ) AS ssl_ok_sites,

            COUNT(DISTINCT s.id) FILTER (
              WHERE cr.ssl_warning IN ('critical','warning')
              OR cr.ssl_valid = false
            ) AS problematic_sites,
        
            (
                SELECT COUNT(*)
                FROM check_results
                WHERE checked_at >= date_trunc('day', now())
            ) AS checks_24h,
            
            (
            SELECT COUNT(*)
            FROM check_results
                WHERE ssl_valid IS NULL
            AND checked_at >= date_trunc('day', now())
            ) AS ssl_no_data_events,

            (
                SELECT COUNT(*)
                FROM check_results
                WHERE ssl_warning = 'critical'
                AND checked_at >= date_trunc('day', now())
            ) AS ssl_critical_events,

            (
                SELECT COUNT(*)
                FROM check_results
                WHERE ssl_warning = 'warning'
                AND checked_at >= date_trunc('day', now())
            ) AS ssl_warning_events,
            
            (
    SELECT COUNT(*)
    FROM check_results
    WHERE ssl_valid = false
    AND checked_at >= date_trunc('day', now())
) AS ssl_invalid_events

        FROM sites s
        
        LEFT JOIN LATERAL (
            SELECT ssl_warning, ssl_valid
            FROM check_results
            WHERE site_id = s.id
            ORDER BY checked_at DESC
            LIMIT 1
        ) cr ON true
        
        WHERE s.is_active = true
    """)

    result = await session.execute(stmt)
    row = result.mappings().first()

    return dict(row) if row else {}