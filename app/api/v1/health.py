from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db

router = APIRouter(prefix="/health", tags=["health"])

@router.get("", include_in_schema=False)
async def health():
    return {"status": "ok"}

@router.get("/db", include_in_schema=False)
async def health_db(session: AsyncSession = Depends(get_db)):
    await session.execute(text("SELECT 1"))
    return {"db": "ok"}
