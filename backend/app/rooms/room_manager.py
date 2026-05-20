from __future__ import annotations

import random
import string
import time
import uuid
from asyncio import Lock
from typing import Optional, Dict

from app.ai.personas import random_persona
from app.game.constants import Role
from app.players.ai import AIPlayer
from app.players.human import HumanPlayer
from app.rooms.room import Room


def _new_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


class RoomManager:
    def __init__(self):
        self._rooms: Dict[str, Room] = {}
        self._lock = Lock()

    async def create_room(self, *, host_nickname: str, mode: str = "6") -> Room:
        if mode == "6":
            ai_slots = 5
        elif mode == "9":
            ai_slots = 8
        elif mode == "12":
            ai_slots = 11
        else:
            raise ValueError(f"Invalid mode: {mode}")
        async with self._lock:
            code = _new_code()
            while code in self._rooms:
                code = _new_code()
            host_id = f"h_{uuid.uuid4().hex[:8]}"
            host = HumanPlayer(id=host_id, nickname=host_nickname,
                               role=Role.VILLAGER, seat=0)
            ai_players = []
            nickname_counts: Dict[str, int] = {}
            for i in range(ai_slots):
                persona = random_persona()
                nickname_counts[persona.name] = nickname_counts.get(persona.name, 0) + 1
                nickname = persona.name if nickname_counts[persona.name] == 1 else f"{persona.name}{nickname_counts[persona.name]}"
                ai_players.append(AIPlayer(
                    id=f"ai_{uuid.uuid4().hex[:8]}",
                    nickname=nickname,
                    role=Role.VILLAGER,  # reassigned at game start
                    seat=1 + i,  # seat 0 is host
                    persona=persona,
                ))
            room = Room(code=code, host_id=host_id,
                        human_slots=1, ai_slots=ai_slots,
                        players=[host, *ai_players], created_at=time.time())
            self._rooms[code] = room
            return room

    async def join_room(self, code: str, *, nickname: str) -> str:
        async with self._lock:
            room = self._rooms.get(code)
            if room is None:
                raise KeyError(f"Room not found: {code}")
            if room.full:
                raise ValueError("Room is full")
            pid = f"h_{uuid.uuid4().hex[:8]}"
            seat = next((i for i, p in enumerate(room.players) if p.is_ai), len(room.players))
            hp = HumanPlayer(id=pid, nickname=nickname, role=Role.VILLAGER, seat=seat)
            ai_idx = next((i for i, p in enumerate(room.players) if p.is_ai), None)
            if ai_idx is not None:
                room.players[ai_idx] = hp
            else:
                room.players.append(hp)
            return pid

    def get_room(self, code: str) -> Optional[Room]:
        return self._rooms.get(code)

    def destroy(self, code: str) -> None:
        self._rooms.pop(code, None)