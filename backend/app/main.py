from __future__ import annotations

import asyncio
from datetime import date
import json
import logging
import random

import os
import json

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.game.assign import assign_roles
from app.game.constants import Phase, Role
from app.game.engine import GameEngine
from app.game.events import GameEvent
from app.players.ai import AIPlayer
from app.ai.llm import build_llm
from app.rooms.room_manager import RoomManager
from app.auth_routes import router as auth_router
from sqlalchemy import select, func
from app.database.session import async_session_factory
from app.database.models import Room as RoomModel


logger = logging.getLogger("werewolf")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


app = FastAPI(title="Werewolf AI Backend")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)
manager = RoomManager()
app.include_router(auth_router)


class CreateRoomBody(BaseModel):
    user_id: int
    nickname: str
    mode: str = "6"


class JoinRoomBody(BaseModel):
    nickname: str


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.post("/api/rooms")
async def create_room(body: CreateRoomBody):
    from app.database.models import User as UserModel
    today = date.today()
    async with async_session_factory() as session:
        user = (await session.execute(select(UserModel).where(UserModel.id == body.user_id))).scalar_one_or_none()
        is_vip = user is not None and user.vip != 0
        if not is_vip:
            stmt = select(func.count()).select_from(RoomModel).where(
                RoomModel.creator_id == body.user_id,
                func.date(RoomModel.created_at) == today,
            )
            result = await session.execute(stmt)
            today_count = result.scalar() or 0
            if today_count >= 3:
                raise HTTPException(status_code=429, detail="今日游戏次数已达上限（3次），请明天再来")
    try:
        room = await manager.create_room(
            creator_id=body.user_id, host_nickname=body.nickname,
            mode=body.mode,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"room_code": room.code, "host_id": room.host_id}


@app.post("/api/rooms/{code}/join")
async def join_room(code: str, body: JoinRoomBody):
    try:
        pid = await manager.join_room(code, nickname=body.nickname)
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"player_id": pid, "room_code": code}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    # Handshake: first message must be {type:"hello", room, player_id}
    hello = await ws.receive_json()
    if hello.get("type") != "hello":
        await ws.close(code=1003)
        return
    room = manager.get_room(hello.get("room"))
    if room is None:
        await ws.send_json({"type": "error", "payload": {"code": "no_room", "message": "unknown room"}})
        await ws.close()
        return
    player = room.get_player(hello.get("player_id"))
    if player is None or player.is_ai:
        await ws.send_json({"type": "error", "payload": {"code": "no_player", "message": "unknown or AI player"}})
        await ws.close()
        return
    await player.attach(ws, last_ack_seq=int(hello.get("last_ack_seq", 0)))

    # Send room state immediately so the client knows the player list
    await ws.send_json({
        "type": "room_state",
        "payload": {
            "room_code": room.code,
            "host_id": room.host_id,
            "players": [
                {
                    "id": p.id,
                    "nickname": p.nickname,
                    "seat": p.seat,
                    "is_ai": p.is_ai,
                    "alive": p.alive,
                    "connected": getattr(p, "socket", None) is not None or p.is_ai,
                }
                for p in room.players
            ],
        },
        "seq": player._next_seq(),
    })

    try:
        while True:
            msg = await ws.receive_json()
            mtype = msg.get("type")
            payload = msg.get("payload", {}) or {}
            if mtype == "ack":
                player.prune_acked(int(payload.get("seq", 0)))
            elif mtype == "action":
                await player.deliver_action(payload)
            elif mtype == "chat":
                entry = {"from": player.id, "from_name": player.nickname, **payload}
                room.chat_log.append(entry)
                await room.queue.put({"type": "chat", **entry})
            elif mtype == "start_game":
                if player.id == room.host_id:
                    preferred = payload.get("preferred_role") if isinstance(payload, dict) else None
                    asyncio.create_task(_run_game(room, preferred_role=preferred))
    except WebSocketDisconnect:
        await player.detach()


async def _run_game(room, preferred_role=None) -> None:
    logger.info("游戏开始 | room=%s | players=%s",
                room.code,
                [{"id": p.id, "nickname": p.nickname, "type": "AI" if p.is_ai else "Human"}
                 for p in room.players])
    try:
        # Assign roles
        roles = assign_roles(len(room.players))
        for player, role in zip(room.players, roles):
            player.role = role

        # VIP 优先选角色：把房主的角色与目标角色交换
        if preferred_role:
            try:
                wanted = Role(preferred_role)
                host = next(p for p in room.players if p.id == room.host_id)
                logger.info("VIP优先选角 | host=%s wanted=%s current=%s", host.nickname, preferred_role, host.role.value)
                if host.role != wanted:
                    target = next(p for p in room.players if p.role == wanted)
                    logger.info("VIP角色交换 | %s<->%s", host.nickname, target.nickname)
                    host.role, target.role = target.role, host.role
                else:
                    logger.info("VIP角色已匹配 | host=%s role=%s", host.nickname, host.role.value)
            except (ValueError, StopIteration) as e:
                logger.warning("VIP优先选角失败 | error=%s", e)

        wolf_ids = []
        for player in room.players:
            logger.info("角色分配 | player=%s(%s) | seat=%s | role=%s",
                        player.id, player.nickname, player.seat, player.role.value)
            if player.role == Role.WEREWOLF:
                wolf_ids.append(player.id)
        for p in room.players:
            if p.role == Role.WEREWOLF and hasattr(p, "wolf_teammates"):
                p.wolf_teammates = [w for w in wolf_ids if w != p.id]
            # Notify role privately
            extra = {"wolf_teammates": [w for w in wolf_ids if w != p.id]} if p.role == Role.WEREWOLF else {}
            await p.notify(GameEvent(
                type="role_assigned",
                payload={"role": p.role.value, **extra},
                audience=f"player:{p.id}",
            ))

        # Attach llm lazily for AI players
        for p in room.players:
            if isinstance(p, AIPlayer) and p.llm is None:
                try:
                    p.llm = build_llm()
                except Exception:
                    p.llm = None  # fallback path kicks in inside AIPlayer

        # Pick start seat
        start_id = random.choice(room.players).id

        # Broadcast phase change to all players so the frontend knows game started
        for p in room.players:
            await p.notify(GameEvent(
                type="phase_change",
                payload={"phase": Phase.NIGHT_START.value, "deadline_ts": None, "day": 1},
            ))

        # 更新游戏状态为 playing
        async with async_session_factory() as session:
            r = (await session.execute(select(RoomModel).where(RoomModel.room_code == room.code))).scalar_one_or_none()
            if r:
                r.status = "playing"
                await session.commit()

        _player_map = {p.id: p.nickname for p in room.players}
        def _nickname(pid):
            return _player_map.get(pid, pid)

        def _death_label(reason, dead, nick_fn):
            labels = {"wolf": "狼人杀害", "vote": "投票放逐", "hunter_shot": "猎人开枪", "night": "昨夜死亡"}
            if reason == "peaceful" or not dead:
                return "昨夜是平安夜，无人死亡"
            label = labels.get(reason, reason)
            names = ",".join(nick_fn(p) for p in dead)
            return f"{label}：{names}"

        def _chat_log(from_id, from_name, text):
            room.chat_log.append({"from": from_id, "from_name": from_name, "text": text})

        engine = GameEngine(room_code=room.code, players=room.players,
                            start_player_id=start_id, on_chat=_chat_log,
                            on_system=lambda text: room.chat_log.append({"type": "system", "text": text}),
                            on_death=lambda dead, reason: room.chat_log.append(
                                {"type": "system", "text": _death_label(reason, dead, _nickname)}))
        await engine.run_until_game_over()
        logger.info("游戏结束 | room=%s | winner=%s", room.code, engine.winner)

        # 在日志开头插入玩家角色信息
        room.chat_log.insert(0, {
            "type": "system",
            "text": f"玩家列表：{' | '.join(f'{_nickname(p.id)}={p.role.value}' for p in room.players)}"
        })

        # 更新房间结果和聊天记录
        async with async_session_factory() as session:
            r = (await session.execute(select(RoomModel).where(RoomModel.room_code == room.code))).scalar_one_or_none()
            if r:
                r.status = "finished"
                r.result = engine.winner
                r.game_log = json.dumps(room.chat_log, ensure_ascii=False)
                await session.commit()
    except Exception as e:
        import traceback
        logger.error("游戏运行异常", exc_info=True)
        for p in room.players:
            try:
                await p.notify(GameEvent(
                    type="system_announce",
                    payload={"text": f"游戏发生错误: {str(e)}"},
                ))
            except Exception:
                pass


def main():
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    main()