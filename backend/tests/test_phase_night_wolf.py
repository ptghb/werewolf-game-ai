import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.night_wolf import run_wolf_kill
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


def _setup(wolf_targets: list[str | None]):
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = []
    wolf_i = 0
    for p in players:
        f = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        if p.role == Role.WEREWOLF:
            f.scripted = {"wolf_vote": wolf_targets[wolf_i]}
            wolf_i += 1
        fakes.append(f)
    state = GameState(room_code="R", players=players, phase=Phase.WOLF_KILL)
    return state, fakes


@pytest.mark.asyncio
async def test_wolf_majority_picks_target():
    state, fakes = _setup(["p5", "p5", "p4"])
    b = Broadcaster(state, fakes)
    target = await run_wolf_kill(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert target == "p5"
    assert state.tonight_killed_by_wolves == "p5"


@pytest.mark.asyncio
async def test_wolf_tie_picks_one_of_tied():
    state, fakes = _setup(["p5", "p4", None])
    b = Broadcaster(state, fakes)
    target = await run_wolf_kill(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert target in {"p4", "p5"}


@pytest.mark.asyncio
async def test_wolf_all_abstain_no_kill():
    state, fakes = _setup([None, None, None])
    b = Broadcaster(state, fakes)
    target = await run_wolf_kill(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert target is None
    assert state.tonight_killed_by_wolves is None
