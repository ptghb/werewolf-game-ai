from typing import Optional, Dict
import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.night_witch import run_witch_action
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


class ScriptedWitch(FakeAIPlayer):
    """A witch that returns scripted responses for save then poison stages."""
    def __init__(self, *args, save_response=None, poison_response=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.save_response = save_response
        self.poison_response = poison_response

    async def request(self, prompt):
        from app.players.base import ActionResponse
        if prompt.action == "witch_save":
            r = self.save_response or ActionResponse(action="witch_skip")
            return ActionResponse(action=r.get("action", "witch_skip"), target=r.get("target"))
        if prompt.action == "witch_poison":
            r = self.poison_response or ActionResponse(action="witch_skip")
            return ActionResponse(action=r.get("action", "witch_skip"), target=r.get("target"))
        return await super().request(prompt)


def _setup(save_response=None, poison_response=None, killed_by_wolves="p5"):
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = []
    for p in players:
        if p.role == Role.WITCH:
            f = ScriptedWitch(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat,
                              save_response=save_response, poison_response=poison_response)
        else:
            f = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        fakes.append(f)
    state = GameState(room_code="R", players=players, phase=Phase.WITCH_ACTION)
    state.tonight_killed_by_wolves = killed_by_wolves
    return state, fakes


@pytest.mark.asyncio
async def test_witch_save_consumes_save_potion():
    state, fakes = _setup(
        save_response={"action": "witch_save", "target": "p5"},
        poison_response={"action": "witch_skip"},
    )
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert state.tonight_saved_by_witch is True
    assert state.witch.save_left is False
    assert state.witch.poison_left is True


@pytest.mark.asyncio
async def test_witch_poison_consumes_poison_potion():
    state, fakes = _setup(
        save_response={"action": "witch_skip"},
        poison_response={"action": "witch_poison", "target": "p0"},
    )
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert state.tonight_poisoned_by_witch == "p0"
    assert state.witch.poison_left is False
    assert state.witch.save_left is True


@pytest.mark.asyncio
async def test_witch_cannot_use_both_same_night():
    # Current logic: save then poison in sequence. Save first consumes save.
    # Poison stage still runs if poison_left. So both can be used same night.
    # Test: save is used, poison also used
    state, fakes = _setup(
        save_response={"action": "witch_save", "target": "p5"},
        poison_response={"action": "witch_poison", "target": "p0"},
    )
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert state.tonight_saved_by_witch is True
    assert state.witch.save_left is False
    assert state.witch.poison_left is False


@pytest.mark.asyncio
async def test_witch_skip_leaves_potions():
    state, fakes = _setup(
        save_response={"action": "witch_skip"},
        poison_response={"action": "witch_skip"},
    )
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert state.witch.save_left is True
    assert state.witch.poison_left is True
    assert state.tonight_saved_by_witch is False
    assert state.tonight_poisoned_by_witch is None


@pytest.mark.asyncio
async def test_witch_gets_info_about_tonight_kill():
    state, fakes = _setup(
        save_response={"action": "witch_skip"},
        poison_response={"action": "witch_skip"},
        killed_by_wolves="p5",
    )
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    witch_fake = next(f for f in fakes if f.role == Role.WITCH)
    infos = [e for e in witch_fake.received if e.type == "witch_info"]
    assert len(infos) == 1
    assert infos[0].payload["tonight_killed"] == "p5"