import pytest
from unittest.mock import AsyncMock

from app.game.constants import Role, Phase
from app.game.phases.hunter_shot import run_hunter_shot
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


@pytest.fixture
def state():
    players = [
        PlayerState(id="hunter", nickname="猎人", role=Role.HUNTER, is_ai=True, seat=0, alive=False),
        PlayerState(id="wolf1", nickname="狼1", role=Role.WEREWOLF, is_ai=True, seat=1, alive=True),
        PlayerState(id="villager", nickname="村民", role=Role.VILLAGER, is_ai=True, seat=2, alive=True),
    ]
    gs = GameState(room_code="TEST", players=players, phase=Phase.HUNTER_SHOT)
    gs.hunter_can_shoot = True
    gs.hunter_just_died = True
    gs.last_death_reason = "vote"
    return gs


@pytest.fixture
def hunter_player():
    return FakeAIPlayer(id="hunter", nickname="猎人", role=Role.HUNTER, seat=0, alive=False)


async def test_hunter_shoots_target(state, hunter_player):
    hunter_player.scripted = {"hunter_shot": "wolf1"}
    broadcaster = AsyncMock()
    target = await run_hunter_shot(state, [hunter_player], broadcaster=broadcaster, deadline_ts=999999)
    assert target == "wolf1"
    assert not state.hunter_can_shoot
    assert not state.get_player("wolf1").alive


async def test_hunter_skips(state, hunter_player):
    """Hunter declines to shoot — sub-action 'hunter_skip' with no target."""
    hunter_player.scripted = {"hunter_skip": None}
    broadcaster = AsyncMock()
    target = await run_hunter_shot(state, [hunter_player], broadcaster=broadcaster, deadline_ts=999999)
    assert target is None
    assert not state.hunter_can_shoot
    # All other players should remain alive
    assert state.get_player("wolf1").alive
    assert state.get_player("villager").alive


async def test_hunter_no_shot_if_alive(state):
    """Hunter_just_died is False (hunter is alive) — should return None immediately."""
    state.hunter_just_died = False
    hunter_player = FakeAIPlayer(id="hunter", nickname="猎人", role=Role.HUNTER, seat=0, alive=True)
    broadcaster = AsyncMock()
    target = await run_hunter_shot(state, [hunter_player], broadcaster=broadcaster, deadline_ts=999999)
    assert target is None
    # State should be unchanged
    assert state.hunter_can_shoot is True


async def test_hunter_no_shot_if_cannot_shoot(state):
    """hunter_can_shoot is False — skip immediately."""
    state.hunter_can_shoot = False
    hunter_player = FakeAIPlayer(id="hunter", nickname="猎人", role=Role.HUNTER, seat=0, alive=False)
    broadcaster = AsyncMock()
    target = await run_hunter_shot(state, [hunter_player], broadcaster=broadcaster, deadline_ts=999999)
    assert target is None


async def test_hunter_shoots_self_gets_first_option(state, hunter_player):
    """If the scripted target is not in alive_ids, the first valid option is used."""
    hunter_player.scripted = {"hunter_shot": "hunter"}
    broadcaster = AsyncMock()
    target = await run_hunter_shot(state, [hunter_player], broadcaster=broadcaster, deadline_ts=999999)
    # The hunter is dead so not in alive_ids; FakeAIPlayer falls back to prompt.options[0]
    assert target == "wolf1"
    assert not state.get_player("wolf1").alive
    assert not state.hunter_can_shoot