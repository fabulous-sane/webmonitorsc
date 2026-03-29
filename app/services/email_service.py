import asyncio
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.core.config import settings

class EmailService:

    @staticmethod
    async def _send(message: Mail) -> None:
        def blocking():
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            sg.send(message)

        await asyncio.to_thread(blocking)

    @staticmethod
    async def send_confirmation_email(*, email: str, token: str) -> None:
        confirm_link = (
            f"{settings.FRONTEND_URL}/confirm-email?token={token}"
        )

        message = Mail(
            from_email=settings.EMAIL_FROM,
            to_emails=email,
            subject="Confirm your email",
            html_content=f"""
                <p>Привіт,</p>
                <p>Підтверди свою пошту для реєстрації у сервісі WebMonitor:</p>
                <p>
                  <a href="{confirm_link}">
                    Підтвердити email
                  </a>
                </p>
                <p>Посилання дійсне 24 години.</p>
                <p>(Якщо не реєструвався - просто проігноруй цей лист)</p>
            """,
        )

        try:
            await EmailService._send(message)
        except Exception as e:
            raise RuntimeError("Failed to send confirmation email") from e

    @staticmethod
    async def send_password_reset_email(*, email: str, token: str) -> None:
        reset_link = (
            f"{settings.FRONTEND_URL}/reset-password?token={token}"
        )

        message = Mail(
            from_email=settings.EMAIL_FROM,
            to_emails=email,
            subject="Reset your password",
            html_content=f"""
                <p>Хтось запросив скидання паролю.</p>
                <p>Якщо це ти - натисни:</p>
                <p><a href="{reset_link}">Reset password</a></p>
                <p>Посилання дійсне 30 хвилин.</p>
                <p>(Якщо це не ти - просто проігноруй лист.)</p>
            """,
        )

        try:
            await EmailService._send(message)
        except Exception as e:
            raise RuntimeError("Failed to send password reset email") from e