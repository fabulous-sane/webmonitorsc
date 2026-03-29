# app/api/v1/dashboard.py
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.security.dependencies import get_current_user

from app.core.database import get_db
from app.read_models.dashboard_stats import (
    get_overview,
    get_site_checks,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/overview")
async def dashboard_overview(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_overview(
        session=session,
        user_id=current_user.id,
    )


@router.get("/site/{site_id}")
async def dashboard_site(
    site_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    range: str = Query("24h", pattern="^(24h|7d|30d)$"),
):
        checks = await get_site_checks(
            session=session,
            site_id=site_id,
            user_id=current_user.id,
            range=range,
        )
        return checks
