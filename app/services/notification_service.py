import logging
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.ssl_state import resolve_ssl_state
from app.utils.health import normalize_health
from app.monitoring.process_result import NotifyPayload
from app.repositories.users import UsersRepository

logger = logging.getLogger(__name__)

HEALTH_META = {
    "critical": ("🔴", "Критично"),
    "warning": ("🟡", "Попередження"),
    "ok": ("🟢", "Нормально"),
    "no_data": ("⚪", "Немає даних"),
}

class NotificationService:
    def __init__(self, bot: Bot):
        self._bot = bot

    @staticmethod
    def _format_status(payload: NotifyPayload) -> str:
        health = normalize_health(payload.health) or "no_data"
        emoji, label = HEALTH_META.get(health, ("⚪", "Невідомо"))

        is_http_change = payload.old_status is not None and payload.ssl_warning is None

        if is_http_change:
            lines = [
                f"{emoji} <b>Зміна стану сайту</b>",
                "",
                f"<b>Сайт:</b> {payload.site_name}",
                f"<b>URL:</b> {payload.url}",
                f"<b>Стан:</b> {label}",
            ]
        else:
            lines = [
                "🔐 <b>Зміна стану SSL</b>",
                "",
                f"<b>Сайт:</b> {payload.site_name}",
                f"<b>URL:</b> {payload.url}",
            ]

        if payload.status_code is not None:
            lines.append(f"<b>HTTP:</b> {payload.status_code}")

        if payload.response_time_ms is not None:
            lines.append(f"<b>Response:</b> {payload.response_time_ms} ms")

        ssl_state = resolve_ssl_state(
            payload.ssl_valid,
            payload.ssl_warning,
            payload.url,
        )

        days = payload.ssl_days_left if isinstance(payload.ssl_days_left, int) else "?"

        if ssl_state == "http":
            lines.append("🌐 SSL: відсутній")
        elif ssl_state == "critical":
            lines.append(f"🔴 SSL: критично ({days} днів)")
        elif ssl_state == "warning":
            lines.append(f"🟡 SSL: скоро закінчиться ({days} днів)")
        elif ssl_state == "invalid":
            lines.append("❌ SSL: недійсний")
        elif ssl_state == "ok":
            lines.append(f"🟢 SSL: OK ({days} днів)")
        else:
            lines.append("⚪ SSL: немає даних")

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
            await self._bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML"
            )

        except TelegramForbiddenError:
            users_repo = UsersRepository(session)
            user = await users_repo.get_by_telegram_chat_id(chat_id)

            if user:
                user.telegram_chat_id = None
                await session.commit()

        except TelegramBadRequest as e:
            logger.warning("TelegramBadRequest (chat_id=%s): %s", chat_id, e)

        except Exception:
            logger.exception("Unexpected Telegram error")
