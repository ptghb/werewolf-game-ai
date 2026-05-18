import random

from app.game.assign import assign_roles
from app.game.constants import Role, SIX_PLAYER_ROLES


def test_assign_produces_exact_six_roles():
    rng = random.Random(42)
    roles = assign_roles(6, rng=rng)
    assert len(roles) == 6
    assert sorted(roles) == sorted(SIX_PLAYER_ROLES)


def test_assign_deterministic_under_seed():
    r1 = assign_roles(6, rng=random.Random(1))
    r2 = assign_roles(6, rng=random.Random(1))
    assert r1 == r2


def test_assign_roles_9_players():
    roles = assign_roles(9)
    assert len(roles) == 9
    assert roles.count(Role.WEREWOLF) == 3
    assert roles.count(Role.VILLAGER) == 3
    assert roles.count(Role.SEER) == 1
    assert roles.count(Role.WITCH) == 1
    assert roles.count(Role.HUNTER) == 1


def test_assign_rejects_non_six():
    import pytest
    with pytest.raises(ValueError):
        assign_roles(7)


def test_assign_rejects_invalid():
    import pytest
    with pytest.raises(ValueError):
        assign_roles(5)
