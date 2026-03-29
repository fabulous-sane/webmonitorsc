from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.repositories.users import UsersRepository

from app.services.auth_service import AuthService
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ConfirmEmailRequest(BaseModel):
    token: str


class ResendConfirmationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6)

@router.post("/register")
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(UsersRepository(session))

    await service.register(data.email, data.password)
    return {"status": "confirmation_sent"}

@router.post("/login")
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(UsersRepository(session))

    tokens = await service.login(data.email, data.password)
    return tokens

@router.post("/logout")
async def logout(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(UsersRepository(session))
    await service.logout(data.refresh_token)
    return {"status": "logged_out"}

@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "is_verified": user.is_verified,
        "telegram_connected": user.telegram_chat_id is not None,
    }

@router.post("/confirm-email")
async def confirm_email(
    data: ConfirmEmailRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(UsersRepository(session))

    await service.confirm_email(data.token)
    return {"status": "email_confirmed"}


@router.post("/resend-confirmation")
async def resend_confirmation(
    data: ResendConfirmationRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(UsersRepository(session))
    status = await service.resend_confirmation(data.email)
    return {"status": status}

@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(UsersRepository(session))
    await service.request_password_reset(data.email)
    return {"status": "reset_email_sent"}

@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(UsersRepository(session))


    await service.reset_password(
        token=data.token,
        new_password=data.new_password,
    )
    return {"status": "password_updated"}

@router.post("/refresh")
async def refresh(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(UsersRepository(session))
    return await service.refresh(data.refresh_token)


