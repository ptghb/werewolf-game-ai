from __future__ import annotations

import logging
import time
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase
from app.game.events import GameEvent
from app.game.state import GameState
from app.players.base import ActionPrompt, Player


logger = logging.getLogger("werewolf.game.phase")


async def run_day_speech(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    start_player_id: str,
    per_player_timeout: int,
) -> list[str]:
    state.phase = Phase.DAY_SPEECH
    player_lookup = {p.id: p for p in players}
    alive = sorted(state.alive_players(), key=lambda p: p.seat)
    if not alive:
        return []

    ids_in_seat_order = [p.id for p in alive]
    try:
        start_idx = ids_in_seat_order.index(start_player_id)
    except ValueError:
        start_player = state.get_player(start_player_id)
        start_seat = start_player.seat if start_player else 0
        seats = [p.seat for p in alive]
        start_idx = next((i for i, seat in enumerate(seats) if seat >= start_seat), 0)
    order = ids_in_seat_order[start_idx:] + ids_in_seat_order[:start_idx]

    logger.info("阶段开始 | 白天发言 | day=%d | 发言顺序=%s", state.day_number, order)

    await broadcaster.broadcast(GameEvent(
        type="phase_change",
        payload={"phase": "day_speech", "order": order, "per_player_timeout": per_player_timeout},
    ))

    nickname_map = {p.id: p.nickname for p in state.players}

    for pid in order:
        speaker = player_lookup.get(pid)
        if speaker is None:
            continue
        await broadcaster.broadcast(GameEvent(type="speech_turn", payload={"speaker": pid}))
        resp = await speaker.request(ActionPrompt(
            action="speech",
            deadline_ts=time.time() + per_player_timeout,
            hint="Your speech (<=80 chars)",
            nickname_map=nickname_map,
        ))
        text = (resp.text or "").strip()
        if text:
            await broadcaster.broadcast(GameEvent(
                type="chat_message",
                payload={"from": pid, "from_name": speaker.nickname, "text": text, "channel": "day"},
            ))
    return order


__all__ = ["run_day_speech"]
