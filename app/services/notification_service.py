import logging
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.monitoring.status import SiteStatus
from app.utils.ssl_state import resolve_ssl_state
from app.utils.health import normalize_health
from app.monitoring.process_result import NotifyPayload
from app.repositories.users import UsersRepository

logger = logging.getLogger(__name__)

HEALTH_META = {
    "critical": ("🔴", "КРИТИЧНО"),
    "warning": ("🟡", "ПОПЕРЕДЖЕННЯ"),
    "ok": ("🟢", "НОРМАЛЬНО"),
    "no_data": ("⚪", "НЕМАЄ ДАНИХ"),
}

STATUS_LABELS = {
    SiteStatus.UP: "Працює",
    SiteStatus.DOWN: "Недоступний",
    SiteStatus.ERROR: "Помилка",
    SiteStatus.TIMEOUT: "Таймаут",
}

SSL_LABELS = {
    "ok": "OK",
    "warning": "Попередження",
    "critical": "Критично",
    "invalid": "Недійсний",
    "http": "Без SSL",
    "no_data": "Немає даних",
}


class NotificationService:
    def __init__(self, bot: Bot):
        self._bot = bot

    @staticmethod
    def _format_status(payload: NotifyPayload) -> str:
        health = normalize_health(payload.health) or "no_data"
        emoji, label = HEALTH_META.get(health, ("⚪", "НЕВІДОМО"))

        is_http_change = payload.http_changed
        is_ssl_change = payload.is_ssl_change

        lines = [
            f"{emoji} <b>{label}</b>",
            "",
            f"<b>Сайт:</b> {payload.site_name}",
            f"<b>URL:</b> {payload.url}",
        ]

        if is_http_change:
            lines += ["", "<b>HTTP:</b>"]

            old = STATUS_LABELS.get(payload.old_status, "—")
            new = STATUS_LABELS.get(payload.new_status, "—")

            lines.append(f"{old} → {new}")

            if payload.new_status == SiteStatus.TIMEOUT:
                lines.append("⏱ Сервер не відповідає")

            elif payload.new_status == SiteStatus.ERROR:
                if payload.error_type == "connection_error":
                    lines.append("🌐 Помилка з’єднання")
                elif payload.error_type == "request_error":
                    lines.append("⚠ Помилка запиту")
                else:
                    lines.append("⚠ Невідома помилка")

            elif payload.new_status == SiteStatus.DOWN:
                lines.append(f"🔴 HTTP {payload.status_code or 'без відповіді'}")

            elif (
                    payload.old_status in (SiteStatus.DOWN, SiteStatus.ERROR, SiteStatus.TIMEOUT)
                    and payload.new_status == SiteStatus.UP
            ):
                lines.append("🟢 Відновлено")

            if payload.status_code:
                lines.append(f"Код: {payload.status_code}")

            if payload.response_time_ms is not None and payload.new_status == SiteStatus.UP:
                lines.append(f"⏱ {payload.response_time_ms} ms")

        if payload.url.startswith("https://") and is_ssl_change:
            ssl_state = resolve_ssl_state(
                payload.ssl_valid,
                payload.ssl_warning,
                payload.url,
                payload.ssl_error,
            )

            days = payload.ssl_days_left if isinstance(payload.ssl_days_left, int) else "?"

            lines += ["", "<b>SSL:</b>"]

            prev = SSL_LABELS.get(payload.prev_ssl_state, "—")
            curr = SSL_LABELS.get(ssl_state, ssl_state)

            lines.append(f"{prev} → {curr}")

            if ssl_state == "critical":
                lines.append(f"🔴 критично ({days} днів)")
            elif ssl_state == "warning":
                lines.append(f"🟡 скоро закінчиться ({days} днів)")
            elif ssl_state == "invalid":
                lines.append("❌ недійсний")
            elif ssl_state == "ok":
                lines.append(f"🟢 OK ({days} днів)")
            else:
                lines.append("⚪ немає даних")

        return "\n".join(lines)

    async def notify(
        self,
        *,
        payload: NotifyPayload,
        chat_id: int,
        session: AsyncSession,
    ) -> None:

        message = self._format_status(payload)

        if not message.strip():
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
            logger.warning("Telegram error: %s", e)

        except Exception:
            logger.exception("Unexpected Telegram error")