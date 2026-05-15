import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.day_speech import run_day_speech
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


def _setup(speeches: dict[str, str]):
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = []
    for p in players:
        f = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        f.speech = speeches.get(p.id, "(silence)")
        fakes.append(f)
    return GameState(room_code="R", players=players, phase=Phase.DAY_SPEECH), fakes


@pytest.mark.asyncio
async def test_all_alive_speak_in_seat_order_starting_from_start_id():
    speeches = {f"p{i}": f"s{i}" for i in range(6)}
    state, fakes = _setup(speeches)
    b = Broadcaster(state, fakes)
    order = await run_day_speech(state, fakes, broadcaster=b,
                                 start_player_id="p2", per_player_timeout=5)
    assert order == ["p2", "p3", "p4", "p5", "p0", "p1"]


@pytest.mark.asyncio
async def test_dead_players_skipped():
    speeches = {f"p{i}": f"s{i}" for i in range(6)}
    state, fakes = _setup(speeches)
    state.get_player("p3").alive = False
    state.get_player("p5").alive = False
    b = Broadcaster(state, fakes)
    order = await run_day_speech(state, fakes, broadcaster=b,
                                 start_player_id="p2", per_player_timeout=5)
    assert order == ["p2", "p4", "p0", "p1"]


@pytest.mark.asyncio
async def test_dead_start_player_begins_from_next_alive_seat():
    speeches = {f"p{i}": f"s{i}" for i in range(6)}
    state, fakes = _setup(speeches)
    state.get_player("p3").alive = False
    b = Broadcaster(state, fakes)
    order = await run_day_speech(state, fakes, broadcaster=b,
                                 start_player_id="p3", per_player_timeout=5)
    assert order == ["p4", "p5", "p0", "p1", "p2"]


@pytest.mark.asyncio
async def test_empty_speech_skipped_in_broadcast():
    speeches = {"p0": "hello", "p1": "", "p2": "hi"}
    state, fakes = _setup(speeches)
    for p in state.players:
        p.alive = p.id in {"p0", "p1", "p2"}
    b = Broadcaster(state, fakes)
    await run_day_speech(state, fakes, broadcaster=b,
                         start_player_id="p0", per_player_timeout=5)
    some_fake = fakes[0]
    texts = [e.payload.get("text") for e in some_fake.received if e.type == "chat_message"]
    assert "hello" in texts
    assert "hi" in texts
    assert "" not in texts


@pytest.mark.asyncio
async def test_day_speech_includes_sender_nickname():
    state, fakes = _setup({"p0": "hello"})
    for p in state.players:
        p.alive = p.id == "p0"
    b = Broadcaster(state, fakes)

    await run_day_speech(state, fakes, broadcaster=b,
                         start_player_id="p0", per_player_timeout=5)

    chat = next(e for e in fakes[0].received if e.type == "chat_message")
    assert chat.payload["from"] == "p0"
    assert chat.payload["from_name"] == "n0"
