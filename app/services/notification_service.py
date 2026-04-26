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
    def get_status_label(status: str) -> str:
        return {
            "UP": "Працює",
            "DOWN": "Недоступний",
            "TIMEOUT": "Таймаут",
            "ERROR": "Помилка",
        }.get(status, status)

    @staticmethod
    def _format_status(payload: NotifyPayload) -> str:
        status_raw = payload.new_status.name

        emoji = {
            "UP": "🟢",
            "DOWN": "🔴",
            "TIMEOUT": "🟡",
            "ERROR": "⚠️",
        }.get(status_raw, "⚪")

        if payload.old_status is not None:
            old_raw = payload.old_status.name
            new_raw = payload.new_status.name

            old = NotificationService.get_status_label(old_raw)
            new = NotificationService.get_status_label(new_raw)

            lines = [
                f"{emoji} <b>Зміна статусу сайту</b>",
                "",
                f"<b>Сайт:</b> {payload.site_name}",
                f"<b>URL:</b> {payload.url}",
                f"<b>Статус:</b> {old} → {new}",
            ]
        else:
            lines = [
                "🔐 <b>Зміна стану SSL</b>",
                f"<b>Сайт:</b> {payload.site_name}",
                f"<b>URL:</b> {payload.url}",
            ]

        if payload.status_code is not None:
            lines.append(f"<b>HTTP:</b> {payload.status_code}")

        if payload.response_time_ms is not None:
            lines.append(f"<b>Response:</b> {payload.response_time_ms} ms")

        if payload.url.startswith("http://"):
            lines.append("🌐 <b>SSL:</b> відсутній (HTTP)")
            return "\n".join(lines)

        if payload.ssl_warning:
            if payload.ssl_warning == "critical":
                lines.append(f"🔴 <b>SSL:</b> закінчується ({payload.ssl_days_left} днів)")
            elif payload.ssl_warning == "warning":
                lines.append(f"🟡 <b>SSL:</b> скоро закінчиться ({payload.ssl_days_left} днів)")
        elif payload.ssl_days_left is not None:
            lines.append(f"🟢 <b>SSL:</b> дійсний ({payload.ssl_days_left} днів)")
        else:
            lines.append("⚪ <b>SSL:</b> немає даних")

        return "\n".join(lines)

    async def notify(
        self,
        *,
        payload: NotifyPayload,
        chat_id: int,
        session: AsyncSession,
    ) -> None:
        message = self._format_status(payload)

        if self._bot is None:
            logger.warning("Bot not initialized (chat_id=%s)", chat_id)
            return

        try:
            await self._bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")

        except TelegramForbiddenError:
            logger.warning(
                "User blocked bot. Cleaning telegram_chat_id (chat_id=%s)",
                chat_id,
            )

            users_repo = UsersRepository(session)
            user = await users_repo.get_by_telegram_chat_id(chat_id)

            if user:
                user.telegram_chat_id = None
                await session.commit()

        except TelegramBadRequest as e:
            logger.warning("TelegramBadRequest (chat_id=%s): %s", chat_id, e)

        except Exception:
            logger.exception("Unexpected Telegram error")
