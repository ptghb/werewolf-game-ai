from __future__ import annotations

import random

from app.game.constants import Role, SIX_PLAYER_ROLES, NINE_PLAYER_ROLES


def assign_roles(n: int, rng: random.Random | None = None) -> list[Role]:
    if n not in (6, 9):
        raise ValueError(f"Only 6 or 9-player games supported, got {n}")
    rng = rng or random.Random()
    pool = list(NINE_PLAYER_ROLES if n == 9 else SIX_PLAYER_ROLES)
    rng.shuffle(pool)
    return pool


__all__ = ["assign_roles"]
