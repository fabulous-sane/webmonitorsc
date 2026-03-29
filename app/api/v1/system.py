from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.read_models.system_stats import get_system_status

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status", include_in_schema=False)
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

    return data