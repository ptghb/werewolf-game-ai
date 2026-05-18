from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.events import GameEvent
from app.game.state import GameState
from app.players.base import ActionPrompt, Player


logger = logging.getLogger("werewolf.game.phase")


async def run_hunter_shot(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    deadline_ts: float,
) -> str | None:
    """Handle the hunter's revenge shot when eliminated.

    Only triggers if ``state.hunter_just_died`` is ``True`` and the hunter
    still has the ability to shoot (``state.hunter_can_shoot``).

    Returns the player id that the hunter shot, or ``None``.
    """
    if not state.hunter_just_died or not state.hunter_can_shoot:
        logger.info("猎人不开枪 | just_died=%s can_shoot=%s",
                    state.hunter_just_died, state.hunter_can_shoot)
        return None

    state.phase = Phase.HUNTER_SHOT
    logger.info("阶段开始 | 猎人开枪 | day=%d | reason=%s",
                state.day_number, state.last_death_reason)
    await broadcaster.broadcast(GameEvent(
        type="phase_change",
        payload={"phase": "hunter_shot", "deadline_ts": deadline_ts},
    ))

    # Locate hunter player state and player object
    hunter_player_state = next(
        (p for p in state.players if p.role == Role.HUNTER), None
    )
    hunter_player_obj = next(
        (p for p in players if p.role == Role.HUNTER), None
    )

    if hunter_player_state is None:
        logger.warning("猎人阶段但找不到猎人玩家状态")
        state.hunter_can_shoot = False
        return None
    if hunter_player_obj is None:
        logger.warning("猎人阶段但找不到猎人玩家对象")
        state.hunter_can_shoot = False
        return None

    alive_ids = [p.id for p in state.alive_players()]
    if not alive_ids:
        logger.info("没有存活目标，猎人无法开枪")
        state.hunter_can_shoot = False
        return None

    nickname_map = {p.id: p.nickname for p in state.players}
    prompt = ActionPrompt(
        action="hunter_shot",
        options=alive_ids,
        deadline_ts=deadline_ts,
        nickname_map=nickname_map,
    )
    try:
        resp = await asyncio.wait_for(
            hunter_player_obj.request(prompt),
            timeout=max(1.0, deadline_ts - __import__("time").time()),
        )
    except (asyncio.TimeoutError, Exception) as exc:
        logger.info("猎人超时/异常 | %s", exc)
        resp = None

    target = None
    if resp is not None and hasattr(resp, "target") and resp.target in alive_ids:
        target = resp.target

    if target is None:
        logger.info("猎人未选择开枪 | 不开枪")
        await broadcaster.broadcast(GameEvent(
            type="hunter_shot",
            payload={"target": None, "shooter": hunter_player_state.id},
        ))
        state.hunter_can_shoot = False
        return None

    # Hunter shot a target
    victim = state.get_player(target)
    if victim:
        victim.alive = False

    state.hunter_can_shoot = False

    logger.info("猎人开枪 | shooter=%s | target=%s(%s)",
                hunter_player_state.id, target, victim.nickname if victim else "?")
    await broadcaster.broadcast(GameEvent(
        type="hunter_shot",
        payload={
            "shooter": hunter_player_state.id,
            "target": target,
        },
    ))
    await broadcaster.broadcast(GameEvent(
        type="death_announce",
        payload={"dead": [target], "reason": "hunter_shot"},
    ))

    # Give last words to the shot player
    target_player_obj = next((p for p in players if p.id == target), None)
    if target_player_obj is not None:
        try:
            last_words_resp = await target_player_obj.request(ActionPrompt(
                action="last_words", deadline_ts=deadline_ts,
                hint="Your final words (<=80 chars)",
                nickname_map=nickname_map,
            ))
            text = (last_words_resp.text or "").strip()
            if text:
                await broadcaster.broadcast(GameEvent(
                    type="chat_message",
                    payload={
                        "from": target, "from_name": target_player_obj.nickname,
                        "text": text, "channel": "day", "last_words": True,
                    },
                ))
            if victim:
                victim.used_last_words = True
        except Exception:
            pass

    return target


__all__ = ["run_hunter_shot"]