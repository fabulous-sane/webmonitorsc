from uuid import UUID
import csv
import io

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.read_models.export import get_checks_for_export
from app.security.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/site/{site_id}")
async def export_site_checks(
    site_id: UUID,
    range: str = Query("24h", pattern="^(24h|7d|30d)$"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверяем что сайт вообще существует
    site_check = await session.execute(
        text("SELECT id FROM sites WHERE id = :id AND user_id = :uid"),
        {"id": site_id, "uid": current_user.id},
    )

    if not site_check.first():
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
        "response_time_ms",
    ])

    for r in rows:
        writer.writerow([
            r["checked_at"].isoformat() if r["checked_at"] else "",
            r["status"],
            r["status_code"],
            r["response_time_ms"],
        ])

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=site_{site_id}_{range}.csv"
        },
    )