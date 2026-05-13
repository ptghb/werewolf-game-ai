from typing import Optional, Dict
import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.day_vote import run_day_vote
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


def _setup(vote_scripts: Dict[str, Optional[str]], pk_scripts: Optional[Dict[str, Optional[str]]] = None):
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = []
    for p in players:
        f = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat, speech="pk")
        scripts: dict[str, Optional[str]] = {}
        if p.id in vote_scripts:
            scripts["day_vote"] = vote_scripts[p.id]
        if pk_scripts and p.id in pk_scripts:
            scripts["day_vote_pk"] = pk_scripts[p.id]
        f.scripted = scripts
        fakes.append(f)
    return GameState(room_code="R", players=players, phase=Phase.DAY_VOTE), fakes


@pytest.mark.asyncio
async def test_majority_vote_eliminates():
    votes = {"p0": "p5", "p1": "p5", "p2": "p4", "p3": "p5", "p4": "p5", "p5": "p0"}
    state, fakes = _setup(votes)
    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert result["eliminated"] == "p5"
    assert state.get_player("p5").alive is False


@pytest.mark.asyncio
async def test_tie_goes_to_pk_then_resolves():
    votes = {"p0": "p4", "p1": "p4", "p2": "p4",
             "p3": "p5", "p4": "p5", "p5": "p5"}
    pk = {"p0": "p4", "p1": "p4", "p2": "p4",
          "p3": "p5", "p4": "p4", "p5": "p5"}
    state, fakes = _setup(votes, pk)
    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert result["eliminated"] == "p4"
    assert result["pk_used"] is True


@pytest.mark.asyncio
async def test_double_tie_nobody_out():
    votes = {"p0": "p4", "p1": "p4", "p2": "p4",
             "p3": "p5", "p4": "p5", "p5": "p5"}
    pk = dict(votes)
    state, fakes = _setup(votes, pk)
    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert result["eliminated"] is None
    for p in state.players:
        assert p.alive


@pytest.mark.asyncio
async def test_abstain_not_counted():
    votes = {"p0": None, "p1": None, "p2": None,
             "p3": None, "p4": None, "p5": None}
    state, fakes = _setup(votes)
    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert result["eliminated"] is None


@pytest.mark.asyncio
async def test_eliminated_player_gets_last_words():
    votes = {"p0": "p5", "p1": "p5", "p2": "p5",
             "p3": "p5", "p4": "p5", "p5": "p0"}
    state, fakes = _setup(votes)
    p5_fake = next(f for f in fakes if f.id == "p5")
    p5_fake.speech = "farewell"
    b = Broadcaster(state, fakes)
    await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)
    p0_fake = next(f for f in fakes if f.id == "p0")
    chats = [e for e in p0_fake.received if e.type == "chat_message"
             and e.payload.get("from") == "p5"]
    assert any(c.payload.get("text") == "farewell" for c in chats)
