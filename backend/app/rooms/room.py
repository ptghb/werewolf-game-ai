from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional, List

from app.game.constants import Role
from app.players.ai import AIPlayer
from app.players.human import HumanPlayer


@dataclass
class Room:
    code: str
    host_id: str
    human_slots: int
    ai_slots: int
    players: List[Any] = field(default_factory=list)  # HumanPlayer | AIPlayer
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    created_at: float = 0.0
    chat_log: list[dict] = field(default_factory=list)

    @property
    def full(self) -> bool:
        humans = sum(1 for p in self.players if not p.is_ai)
        return humans >= self.human_slots

    def get_player(self, pid: str):
        return next((p for p in self.players if p.id == pid), None)