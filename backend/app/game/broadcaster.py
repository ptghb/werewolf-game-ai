from __future__ import annotations

import asyncio
from typing import Callable, Iterable, Optional

from app.game.events import GameEvent
from app.game.state import GameState
from app.game.visibility import is_visible_to
from app.players.base import Player


class Broadcaster:
    def __init__(self, state: GameState, players: Iterable[Player],
                 on_chat: Optional[Callable[[str, str, str], None]] = None,
                 on_system: Optional[Callable[[str], None]] = None,
                 on_death: Optional[Callable[[list[str], str], None]] = None):
        self.state = state
        self.players = list(players)
        self.on_chat = on_chat
        self.on_system = on_system
        self.on_death = on_death

    async def broadcast(self, event: GameEvent) -> None:
        targets = [p for p in self.players
                   if is_visible_to(event, self.state.get_player(p.id), self.state)]
        if not targets:
            return
        if self.on_chat and event.type == "chat_message":
            self.on_chat(event.payload.get("from", ""),
                         event.payload.get("from_name", ""),
                         event.payload.get("text", ""))
        elif self.on_system and event.type == "system_announce":
            self.on_system(event.payload.get("text", ""))
        elif self.on_death and event.type == "death_announce":
            self.on_death(event.payload.get("dead", []),
                          event.payload.get("reason", ""))
        await asyncio.gather(*(p.notify(event) for p in targets))


__all__ = ["Broadcaster"]
