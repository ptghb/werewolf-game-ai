from __future__ import annotations

from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.events import GameEvent
from app.game.state import GameState
from app.players.base import ActionPrompt, Player


async def run_seer_check(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    deadline_ts: float,
) -> None:
    state.phase = Phase.SEER_CHECK
    await broadcaster.broadcast(GameEvent(
        type="phase_change", payload={"phase": "seer_check", "deadline_ts": deadline_ts},
    ))
    seer = next((p for p in players if p.role == Role.SEER and p.alive), None)
    if seer is None:
        return
    options = [p.id for p in state.alive_players() if p.id != seer.id]
    resp = await seer.request(ActionPrompt(
        action="seer_check", options=options, deadline_ts=deadline_ts,
    ))
    if resp.target is None or resp.target not in options:
        return
    target = state.get_player(resp.target)
    await seer.notify(GameEvent(
        type="seer_result",
        payload={"target_id": target.id, "is_wolf": target.role == Role.WEREWOLF},
        audience=f"player:{seer.id}",
    ))


__all__ = ["run_seer_check"]
