from __future__ import annotations

import logging
import random
import time
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.events import GameEvent
from app.game.phases.day_announce import run_day_announce
from app.game.phases.day_speech import run_day_speech
from app.game.phases.day_vote import run_day_vote
from app.game.phases.hunter_shot import run_hunter_shot
from app.game.phases.night_seer import run_seer_check
from app.game.phases.night_witch import run_witch_action
from app.game.phases.night_wolf import run_wolf_kill
from app.game.state import GameState, PlayerState
from app.game.win_check import check_winner
from app.players.base import Player


logger = logging.getLogger("werewolf.game")


DEFAULT_TIMEOUTS = {
    "wolf_kill": 45,
    "seer_check": 20,
    "witch_action": 25,
    "day_announce": 5,
    "day_speech": 60,
    "day_vote": 30,
    "hunter_shot": 30,
    "last_words": 30,
}


class GameEngine:
    def __init__(
        self,
        room_code: str,
        players: Iterable[Player],
        *,
        start_player_id: str | None = None,
        phase_timeouts: dict[str, int] | None = None,
        rng: random.Random | None = None,
    ):
        self.players = list(players)
        self.rng = rng or random.Random()
        self.phase_timeouts = {**DEFAULT_TIMEOUTS, **(phase_timeouts or {})}
        player_states = [
            PlayerState(
                id=p.id,
                nickname=p.nickname,
                role=p.role,
                is_ai=p.is_ai,
                seat=getattr(p, "seat", idx),
            )
            for idx, p in enumerate(self.players)
        ]
        self.state = GameState(room_code=room_code, players=player_states, phase=Phase.LOBBY)
        self.broadcaster = Broadcaster(self.state, self.players)
        self.start_player_id = start_player_id or player_states[0].id
        self.winner: str | None = None

    def _deadline(self, key: str) -> float:
        return time.time() + self.phase_timeouts[key]

    async def run_one_round(self) -> None:
        logger.info("========== 第 %d 天 ==========", self.state.day_number + 1)
        self.state.phase = Phase.NIGHT_START
        logger.info("天黑 | day=%d", self.state.day_number + 1)
        await self.broadcaster.broadcast(GameEvent(
            type="system_announce",
            payload={"text": "天黑请闭眼"},
        ))

        await run_wolf_kill(
            self.state,
            self.players,
            broadcaster=self.broadcaster,
            deadline_ts=self._deadline("wolf_kill"),
            rng=self.rng,
        )
        await run_seer_check(
            self.state,
            self.players,
            broadcaster=self.broadcaster,
            deadline_ts=self._deadline("seer_check"),
        )
        await run_witch_action(
            self.state,
            self.players,
            broadcaster=self.broadcaster,
            deadline_ts=self._deadline("witch_action"),
        )
        await run_day_announce(
            self.state,
            self.players,
            broadcaster=self.broadcaster,
            deadline_ts=self._deadline("day_announce"),
        )

        # Check if hunter was killed by wolves (not poisoned)
        if self.state.tonight_killed_by_wolves:
            killed_player = self.state.get_player(self.state.tonight_killed_by_wolves)
            if killed_player and killed_player.role == Role.HUNTER:
                self.state.hunter_just_died = True
                self.state.last_death_reason = "wolf"
        await run_hunter_shot(
            self.state,
            self.players,
            broadcaster=self.broadcaster,
            deadline_ts=self._deadline("hunter_shot"),
        )
        self.state.hunter_just_died = False

        if self._resolve_winner():
            return

        alive_ids = [p.id for p in self.state.alive_players()]
        if self.state.day_number == 1 and self.start_player_id in alive_ids:
            start = self.start_player_id
        else:
            start = self.rng.choice(alive_ids) if alive_ids else self.start_player_id
        await run_day_speech(
            self.state,
            self.players,
            broadcaster=self.broadcaster,
            start_player_id=start,
            per_player_timeout=self.phase_timeouts["day_speech"],
        )
        result = await run_day_vote(
            self.state,
            self.players,
            broadcaster=self.broadcaster,
            deadline_ts=self._deadline("day_vote"),
        )
        if result.get("eliminated"):
            eliminated_player = self.state.get_player(result["eliminated"])
            if eliminated_player and eliminated_player.role == Role.HUNTER:
                self.state.hunter_just_died = True
                self.state.last_death_reason = "vote"
            await run_hunter_shot(
                self.state,
                self.players,
                broadcaster=self.broadcaster,
                deadline_ts=self._deadline("hunter_shot"),
            )
            self.state.hunter_just_died = False
        self._resolve_winner()

    def _resolve_winner(self) -> bool:
        self.state.phase = Phase.CHECK_WIN
        alive_players = [{"id": p.id, "nickname": p.nickname, "role": p.role.value, "is_ai": p.is_ai}
                         for p in self.state.alive_players()]
        logger.info("存活玩家 | %s", alive_players)

        winner = check_winner(self.state)
        if winner is None:
            return False
        self.winner = winner.value
        self.state.phase = Phase.GAME_OVER
        logger.info("胜负判定 | winner=%s", winner.value)
        return True

    async def run_until_game_over(self, max_rounds: int = 20) -> None:
        if not self._resolve_winner():
            for _ in range(max_rounds):
                await self.run_one_round()
                if self.state.phase == Phase.GAME_OVER:
                    break
        await self._broadcast_game_over()

    async def _broadcast_game_over(self) -> None:
        logger.info("游戏结束 | winner=%s", self.winner)
        role_snapshot = {p.id: {"nickname": p.nickname, "role": p.role.value, "is_ai": p.is_ai}
                         for p in self.state.players}
        logger.info("最终角色 | %s", role_snapshot)
        await self.broadcaster.broadcast(GameEvent(
            type="game_over",
            payload={
                "winner": self.winner,
                "roles": {p.id: p.role.value for p in self.state.players},
            },
        ))


__all__ = ["GameEngine"]
