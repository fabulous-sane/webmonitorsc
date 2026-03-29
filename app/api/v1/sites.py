from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.schemas.site import SiteCreate, SiteOut, SiteIntervalUpdate
from app.services.exceptions import (
    SiteLimitExceeded,
    SiteAlreadyExists,
    SiteNotFound,
)
from app.services.monitoring_service import MonitoringService
from app.services.site_service import SiteService
from app.security.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/sites", tags=["sites"])

def get_monitoring_service(request: Request) -> MonitoringService:
    return request.app.state.monitoring_service

@router.post("", response_model=SiteOut, status_code=status.HTTP_201_CREATED)
async def create_site(
    data: SiteCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    service = SiteService(
        session=session,
        monitoring_service=monitoring_service,
    )

    try:
        return await service.create_site(
            user_id=current_user.id,
            name=data.name,
            url=str(data.url),
            check_interval=data.check_interval,
        )
    except SiteLimitExceeded:
        raise HTTPException(status_code=403, detail="Site limit reached")
    except SiteAlreadyExists:
        raise HTTPException(status_code=409, detail="Site already exists")

    except Exception:
        raise

@router.get("", response_model=list[SiteOut])
async def list_sites(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SiteService(session=session)
    return await service.list_active_sites(current_user.id)

@router.patch("/{site_id}/interval", status_code=status.HTTP_204_NO_CONTENT)
async def update_site_interval(
    site_id: UUID,
    data: SiteIntervalUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    service = SiteService(
        session=session,
        monitoring_service=monitoring_service,
    )

    try:
        await service.update_interval(
            site_id=site_id,
            user_id=current_user.id,
            check_interval=data.check_interval,
        )
    except SiteNotFound:
        raise HTTPException(status_code=404, detail="Site not found")

    except Exception:
        raise

@router.post("/{site_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_site(
    site_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    service = SiteService(
        session=session,
        monitoring_service=monitoring_service,
    )

    try:
        await service.deactivate(
            site_id=site_id,
            user_id=current_user.id,
        )
    except SiteNotFound:
        raise HTTPException(status_code=404, detail="Site not found")

    except Exception:
        raise

@router.post("/{site_id}/reactivate", status_code=status.HTTP_204_NO_CONTENT)
async def reactivate_site(
    site_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    service = SiteService(
        session=session,
        monitoring_service=monitoring_service,
    )

    try:
        await service.reactivate(
            site_id=site_id,
            user_id=current_user.id,
        )
    except SiteNotFound:
        raise HTTPException(status_code=404, detail="Site not found")

@router.get("/{site_id}/uptime")
async def get_uptime(
            site_id: UUID,
            hours: int = 24,
            session: AsyncSession = Depends(get_db),
            current_user: User = Depends(get_current_user),
    ):
        service = SiteService(session=session)

        try:
            uptime = await service.get_site_uptime(
                site_id=site_id,
                user_id=current_user.id,
                hours=hours,
            )
            return {"uptime_percent": uptime}
        except SiteNotFound:
            raise HTTPException(status_code=404, detail="Site not found")




