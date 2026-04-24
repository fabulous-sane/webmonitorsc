from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.core.config import settings
from app.core.database import get_db
from app.read_models.system_stats import get_system_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/status")
async def system_status(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    data = await get_system_status(session)
    now = datetime.now(timezone.utc)

    cutoff = now - timedelta(days=settings.RETENTION_DAYS)
    delay_threshold = timedelta(hours=settings.RETENTION_DELAY_THRESHOLD_HOURS)

    scheduler = getattr(request.app.state, "scheduler", None)

    if scheduler is None:
        logger.error("Scheduler missing")
        return {
            "active_sites": 0,
            "archived_sites": 0,
            "checks_24h": 0,

            "ssl_critical_sites": 0,
            "ssl_warning_sites": 0,
            "ssl_invalid_sites": 0,
            "ssl_ok_sites": 0,
            "ssl_no_data_sites": 0,

            "problematic_sites": 0,

            "ssl_critical_events": 0,
            "ssl_warning_events": 0,
            "ssl_invalid_events": 0,
            "ssl_no_data_events": 0,

            "retention_last_run": None,
            "retention_next_run": None,
            "data_retention_days": settings.RETENTION_DAYS,
            "cleanup_interval": "daily",

            "retention_never_run": True,
            "retention_broken": True,
            "retention_delayed": False,
            "data_cutoff_date": cutoff,
            "retention_deleted_last": None,
        }

    job = scheduler.get_job("retention_cleanup")
    if not job:
        logger.error("Retention job missing")
    next_run = None
    if job and job.next_run_time:
        next_run = job.next_run_time
        if next_run.tzinfo is None:
            next_run = next_run.replace(tzinfo=timezone.utc)
        else:
            next_run = next_run.astimezone(timezone.utc)

    try:
        row = await session.execute(
            text("SELECT last_run_at, last_deleted_count FROM retention_meta WHERE id = 1")
        )
        meta = row.first()
    except Exception:
        logger.exception("Retention meta read failed")
        meta = None

    last_run = meta[0] if meta else None
    deleted = meta[1] if meta else None

    retention_never_run = last_run is None and deleted is None
    retention_broken = scheduler is None or next_run is None
    retention_delayed = (
            next_run is not None and now > next_run + delay_threshold
    )

    return {
        "active_sites": data.get("active_sites", 0),
        "archived_sites": data.get("archived_sites", 0),

        "ssl_critical_sites": data.get("ssl_critical_sites", 0),
        "ssl_warning_sites": data.get("ssl_warning_sites", 0),
        "ssl_invalid_sites": data.get("ssl_invalid_sites", 0),
        "ssl_ok_sites": data.get("ssl_ok_sites", 0),

        "problematic_sites": data.get("problematic_sites", 0),

        "checks_24h": data.get("checks_24h", 0),

        "ssl_critical_events": data.get("ssl_critical_events", 0),
        "ssl_warning_events": data.get("ssl_warning_events", 0),
        "ssl_invalid_events": data.get("ssl_invalid_events", 0),
        "ssl_no_data_sites": data.get("ssl_no_data_sites", 0),
        "ssl_no_data_events": data.get("ssl_no_data_events", 0),

        "retention_last_run": last_run,
        "retention_next_run": next_run,
        "data_retention_days": settings.RETENTION_DAYS,
        "cleanup_interval": "daily",
        "retention_never_run": retention_never_run,
        "retention_broken": retention_broken,
        "retention_delayed": retention_delayed,
        "data_cutoff_date": cutoff,
        "retention_deleted_last": deleted,
    }