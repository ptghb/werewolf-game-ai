import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.night_seer import run_seer_check
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


def _setup(seer_target: str | None):
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = []
    for p in players:
        f = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        if p.role == Role.SEER:
            f.scripted = {"seer_check": seer_target}
        fakes.append(f)
    state = GameState(room_code="R", players=players, phase=Phase.SEER_CHECK)
    return state, fakes


@pytest.mark.asyncio
async def test_seer_checks_wolf_gets_true():
    state, fakes = _setup("p0")
    b = Broadcaster(state, fakes)
    await run_seer_check(state, fakes, broadcaster=b, deadline_ts=9999999999)
    seer_fake = next(f for f in fakes if f.role == Role.SEER)
    results = [e for e in seer_fake.received if e.type == "seer_result"]
    assert len(results) == 1
    assert results[0].payload["target_id"] == "p0"
    assert results[0].payload["is_wolf"] is True


@pytest.mark.asyncio
async def test_seer_checks_villager_gets_false():
    state, fakes = _setup("p5")
    b = Broadcaster(state, fakes)
    await run_seer_check(state, fakes, broadcaster=b, deadline_ts=9999999999)
    seer_fake = next(f for f in fakes if f.role == Role.SEER)
    results = [e for e in seer_fake.received if e.type == "seer_result"]
    assert results[0].payload["is_wolf"] is False


@pytest.mark.asyncio
async def test_seer_skip_no_result():
    state, fakes = _setup(None)
    b = Broadcaster(state, fakes)
    await run_seer_check(state, fakes, broadcaster=b, deadline_ts=9999999999)
    seer_fake = next(f for f in fakes if f.role == Role.SEER)
    results = [e for e in seer_fake.received if e.type == "seer_result"]
    assert results == []


@pytest.mark.asyncio
async def test_seer_dead_is_noop():
    state, fakes = _setup("p0")
    seer_player = next(p for p in state.players if p.role == Role.SEER)
    seer_player.alive = False
    b = Broadcaster(state, fakes)
    await run_seer_check(state, fakes, broadcaster=b, deadline_ts=9999999999)
    seer_fake = next(f for f in fakes if f.role == Role.SEER)
    assert not any(e.type == "seer_result" for e in seer_fake.received)
