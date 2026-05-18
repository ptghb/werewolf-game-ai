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

    await witch.notify(GameEvent(
        type="witch_info",
        payload={
            "tonight_killed": state.tonight_killed_by_wolves,
            "tonight_killed_name": (state.get_player(state.tonight_killed_by_wolves).nickname
                                     if state.tonight_killed_by_wolves else None),
            "save_left": state.witch.save_left,
            "poison_left": state.witch.poison_left,
        },
        audience=f"player:{witch.id}",
    ))
    options = [p.id for p in state.alive_players()]
    nickname_map = {p.id: p.nickname for p in state.players}
    resp = await witch.request(ActionPrompt(
        action="witch_action", options=options, deadline_ts=deadline_ts,
        hint="Reply via witch_save/witch_poison/witch_skip",
        nickname_map=nickname_map,
    ))
    if resp.action == "witch_save" and state.witch.save_left:
        if state.tonight_killed_by_wolves and resp.target == state.tonight_killed_by_wolves:
            state.tonight_saved_by_witch = True
            state.witch.save_left = False
            logger.info("女巫使用救药 | target=%s", resp.target)
            return
        else:
            logger.warning("女巫救药目标无效 | target=%s | killed=%s",
                           resp.target, state.tonight_killed_by_wolves)
    if resp.action == "witch_poison" and state.witch.poison_left:
        if resp.target in options:
            state.tonight_poisoned_by_witch = resp.target
            state.witch.poison_left = False
            logger.info("女巫使用毒药 | target=%s", resp.target)
            return


__all__ = ["run_witch_action"]
