from __future__ import annotations
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.auth import create_token, hash_password, verify_password
from app.database.models import User, Room as RoomModel
from app.database.schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.database.session import get_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/rooms/history")
async def room_history(user_id: int = Query(...), session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(RoomModel)
        .where(RoomModel.creator_id == user_id, RoomModel.status == "finished")
        .order_by(desc(RoomModel.created_at))
        .limit(20)
    )
    rooms = result.scalars().all()
    return [
        {"id": r.id, "room_code": r.room_code, "status": r.status, "result": r.result,
         "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in rooms
    ]


@router.get("/rooms/history/{room_id}")
async def room_history_detail(room_id: int, session: AsyncSession = Depends(get_session)):
    r = await session.get(RoomModel, room_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Room not found")
    game_log = json.loads(r.game_log) if r.game_log else []
    return {
        "id": r.id, "room_code": r.room_code, "creator_nickname": r.creator_nickname,
        "status": r.status, "result": r.result,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "game_log": game_log,
    }


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