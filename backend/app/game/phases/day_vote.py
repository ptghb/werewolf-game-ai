from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase
from app.game.events import GameEvent
from app.game.state import GameState
from app.game.vote import tally_votes
from app.players.base import ActionPrompt, Player


logger = logging.getLogger("werewolf.game.phase")


async def _collect_votes(
    voters: list[Player],
    options: list[str],
    action_name: str,
    deadline_ts: float,
) -> dict[str, str | None]:
    prompts = [
        ActionPrompt(action=action_name, options=options, deadline_ts=deadline_ts)
        for _ in voters
    ]
    responses = await asyncio.gather(*(v.request(p) for v, p in zip(voters, prompts)))
    return {
        v.id: (r.target if r.target in options else None)
        for v, r in zip(voters, responses)
    }


async def run_day_vote(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    deadline_ts: float,
) -> dict:
    state.phase = Phase.DAY_VOTE
    logger.info("阶段开始 | 白天投票 | day=%d", state.day_number)
    await broadcaster.broadcast(GameEvent(
        type="phase_change", payload={"phase": "day_vote", "deadline_ts": deadline_ts},
    ))
    player_lookup = {p.id: p for p in players}
    alive_ids = [p.id for p in state.alive_players()]
    voters = [player_lookup[pid] for pid in alive_ids if pid in player_lookup]

    votes = await _collect_votes(voters, alive_ids, "day_vote", deadline_ts)
    state.last_vote_tally = {k: v for k, v in votes.items() if v is not None}
    logger.info("第一轮投票 | votes=%s", votes)
    await broadcaster.broadcast(GameEvent(
        type="vote_tally", payload={"votes": votes, "round": 1},
    ))

    vote_result = tally_votes(votes)
    eliminated: str | None = None
    pk_used = False
    if vote_result.kind == "winner":
        eliminated = vote_result.winner
        logger.info("投票结果 | 出局=%s | 得票=%d", eliminated, vote_result.counts.get(eliminated, 0))
    elif vote_result.kind == "tie":
        pk_used = True
        candidates = vote_result.tied_candidates
        logger.info("投票平局 | candidates=%s | 进入PK轮", candidates)
        await broadcaster.broadcast(GameEvent(
            type="pk_round", payload={"candidates": candidates},
        ))
        pk_votes = await _collect_votes(voters, candidates, "day_vote_pk", deadline_ts)
        logger.info("PK投票 | votes=%s", pk_votes)
        await broadcaster.broadcast(GameEvent(
            type="vote_tally", payload={"votes": pk_votes, "round": 2},
        ))
        pk_result = tally_votes(pk_votes)
        if pk_result.kind == "winner":
            eliminated = pk_result.winner
            logger.info("PK结果 | 出局=%s | 得票=%d", eliminated, pk_result.counts.get(eliminated, 0))
        else:
            logger.info("PK仍平局，无人出局 | candidates=%s", pk_result.tied_candidates)
    else:
        logger.info("无人投票")

    if eliminated:
        victim = state.get_player(eliminated)
        if victim:
            victim.alive = False
        logger.info("放逐 | player=%s(%s) | is_ai=%s",
                    eliminated, victim.nickname if victim else "?", victim.is_ai if victim else "?")
        await broadcaster.broadcast(GameEvent(
            type="death_announce", payload={"dead": [eliminated], "reason": "vote"},
        ))
        speaker = player_lookup.get(eliminated)
        if speaker is not None:
            resp = await speaker.request(ActionPrompt(
                action="last_words",
                deadline_ts=deadline_ts,
                hint="Your final words (<=80 chars)",
            ))
            text = (resp.text or "").strip()
            if text:
                await broadcaster.broadcast(GameEvent(
                    type="chat_message",
                    payload={"from": eliminated, "from_name": speaker.nickname, "text": text, "channel": "day", "last_words": True},
                ))
            if victim:
                victim.used_last_words = True
    return {"eliminated": eliminated, "pk_used": pk_used, "votes": votes}


__all__ = ["run_day_vote"]
