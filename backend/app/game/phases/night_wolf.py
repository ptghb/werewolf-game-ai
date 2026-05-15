from __future__ import annotations

import asyncio
import logging
import random
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.events import GameEvent
from app.game.state import GameState
from app.game.vote import tally_votes
from app.players.base import ActionPrompt, Player


logger = logging.getLogger("werewolf.game.phase")


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
    logger.info("阶段开始 | 狼人杀人 | day=%d", state.day_number)
    await broadcaster.broadcast(GameEvent(
        type="phase_change", payload={"phase": "wolf_kill", "deadline_ts": deadline_ts},
    ))
    alive_wolf_ids = {p.id for p in state.alive_players_by_role(Role.WEREWOLF)}
    wolves = [p for p in players if p.id in alive_wolf_ids]
    alive_non_wolf = [p for p in state.alive_players() if p.role != Role.WEREWOLF]
    options = [p.id for p in alive_non_wolf]
    logger.info("狼人列表 | %s | 可选目标 | %s",
                [w.id for w in wolves], options)
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
    logger.info("狼人投票结果 | votes=%s | result=%s", votes, result)

    if result.kind == "winner":
        target = result.winner
    elif result.kind == "tie":
        target = rng.choice(result.tied_candidates)
        logger.info("狼人投票平局 | candidates=%s | 随机选择=%s", result.tied_candidates, target)
    else:
        target = None
        logger.warning("狼人无人投票")
    state.tonight_killed_by_wolves = target
    logger.info("狼人杀人结果 | target=%s", target)
    return target


__all__ = ["run_wolf_kill"]
