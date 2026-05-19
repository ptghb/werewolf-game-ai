from __future__ import annotations

import logging
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.events import GameEvent
from app.game.state import GameState
from app.players.base import ActionPrompt, Player


logger = logging.getLogger("werewolf.game.phase")


async def run_witch_action(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    deadline_ts: float,
) -> None:
    state.phase = Phase.WITCH_ACTION
    logger.info("阶段开始 | 女巫行动 | day=%d", state.day_number)
    await broadcaster.broadcast(GameEvent(
        type="phase_change", payload={"phase": "witch_action", "deadline_ts": deadline_ts},
    ))
    alive_witch_ids = {p.id for p in state.alive_players_by_role(Role.WITCH)}
    witch = next((p for p in players if p.id in alive_witch_ids), None)
    if witch is None:
        logger.info("女巫已死亡，跳过")
        return

    logger.info("女巫信息 | save_left=%s | poison_left=%s | tonight_killed=%s",
                state.witch.save_left, state.witch.poison_left, state.tonight_killed_by_wolves)

    killed_id = state.tonight_killed_by_wolves
    killed_name = state.get_player(killed_id).nickname if killed_id else None
    await witch.notify(GameEvent(
        type="witch_info",
        payload={
            "tonight_killed": killed_id,
            "tonight_killed_name": killed_name,
            "save_left": state.witch.save_left,
            "poison_left": state.witch.poison_left,
        },
        audience=f"player:{witch.id}",
    ))

    # Stage 1: Save — only if save is available and someone was killed
    if state.witch.save_left and killed_id and not state.tonight_saved_by_witch:
        nickname_map = {p.id: p.nickname for p in state.players}
        resp = await witch.request(ActionPrompt(
            action="witch_save",
            options=[killed_id],
            deadline_ts=deadline_ts,
            hint=f"今晚被狼人杀死的是 {killed_name}。是否使用救药？",
            nickname_map=nickname_map,
        ))
        if resp.action != "witch_skip" and resp.target == killed_id:
            state.tonight_saved_by_witch = True
            state.witch.save_left = False
            logger.info("女巫使用救药 | target=%s", killed_id)
        else:
            logger.info("女巫不使用救药")

    # Stage 2: Poison — if poison still available
    if state.witch.poison_left:
        options = [p.id for p in state.alive_players() if p.id != witch.id]
        nickname_map = {p.id: p.nickname for p in state.players}
        resp = await witch.request(ActionPrompt(
            action="witch_poison",
            options=options,
            deadline_ts=deadline_ts,
            hint="是否使用毒药毒杀一名玩家？",
            nickname_map=nickname_map,
        ))
        if resp.action != "witch_skip" and resp.target and resp.target in options:
            state.tonight_poisoned_by_witch = resp.target
            state.witch.poison_left = False
            logger.info("女巫使用毒药 | target=%s", resp.target)
        else:
            logger.info("女巫不使用毒药")


__all__ = ["run_witch_action"]