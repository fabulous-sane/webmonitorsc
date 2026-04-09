import asyncio
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self) -> None:
        self._client = SendGridAPIClient(settings.SENDGRID_API_KEY)

    async def _send(self, message: Mail) -> None:
        if settings.ENVIRONMENT == "development":
            logger.info("Email skipped in development: %s", message.subject)
            return

        def blocking():
            self._client.send(message)

        try:
            await asyncio.wait_for(
                asyncio.to_thread(blocking),
                timeout=10,
            )
        except Exception as e:
            logger.exception("Email sending failed")
            raise RuntimeError("Failed to send email") from e

    async def send_confirmation_email(self, *, email: str, token: str) -> None:
        confirm_link = (
            f"{settings.FRONTEND_URL}/confirm-email?token={token}"
        )

        message = Mail(
            from_email=settings.EMAIL_FROM,
            to_emails=email,
            subject="Підтвердження пошти",
            html_content=f"""
                <p>Привіт,</p>
                <p>Підтверди свою пошту для реєстрації у сервісі WebMonitor:</p>
                <p>
                  <a href="{confirm_link}">
                    Підтвердити email
                  </a>
                </p>
                <p>Посилання дійсне 24 години.</p>
                <p>(Якщо не реєструвався, просто проігноруй цей лист.)</p>
            """,
        )

        await self._send(message)

    async def send_password_reset_email(self, *, email: str, token: str) -> None:
        reset_link = (
            f"{settings.FRONTEND_URL}/reset-password?token={token}"
        )

        message = Mail(
            from_email=settings.EMAIL_FROM,
            to_emails=email,
            subject="Скидання паролю",
            html_content=f"""
                <p>Хтось запросив скидання паролю.</p>
                <p>Якщо це ти - натисни:</p>
                <p><a href="{reset_link}">Reset password</a></p>
                <p>Посилання дійсне 30 хвилин.</p>
                <p>(Якщо це не ти, то просто проігноруй лист.)</p>
            """,
        )

        await self._send(message)