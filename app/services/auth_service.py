# app/services/auth_service.py

from datetime import timedelta, datetime, timezone
from sqlalchemy.exc import IntegrityError
from app.models.refresh_token import RefreshToken
from app.repositories.users import UsersRepository
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.security.password import hash_password, verify_password, hash_refresh_token
from app.security.jwt import create_access_token, create_refresh_token
from app.services.email_service import EmailService
from app.security.email_confirmation import (
    generate_confirmation_token,
    hash_token,
    generate_password_reset_token,
)


class AuthService:
    def __init__(self, users_repo: UsersRepository):
        self.users_repo = users_repo

    async def register(self, email: str, password: str) -> None:
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")

        token = generate_confirmation_token()

        try:
            user = await self.users_repo.create(
                email=email,
                password_hash=hash_password(password),
            )

            user.email_confirm_token_hash = hash_token(token)
            user.email_confirm_expires_at = (
                    datetime.now(timezone.utc) + timedelta(hours=24)
            )

            await self.users_repo.session.commit()

        except IntegrityError:
            await self.users_repo.session.rollback()
            raise ValueError("User already exists")

        await EmailService.send_confirmation_email(
            email=user.email,
            token=token,
        )

    async def login(self, email: str, password: str) -> dict:
        user = await self.users_repo.get_by_email(email)

        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")

        if not user.is_verified:
            raise ValueError("Email not confirmed")

        access_token, access_jti = create_access_token(str(user.id))
        refresh_token, refresh_jti, expires_at = create_refresh_token(str(user.id))

        refresh_repo = RefreshTokenRepository(self.users_repo.session)

        token_obj = RefreshToken(
            user_id=user.id,
            jti=refresh_jti,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=expires_at,
        )

        await refresh_repo.create(token_obj)
        await self.users_repo.session.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def confirm_email(self, token: str) -> None:
        token_hash = hash_token(token)
        user = await self.users_repo.get_by_email_confirm_token(token_hash)

        if not user:
            raise ValueError("Invalid token")

        if (
            user.email_confirm_expires_at is None
            or user.email_confirm_expires_at < datetime.now(timezone.utc)
        ):
            raise ValueError("Token expired")

        user.is_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        user.email_confirm_token_hash = None
        user.email_confirm_expires_at = None

        await self.users_repo.session.commit()

    async def resend_confirmation(self, email: str) -> str:
        user = await self.users_repo.get_by_email(email)

        if not user:
            return "confirmation_sent"

        if user.is_verified:
            return "already_verified"

        token = generate_confirmation_token()

        user.email_confirm_token_hash = hash_token(token)
        user.email_confirm_expires_at = (
            datetime.now(timezone.utc) + timedelta(hours=24)
        )

        await self.users_repo.session.commit()

        await EmailService.send_confirmation_email(
            email=user.email,
            token=token,
        )

        return "confirmation_resent"

    async def request_password_reset(self, email: str) -> None:
        user = await self.users_repo.get_by_email(email)

        if not user or not user.is_verified:
            return

        token = generate_password_reset_token()

        user.password_reset_token_hash = hash_token(token)
        user.password_reset_expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=30)
        )

        await self.users_repo.session.commit()

        await EmailService.send_password_reset_email(
            email=user.email,
            token=token,
        )

    async def reset_password(self, token: str, new_password: str) -> None:
        token_hash = hash_token(token)
        user = await self.users_repo.get_by_password_reset_token(token_hash)

        if not user:
            raise ValueError("Invalid token")

        if (
            user.password_reset_expires_at is None
            or user.password_reset_expires_at < datetime.now(timezone.utc)
        ):
            raise ValueError("Token expired")

        if len(new_password) < 6:
            raise ValueError("Password is too short")

        user.password_hash = hash_password(new_password)
        user.password_reset_token_hash = None
        user.password_reset_expires_at = None

        await self.users_repo.session.commit()
