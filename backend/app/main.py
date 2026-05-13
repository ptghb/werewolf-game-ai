from __future__ import annotations

import asyncio
import json
import random

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.game.assign import assign_roles
from app.game.constants import Role
from app.game.engine import GameEngine
from app.game.events import GameEvent
from app.players.ai import AIPlayer
from app.ai.llm import build_llm
from app.rooms.room_manager import RoomManager


app = FastAPI(title="Werewolf AI Backend")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)
manager = RoomManager()


class CreateRoomBody(BaseModel):
    nickname: str
    human_slots: int = 1
    ai_slots: int = 5


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
            human_slots=body.human_slots,
            ai_slots=body.ai_slots,
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
                await room.queue.put({"type": "chat", "from": player.id, **payload})
            elif mtype == "start_game":
                if player.id == room.host_id:
                    asyncio.create_task(_run_game(room))
    except WebSocketDisconnect:
        await player.detach()


async def _run_game(room) -> None:
    # Assign roles
    roles = assign_roles(6)
    wolf_ids = []
    for player, role in zip(room.players, roles):
        player.role = role
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
    start_id = room.players[random.randrange(len(room.players))].id
    engine = GameEngine(room_code=room.code, players=room.players, start_player_id=start_id)
    await engine.run_until_game_over()