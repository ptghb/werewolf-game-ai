from typing import Optional, Dict
import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.day_vote import run_day_vote
from app.game.state import GameState, PlayerState
from app.players.base import ActionPrompt, ActionResponse
from tests.fakes import FakeAIPlayer


class TrackingFakeAIPlayer(FakeAIPlayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompts: list[ActionPrompt] = []

    async def request(self, prompt: ActionPrompt) -> ActionResponse:
        self.prompts.append(prompt)
        return await super().request(prompt)


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
    assert any(c.payload.get("from_name") == "n5" for c in chats)


@pytest.mark.asyncio
async def test_idiot_vote_reveal_sets_state_and_event_without_death():
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.IDIOT]
    state = GameState(
        room_code="R",
        players=[
            PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
            for i, r in enumerate(roles)
        ],
        phase=Phase.DAY_VOTE,
    )
    fakes = []
    for p in state.players:
        fake = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat, speech="farewell")
        fake.scripted = {"day_vote": "p5"}
        fakes.append(fake)

    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)

    idiot = state.get_player("p5")
    assert idiot.alive is True
    assert idiot.idiot_revealed is True
    assert result["eliminated"] is None
    assert result["idiot_revealed"] == "p5"

    events = fakes[0].received
    assert any(e.type == "idiot_reveal" and e.payload == {"player_id": "p5"} for e in events)
    assert not any(e.type == "death_announce" and e.payload.get("reason") == "vote" for e in events)
    assert not any(e.type == "chat_message" and e.payload.get("last_words") for e in events)


@pytest.mark.asyncio
async def test_revealed_idiot_cannot_vote_or_be_voted():
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.IDIOT]
    state = GameState(
        room_code="R",
        players=[
            PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
            for i, r in enumerate(roles)
        ],
        phase=Phase.DAY_VOTE,
    )
    state.get_player("p5").idiot_revealed = True
    fakes = []
    for p in state.players:
        fake = TrackingFakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        fake.scripted = {"day_vote": "p5"}
        fakes.append(fake)

    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)

    votes = result["votes"]
    p5_fake = next(f for f in fakes if f.id == "p5")
    assert "p5" not in votes
    assert all(target != "p5" for target in votes.values())
    assert not any(prompt.action == "day_vote" for prompt in p5_fake.prompts)
    assert state.get_player("p5").alive is True


@pytest.mark.asyncio
async def test_revealed_idiot_excluded_from_pk_candidates():
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.IDIOT]
    state = GameState(
        room_code="R",
        players=[
            PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
            for i, r in enumerate(roles)
        ],
        phase=Phase.DAY_VOTE,
    )
    state.get_player("p5").idiot_revealed = True
    vote_scripts = {
        "p0": "p3",
        "p1": "p3",
        "p2": "p4",
        "p3": "p4",
        "p4": "p5",
        "p5": "p5",
    }
    pk_scripts = {
        "p0": "p3",
        "p1": "p3",
        "p2": "p4",
        "p3": "p4",
        "p4": "p3",
        "p5": "p4",
    }
    fakes = []
    for p in state.players:
        fake = TrackingFakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        fake.scripted = {"day_vote": vote_scripts[p.id], "day_vote_pk": pk_scripts[p.id]}
        fakes.append(fake)

    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)

    pk_events = [event for event in fakes[0].received if event.type == "pk_round"]
    assert result["pk_used"] is True
    assert pk_events[-1].payload["candidates"] == ["p3", "p4"]
    assert result["eliminated"] == "p3"
    assert state.get_player("p5").alive is True


@pytest.mark.asyncio
async def test_idiot_reveals_when_eliminated_in_pk_round():
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.IDIOT]
    state = GameState(
        room_code="R",
        players=[
            PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
            for i, r in enumerate(roles)
        ],
        phase=Phase.DAY_VOTE,
    )
    vote_scripts = {
        "p0": "p4",
        "p1": "p4",
        "p2": "p4",
        "p3": "p5",
        "p4": "p5",
        "p5": "p5",
    }
    pk_scripts = {
        "p0": "p5",
        "p1": "p5",
        "p2": "p5",
        "p3": "p5",
        "p4": "p4",
        "p5": "p4",
    }
    fakes = []
    for p in state.players:
        fake = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat, speech="farewell")
        fake.scripted = {"day_vote": vote_scripts[p.id], "day_vote_pk": pk_scripts[p.id]}
        fakes.append(fake)

    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)

    idiot = state.get_player("p5")
    assert result["pk_used"] is True
    assert result["eliminated"] is None
    assert result["idiot_revealed"] == "p5"
    assert idiot.alive is True
    assert idiot.idiot_revealed is True

    events = fakes[0].received
    assert any(e.type == "idiot_reveal" and e.payload == {"player_id": "p5"} for e in events)
    assert not any(e.type == "death_announce" and e.payload.get("reason") == "vote" for e in events)
    assert not any(e.type == "chat_message" and e.payload.get("last_words") for e in events)
