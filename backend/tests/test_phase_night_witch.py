import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.night_witch import run_witch_action
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


def _setup(scripted_action: str, target: str | None, killed_by_wolves: str | None = "p5"):
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = []
    for p in players:
        f = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        if p.role == Role.WITCH:
            f.scripted = {scripted_action: target}
        fakes.append(f)
    state = GameState(room_code="R", players=players, phase=Phase.WITCH_ACTION)
    state.tonight_killed_by_wolves = killed_by_wolves
    return state, fakes


@pytest.mark.asyncio
async def test_witch_save_consumes_save_potion():
    state, fakes = _setup("witch_save", "p5")
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert state.tonight_saved_by_witch is True
    assert state.witch.save_left is False
    assert state.witch.poison_left is True


@pytest.mark.asyncio
async def test_witch_poison_consumes_poison_potion():
    state, fakes = _setup("witch_poison", "p0")
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert state.tonight_poisoned_by_witch == "p0"
    assert state.witch.poison_left is False
    assert state.witch.save_left is True


@pytest.mark.asyncio
async def test_witch_cannot_use_both_same_night():
    state, fakes = _setup("witch_save", "p5")
    witch_fake = next(f for f in fakes if f.role == Role.WITCH)
    witch_fake.scripted = {"witch_save": "p5", "witch_poison": "p0"}
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert state.tonight_saved_by_witch is True
    assert state.tonight_poisoned_by_witch is None


@pytest.mark.asyncio
async def test_witch_skip_leaves_potions():
    state, fakes = _setup("witch_skip", None)
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert state.witch.save_left is True
    assert state.witch.poison_left is True
    assert state.tonight_saved_by_witch is False
    assert state.tonight_poisoned_by_witch is None


@pytest.mark.asyncio
async def test_witch_gets_info_about_tonight_kill():
    state, fakes = _setup("witch_skip", None, killed_by_wolves="p5")
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    witch_fake = next(f for f in fakes if f.role == Role.WITCH)
    infos = [e for e in witch_fake.received if e.type == "witch_info"]
    assert len(infos) == 1
    assert infos[0].payload["tonight_killed"] == "p5"
