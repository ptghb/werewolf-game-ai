from __future__ import annotations

import asyncio
import random
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.events import GameEvent
from app.game.state import GameState
from app.game.vote import tally_votes
from app.players.base import ActionPrompt, Player


async def run_wolf_kill(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    deadline_ts: float,
    rng: random.Random | None = None,
) -> str | None:
    rng = rng or random.Random()
    state.phase = Phase.WOLF_KILL
    await broadcaster.broadcast(GameEvent(
        type="phase_change", payload={"phase": "wolf_kill", "deadline_ts": deadline_ts},
    ))
    wolves = [p for p in players if p.role == Role.WEREWOLF and p.alive]
    alive_non_wolf = [p for p in state.alive_players() if p.role != Role.WEREWOLF]
    options = [p.id for p in alive_non_wolf]
    prompts = [
        ActionPrompt(action="wolf_vote", options=options, deadline_ts=deadline_ts)
        for _ in wolves
    ]
    responses = await asyncio.gather(
        *(w.request(p) for w, p in zip(wolves, prompts))
    )
    votes = {w.id: (r.target if r.target in options else None)
             for w, r in zip(wolves, responses)}
    result = tally_votes(votes)
    if result.kind == "winner":
        target = result.winner
    elif result.kind == "tie":
        target = rng.choice(result.tied_candidates)
    else:
        target = None
    state.tonight_killed_by_wolves = target
    return target


__all__ = ["run_wolf_kill"]
