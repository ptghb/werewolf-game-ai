from __future__ import annotations

from enum import Enum
from typing import Optional

from app.game.constants import Role
from app.game.state import GameState


class Winner(str, Enum):
    GOOD = "good"
    WEREWOLF = "werewolf"


def check_winner(state: GameState) -> Optional[Winner]:
    alive_wolves = len(state.alive_players_by_role(Role.WEREWOLF))
    alive_good = sum(
        1 for p in state.alive_players() if p.role != Role.WEREWOLF
    )
    if alive_wolves == 0:
        return Winner.GOOD
    if alive_good == 0:
        return Winner.WEREWOLF
    return None
