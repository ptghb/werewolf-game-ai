from __future__ import annotations

import logging
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.events import GameEvent
from app.game.state import GameState
from app.players.base import ActionPrompt, Player


logger = logging.getLogger("werewolf.game.phase")


async def run_seer_check(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    deadline_ts: float,
) -> None:
    state.phase = Phase.SEER_CHECK
    logger.info("阶段开始 | 预言家查验 | day=%d", state.day_number)
    await broadcaster.broadcast(GameEvent(
        type="phase_change", payload={"phase": "seer_check", "deadline_ts": deadline_ts},
    ))
    seer = next(
        (p for p in players
         if p.role == Role.SEER
         and state.get_player(p.id) is not None
         and state.get_player(p.id).alive),
        None,
    )
    if seer is None:
        logger.info("预言家已死亡，跳过")
        return
    options = [p.id for p in state.alive_players() if p.id != seer.id]
    nickname_map = {p.id: p.nickname for p in state.players}
    resp = await seer.request(ActionPrompt(
        action="seer_check", options=options, deadline_ts=deadline_ts, nickname_map=nickname_map,
    ))
    if resp.target is None or resp.target not in options:
        logger.info("预言家跳过查验")
        return
    target = state.get_player(resp.target)
    is_wolf = target.role == Role.WEREWOLF
    logger.info("预言家查验结果 | target=%s(%s) | is_wolf=%s",
                target.id, target.nickname, is_wolf)
    await seer.notify(GameEvent(
        type="seer_result",
        payload={"target_id": target.id, "target_name": target.nickname, "is_wolf": is_wolf},
        audience=f"player:{seer.id}",
    ))


__all__ = ["run_seer_check"]
