from __future__ import annotations

import asyncio
import logging
from collections import Counter
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.events import GameEvent
from app.game.state import GameState, PlayerState
from app.game.vote import tally_votes
from app.players.base import ActionPrompt, Player


logger = logging.getLogger("werewolf.game.phase")


def _is_revealed_idiot(player: PlayerState) -> bool:
    return player.role == Role.IDIOT and player.idiot_revealed


def _can_vote(player: PlayerState) -> bool:
    return player.alive and not _is_revealed_idiot(player)


def _can_be_voted(player: PlayerState) -> bool:
    return player.alive and not _is_revealed_idiot(player)


def _format_vote_summary(votes: dict[str, str | None], nickname_map: dict[str, str]) -> str:
    """Format vote tally as a readable summary."""
    targets = [t for t in votes.values() if t is not None]
    if not targets:
        return "无人投票"
    counts = Counter(targets)
    parts = [f"{nickname_map.get(pid, pid)}({n}票)" for pid, n in counts.most_common()]
    return "、".join(parts)


async def _collect_votes(
    voters: list[Player],
    options: list[str],
    action_name: str,
    deadline_ts: float,
    nickname_map: dict[str, str],
) -> dict[str, str | None]:
    prompts = [
        ActionPrompt(action=action_name, options=options, deadline_ts=deadline_ts, nickname_map=nickname_map)
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
    await broadcaster.broadcast(GameEvent(
        type="system_announce",
        payload={"text": "投票开始，请选择你要放逐的玩家"},
    ))

    player_lookup = {p.id: p for p in players}
    vote_options = [p.id for p in state.players if _can_be_voted(p)]
    voter_ids = [p.id for p in state.players if _can_vote(p)]
    voters = [player_lookup[pid] for pid in voter_ids if pid in player_lookup]
    nickname_map = {p.id: p.nickname for p in state.players}

    votes = await _collect_votes(voters, vote_options, "day_vote", deadline_ts, nickname_map)
    state.last_vote_tally = {k: v for k, v in votes.items() if v is not None}
    logger.info("第一轮投票 | votes=%s", votes)
    await broadcaster.broadcast(GameEvent(
        type="vote_tally", payload={"votes": votes, "round": 1},
    ))
    await broadcaster.broadcast(GameEvent(
        type="system_announce",
        payload={"text": f"第一轮投票结果：{_format_vote_summary(votes, nickname_map)}"},
    ))

    vote_result = tally_votes(votes)
    eliminated: str | None = None
    pk_used = False
    if vote_result.kind == "winner":
        eliminated = vote_result.winner
        logger.info("投票结果 | 出局=%s | 得票=%d", eliminated, vote_result.counts.get(eliminated, 0))
    elif vote_result.kind == "tie":
        candidates = [candidate for candidate in vote_result.tied_candidates if candidate in vote_options]
        pk_used = bool(candidates)
        logger.info("投票平局 | candidates=%s | 进入PK轮", candidates)
        pk_names = "、".join(nickname_map.get(c, c) for c in candidates)
        await broadcaster.broadcast(GameEvent(
            type="system_announce",
            payload={"text": f"平票！进入平票PK投票，候选玩家：{pk_names}"},
        ))
        await broadcaster.broadcast(GameEvent(
            type="pk_round", payload={"candidates": candidates},
        ))
        pk_votes = await _collect_votes(voters, candidates, "day_vote_pk", deadline_ts, nickname_map)
        logger.info("PK投票 | votes=%s", pk_votes)
        await broadcaster.broadcast(GameEvent(
            type="vote_tally", payload={"votes": pk_votes, "round": 2},
        ))
        await broadcaster.broadcast(GameEvent(
            type="system_announce",
            payload={"text": f"平票PK投票结果：{_format_vote_summary(pk_votes, nickname_map)}"},
        ))
        pk_result = tally_votes(pk_votes)
        if pk_result.kind == "winner":
            eliminated = pk_result.winner
            logger.info("PK结果 | 出局=%s | 得票=%d", eliminated, pk_result.counts.get(eliminated, 0))
        else:
            logger.info("PK仍平局，无人出局 | candidates=%s", pk_result.tied_candidates)
    else:
        logger.info("无人投票")

    idiot_revealed: str | None = None
    if eliminated:
        victim = state.get_player(eliminated)
        if victim and victim.role == Role.IDIOT and not victim.idiot_revealed:
            victim.idiot_revealed = True
            idiot_revealed = eliminated
            eliminated = None
            logger.info("白痴翻牌免死 | player=%s(%s)", victim.id, victim.nickname)
            await broadcaster.broadcast(GameEvent(
                type="system_announce",
                payload={"text": f"{victim.nickname} 是白痴，翻牌免死，本轮无人被放逐"},
            ))
            await broadcaster.broadcast(GameEvent(
                type="idiot_reveal", payload={"player_id": victim.id},
            ))
        else:
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
                    nickname_map=nickname_map,
                ))
                text = (resp.text or "").strip()
                if text:
                    await broadcaster.broadcast(GameEvent(
                        type="chat_message",
                        payload={"from": eliminated, "from_name": speaker.nickname, "text": text, "channel": "day", "last_words": True},
                    ))
                if victim:
                    victim.used_last_words = True
    else:
        await broadcaster.broadcast(GameEvent(
            type="system_announce",
            payload={"text": "本轮无人被放逐"},
        ))
    return {"eliminated": eliminated, "idiot_revealed": idiot_revealed, "pk_used": pk_used, "votes": votes}


__all__ = ["run_day_vote"]
