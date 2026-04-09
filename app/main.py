import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.http_client import client
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.services.monitoring_service import MonitoringService
from app.services.notification_service import NotificationService
from app.monitoring.retention import cleanup_old_checks

from app.bot.telegram_bot import dp, bot
from app.api.v1.sites import router as sites_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.export import router as export_router
from app.api.v1.telegram import router as telegram_router
from app.api.v1.health import router as health_router
from app.api.v1.system import router as system_router
from fastapi.responses import JSONResponse
from app.services.exceptions import (
    SiteLimitExceeded,
    SiteAlreadyExists,
    SiteNotFound,
    UserAlreadyExists,
    InvalidCredentials,
    EmailNotConfirmed,
    InvalidToken,
    TokenExpired, InvalidRefreshToken, UserInactive, InvalidLogoutToken,
)

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.start()

    app.state.scheduler = scheduler

    notification_service = NotificationService(bot)

    monitoring_service = MonitoringService(
        scheduler=scheduler,
        notification_service=notification_service,
    )

    app.state.monitoring_service = monitoring_service

    polling_task = asyncio.create_task(
        dp.start_polling(bot, skip_updates=True)
    )

    logger.info("Telegram bot polling started")

    async def retention_job():
        async with AsyncSessionLocal() as session:
            deleted = await cleanup_old_checks(
                session=session,
                keep_days=settings.RETENTION_DAYS,
            )
            await session.commit()
            logger.info("Retention cleanup removed %s rows", deleted)

    scheduler.add_job(
        retention_job,
        trigger="cron",
        hour=1,
        id="retention_cleanup",
        replace_existing=True,
    )

    async with AsyncSessionLocal() as session:
        await monitoring_service.bootstrap_active_sites(session=session)

    yield

    logger.info("Shutting down polling...")
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass

    logger.info("Shutting down scheduler...")
    scheduler.shutdown(wait=False)

    await bot.session.close()
    await client.aclose()

    logger.info("Application shutdown complete")

app = FastAPI(
    title="WebCheck",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://webmonitorsc.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sites_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(telegram_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")

@app.get("/ready", include_in_schema=False)
async def ready(request: Request):
    scheduler = getattr(request.app.state, "scheduler", None)

    if scheduler is None:
        return {"error": "Scheduler not initialized"}

    return {"scheduler_running": scheduler.running}

@app.get("/_debug/scheduler", include_in_schema=False)
async def debug_scheduler(request: Request):
    scheduler = getattr(request.app.state, "scheduler", None)

    if scheduler is None:
        return {"error": "Scheduler not initialized"}

    return {
        "running": scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "trigger": str(job.trigger),
                "next_run_time": str(job.next_run_time),
            }
            for job in scheduler.get_jobs()
        ],
    }

@app.exception_handler(SiteLimitExceeded)
async def handle_site_limit(_, __):
    return JSONResponse(
        status_code=403,
        content={"detail": "Site limit reached"},
    )

@app.exception_handler(SiteAlreadyExists)
async def handle_site_exists(_, __):
    return JSONResponse(
        status_code=409,
        content={"detail": "Site already exists"},
    )

@app.exception_handler(SiteNotFound)
async def handle_site_not_found(_, __):
    return JSONResponse(
        status_code=404,
        content={"detail": "Site not found"},
    )

@app.exception_handler(UserAlreadyExists)
async def handle_user_exists(_, __):
    return JSONResponse(
        status_code=409,
        content={"detail": "User already exists"},
    )

@app.exception_handler(InvalidCredentials)
async def handle_invalid_credentials(_, __):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid credentials"},
    )

@app.exception_handler(EmailNotConfirmed)
async def handle_email_not_confirmed(_, __):
    return JSONResponse(
        status_code=403,
        content={"detail": "Email not confirmed"},
    )

@app.exception_handler(InvalidToken)
async def handle_invalid_token(_, __):
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid token"},
    )

@app.exception_handler(TokenExpired)
async def handle_token_expired(_, __):
    return JSONResponse(
        status_code=400,
        content={"detail": "Token expired"},
    )

@app.exception_handler(InvalidRefreshToken)
async def handle_invalid_refresh(_, __):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid refresh token"},
    )

@app.exception_handler(UserInactive)
async def handle_user_inactive(_, __):
    return JSONResponse(
        status_code=401,
        content={"detail": "User inactive"},
    )

@app.exception_handler(InvalidLogoutToken)
async def handle_invalid_logout(_, __):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid logout token"},
    )