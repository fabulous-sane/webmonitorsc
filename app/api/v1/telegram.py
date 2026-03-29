import secrets

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.security.dependencies import get_current_user
from app.repositories.telegram_tokens import TelegramTokenRepository

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/connect")
async def generate_connect_token(
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    repo = TelegramTokenRepository(session)

    await repo.delete_by_user(current_user.id)
    token = secrets.token_urlsafe(16)

    await repo.create(
        user_id=current_user.id,
        token=token,
    )

    await session.commit()

    return {
        "instruction": "Send this command to the bot:",
        "command": f"/connect {token}",
    }

@router.post("/disconnect")
async def disconnect_telegram(
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    user.telegram_chat_id = None
    await session.commit()
    return {"status": "telegram_disconnected"}
