from __future__ import annotations

import asyncio
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase
from app.game.events import GameEvent
from app.game.state import GameState
from app.game.vote import tally_votes
from app.players.base import ActionPrompt, Player


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
    await broadcaster.broadcast(GameEvent(
        type="phase_change", payload={"phase": "day_vote", "deadline_ts": deadline_ts},
    ))
    player_lookup = {p.id: p for p in players}
    alive_ids = [p.id for p in state.alive_players()]
    voters = [player_lookup[pid] for pid in alive_ids if pid in player_lookup]

    votes = await _collect_votes(voters, alive_ids, "day_vote", deadline_ts)
    state.last_vote_tally = {k: v for k, v in votes.items() if v is not None}
    await broadcaster.broadcast(GameEvent(
        type="vote_tally", payload={"votes": votes, "round": 1},
    ))

    vote_result = tally_votes(votes)
    eliminated: str | None = None
    pk_used = False
    if vote_result.kind == "winner":
        eliminated = vote_result.winner
    elif vote_result.kind == "tie":
        pk_used = True
        candidates = vote_result.tied_candidates
        await broadcaster.broadcast(GameEvent(
            type="pk_round", payload={"candidates": candidates},
        ))
        pk_votes = await _collect_votes(voters, candidates, "day_vote_pk", deadline_ts)
        await broadcaster.broadcast(GameEvent(
            type="vote_tally", payload={"votes": pk_votes, "round": 2},
        ))
        pk_result = tally_votes(pk_votes)
        if pk_result.kind == "winner":
            eliminated = pk_result.winner

    if eliminated:
        victim = state.get_player(eliminated)
        if victim:
            victim.alive = False
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
                    payload={"from": eliminated, "text": text, "channel": "day", "last_words": True},
                ))
            if victim:
                victim.used_last_words = True
    return {"eliminated": eliminated, "pk_used": pk_used, "votes": votes}


__all__ = ["run_day_vote"]
