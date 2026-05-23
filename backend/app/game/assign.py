from __future__ import annotations

import random

from app.game.constants import Role, SIX_PLAYER_ROLES, NINE_PLAYER_ROLES, TWELVE_PLAYER_ROLES


ROLE_POOLS = {
    6: SIX_PLAYER_ROLES,
    9: NINE_PLAYER_ROLES,
    12: TWELVE_PLAYER_ROLES,
}


def assign_roles(n: int, *, reserved_role: Role | None = None, rng: random.Random | None = None) -> list[Role]:
    if n not in ROLE_POOLS:
        raise ValueError(f"Only 6, 9, or 12-player games supported, got {n}")
    rng = rng or random.Random()
    pool = list(ROLE_POOLS[n])
    if reserved_role is not None and reserved_role in pool:
        pool.remove(reserved_role)
        rng.shuffle(pool)
        return [reserved_role] + pool
    rng.shuffle(pool)
    return pool


__all__ = ["assign_roles"]
