from uuid import UUID
import csv
import io

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.read_models.export import get_checks_for_export
from app.security.dependencies import get_current_user
from app.models.user import User
from app.repositories.sites import SitesRepository

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/site/{site_id}")
async def export_site_checks(
    site_id: UUID,
    range: str = Query("24h", pattern="^(24h|7d|30d)$"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sites_repo = SitesRepository(session)
    site = await sites_repo.get_by_id_and_user(site_id, current_user.id)

    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    rows = await get_checks_for_export(
        session=session,
        site_id=site_id,
        user_id=current_user.id,
        range=range,
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow([
        "checked_at",
        "status",
        "status_code",
        "avg_response_time_ms",
    ])

    for r in rows:
        status = r["status"]
        status_value = status if status else ""
        timestamp = r["bucket"]
        writer.writerow([
            timestamp.isoformat() if timestamp else "",
            status_value,
            r["status_code"] if r["status_code"] is not None else "",
            float(r["avg_response_time_ms"]) if r["avg_response_time_ms"] is not None else ""
        ])

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=site_{site_id}_{range}.csv"
        },
    )