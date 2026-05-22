from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.auth import create_token, hash_password, verify_password
from app.database.models import User
from app.database.schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.database.session import get_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(User).where(or_(User.account == body.account, User.phone == body.phone, User.nickname == body.nickname))
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account, phone or nickname already exists")

    user = User(
        nickname=body.nickname,
        phone=body.phone,
        account=body.account,
        password=hash_password(body.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_token(user)
    return AuthResponse(user=UserResponse.model_validate(user), token=token)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(User).where(or_(User.account == body.account, User.phone == body.account))
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid account or password")

    token = create_token(user)
    return AuthResponse(user=UserResponse.model_validate(user), token=token)