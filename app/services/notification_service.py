import logging
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.monitoring.process_result import NotifyPayload
from app.repositories.users import UsersRepository

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, bot: Bot):
        self._bot = bot

    @staticmethod
    def _format_status(payload: NotifyPayload) -> str:
        old = payload.old_status.name if payload.old_status else "UNKNOWN"
        new = payload.new_status.name

        emoji = "🟢" if new == "UP" else "🔴"

        lines = [
            f"{emoji} <b>Зміна статусу сайту</b>",
            "",
            f"<b>Сайт:</b> {payload.site_name}",
            f"<b>URL:</b> {payload.url}",
            f"<b>Статус:</b> {old} → {new}",
        ]

        if payload.status_code is not None:
            lines.append(f"<b>HTTP:</b> {payload.status_code}")

        if payload.response_time_ms is not None:
            lines.append(f"<b>Response:</b> {payload.response_time_ms} ms")

        return "\n".join(lines)

    async def notify(
        self,
        *,
        payload: NotifyPayload,
        chat_id: int,
        session: AsyncSession,
    ) -> None:
        message = self._format_status(payload)

        try:
            await self._bot.send_message(chat_id=chat_id, text=message)

        except TelegramForbiddenError:
            logger.warning(
                "User blocked bot. Cleaning telegram_chat_id (chat_id=%s)",
                chat_id,
            )

            users_repo = UsersRepository(session)
            user = await users_repo.get_by_telegram_chat_id(chat_id)

            if user:
                user.telegram_chat_id = None

        except TelegramBadRequest as e:
            logger.warning("TelegramBadRequest: %s", e)

        except Exception as e:
            logger.error("Unexpected Telegram error: %s", e)
