from __future__ import annotations

import random

from app.game.constants import Role, SIX_PLAYER_ROLES


def assign_roles(n: int, rng: random.Random | None = None) -> list[Role]:
    if n != 6:
        raise ValueError(f"Only 6-player games supported, got {n}")
    rng = rng or random.Random()
    pool = list(SIX_PLAYER_ROLES)
    rng.shuffle(pool)
    return pool


__all__ = ["assign_roles"]
