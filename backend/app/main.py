from __future__ import annotations

import asyncio
import json
import logging
import random

import os

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


class CreateRoomBody(BaseModel):
    nickname: str
    mode: str = "6"


class JoinRoomBody(BaseModel):
    nickname: str


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.post("/api/rooms")
async def create_room(body: CreateRoomBody):
    try:
        room = await manager.create_room(
            host_nickname=body.nickname,
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
                await room.queue.put({"type": "chat", **payload, "from": player.id, "from_name": player.nickname})
            elif mtype == "start_game":
                if player.id == room.host_id:
                    asyncio.create_task(_run_game(room))
    except WebSocketDisconnect:
        await player.detach()


async def _run_game(room) -> None:
    logger.info("游戏开始 | room=%s | players=%s",
                room.code,
                [{"id": p.id, "nickname": p.nickname, "type": "AI" if p.is_ai else "Human"}
                 for p in room.players])
    try:
        # Assign roles
        roles = assign_roles(len(room.players))
        wolf_ids = []
        for player, role in zip(room.players, roles):
            player.role = role
            logger.info("角色分配 | player=%s(%s) | seat=%s | role=%s",
                        player.id, player.nickname, player.seat, role.value)
            if role == Role.WEREWOLF:
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

        engine = GameEngine(room_code=room.code, players=room.players, start_player_id=start_id)
        await engine.run_until_game_over()
        logger.info("游戏结束 | room=%s | winner=%s", room.code, engine.winner)
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