from __future__ import annotations

import asyncio
from typing import Iterable

from app.game.events import GameEvent
from app.game.state import GameState
from app.game.visibility import is_visible_to
from app.players.base import Player


class Broadcaster:
    def __init__(self, state: GameState, players: Iterable[Player]):
        self.state = state
        self.players = list(players)

    async def broadcast(self, event: GameEvent) -> None:
        targets = [p for p in self.players
                   if is_visible_to(event, self.state.get_player(p.id), self.state)]
        if not targets:
            return
        await asyncio.gather(*(p.notify(event) for p in targets))


__all__ = ["Broadcaster"]
