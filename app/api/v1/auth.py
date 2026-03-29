from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.core.database import get_db
from app.core.config import settings
from app.models.refresh_token import RefreshToken
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.users import UsersRepository
from app.security.jwt import create_access_token, create_refresh_token
from app.security.password import hash_refresh_token
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

    try:
        await service.register(data.email, data.password)
        return {"status": "confirmation_sent"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(UsersRepository(session))

    try:
        tokens = await service.login(data.email, data.password)
        return tokens
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/logout")
async def logout(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_db),
):
    try:
        payload = jwt.decode(
            data.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    repo = RefreshTokenRepository(session)
    token_obj = await repo.get_by_jti(payload.get("jti"))

    if (
            token_obj
            and not token_obj.is_revoked
            and token_obj.token_hash == hash_refresh_token(data.refresh_token)
            and token_obj.expires_at > datetime.now(timezone.utc)
    ):
        await repo.revoke(token_obj)
        await session.commit()

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

    try:
        await service.confirm_email(data.token)
        return {"status": "email_confirmed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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

    try:
        await service.reset_password(
            token=data.token,
            new_password=data.new_password,
        )
        return {"status": "password_updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/refresh")
async def refresh(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_db),
):
    try:
        payload = jwt.decode(
            data.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    jti = payload.get("jti")
    user_id = payload.get("sub")

    if not jti or not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    repo = RefreshTokenRepository(session)
    token_obj = await repo.get_by_jti(jti)

    user_repo = UsersRepository(session)
    user = await user_repo.get_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive")

    if not token_obj or str(token_obj.user_id) != str(user_id):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if (
        token_obj.is_revoked
        or token_obj.expires_at < datetime.now(timezone.utc)
        or token_obj.token_hash != hash_refresh_token(data.refresh_token)
    ):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    await repo.revoke(token_obj)

    access_token, _ = create_access_token(user_id)
    new_refresh_token, new_jti, expires_at = create_refresh_token(user_id)

    new_token_obj = RefreshToken(
        user_id=token_obj.user_id,
        jti=new_jti,
        token_hash=hash_refresh_token(new_refresh_token),
        expires_at=expires_at,
    )

    await repo.create(new_token_obj)
    await session.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


