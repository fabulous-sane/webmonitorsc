from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.read_models.system_stats import get_system_status

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status", include_in_schema=True)
async def system_status(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    data = await get_system_status(session)

    scheduler = getattr(request.app.state, "scheduler", None)

    retention_next_run = None

    if scheduler:
        job = scheduler.get_job("retention_cleanup")
        if job and job.next_run_time:
            retention_next_run = job.next_run_time.isoformat()

    data["retention_next_run"] = retention_next_run

    return {
        "active_sites": data.get("active_sites", 0),
        "archived_sites": data.get("archived_sites", 0),

        "ssl_critical_sites": data.get("ssl_critical_sites", 0),
        "ssl_warning_sites": data.get("ssl_warning_sites", 0),
        "ssl_invalid_sites": data.get("ssl_invalid_sites", 0),

        "checks_24h": data.get("checks_24h", 0),
        "ssl_critical_events": data.get("ssl_critical_events", 0),
        "ssl_warning_events": data.get("ssl_warning_events", 0),
        "ssl_invalid_events": data.get("ssl_invalid_events", 0),
        "ssl_unknown_sites": data.get("ssl_unknown_sites", 0),
        "ssl_unknown_events": data.get("ssl_unknown_events", 0),

        "retention_next_run": retention_next_run,
    }