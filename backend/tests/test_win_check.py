from app.game.constants import Role, Phase
from app.game.state import GameState, PlayerState
from app.game.win_check import check_winner, Winner


def _make_state(alive_roles: list[Role]) -> GameState:
    all_roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
                 Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=False, seat=i)
        for i, r in enumerate(all_roles)
    ]
    counts = {r: 0 for r in set(all_roles)}
    for r in alive_roles:
        counts[r] = counts.get(r, 0) + 1
    for p in players:
        p.alive = False
    remaining = dict(counts)
    for p in players:
        if remaining.get(p.role, 0) > 0:
            p.alive = True
            remaining[p.role] -= 1
    return GameState(room_code="R", players=players, phase=Phase.CHECK_WIN)


def test_all_wolves_dead_good_wins():
    s = _make_state([Role.WITCH, Role.SEER, Role.VILLAGER])
    assert check_winner(s) == Winner.GOOD


def test_all_good_dead_wolves_win():
    s = _make_state([Role.WEREWOLF, Role.WEREWOLF])
    assert check_winner(s) == Winner.WEREWOLF


def test_mixed_still_alive_no_winner():
    s = _make_state([Role.WEREWOLF, Role.SEER, Role.VILLAGER])
    assert check_winner(s) is None


def test_wolves_plus_one_good_still_no_winner():
    s = _make_state([Role.WEREWOLF, Role.VILLAGER])
    assert check_winner(s) is None
