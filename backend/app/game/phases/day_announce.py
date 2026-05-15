from __future__ import annotations

import logging
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase
from app.game.events import GameEvent
from app.game.state import GameState
from app.players.base import ActionPrompt, Player


logger = logging.getLogger("werewolf.game.phase")


async def run_day_announce(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    deadline_ts: float,
) -> list[str]:
    state.phase = Phase.DAY_ANNOUNCE
    state.day_number += 1
    logger.info("========== 天亮 | 第 %d 天 ==========", state.day_number)
    await broadcaster.broadcast(GameEvent(
        type="phase_change", payload={"phase": "day_announce", "day": state.day_number,
                                      "deadline_ts": deadline_ts},
    ))
    dead_ids: list[str] = []
    killed = state.tonight_killed_by_wolves
    if killed and not state.tonight_saved_by_witch:
        dead_ids.append(killed)
    poisoned = state.tonight_poisoned_by_witch
    if poisoned and poisoned != killed:
        dead_ids.append(poisoned)

    for pid in dead_ids:
        p = state.get_player(pid)
        if p and p.alive:
            p.alive = False

    logger.info("死亡公告 | night_killed=%s | saved=%s | poisoned=%s | dead=%s",
                killed, state.tonight_saved_by_witch, poisoned, dead_ids)

    await broadcaster.broadcast(GameEvent(
        type="death_announce",
        payload={"dead": dead_ids, "reason": "night" if dead_ids else "peaceful"},
    ))

    lookup = {p.id: p for p in players}
    for pid in dead_ids:
        player = lookup.get(pid)
        if player is None:
            continue
        resp = await player.request(ActionPrompt(
            action="last_words", deadline_ts=deadline_ts,
            hint="Your final words (<=80 chars)",
        ))
        text = (resp.text or "").strip()
        if text:
            await broadcaster.broadcast(GameEvent(
                type="chat_message",
                payload={"from": pid, "from_name": player.nickname, "text": text, "channel": "day", "last_words": True},
            ))
        state.get_player(pid).used_last_words = True

    state.tonight_killed_by_wolves = None
    state.tonight_poisoned_by_witch = None
    state.tonight_saved_by_witch = False
    return dead_ids


__all__ = ["run_day_announce"]
