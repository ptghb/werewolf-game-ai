import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Channel, Phase, Role
from app.game.events import GameEvent
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


def _state():
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = [
        FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        for p in players
    ]
    return GameState(room_code="R", players=players, phase=Phase.LOBBY), fakes


@pytest.mark.asyncio
async def test_broadcast_all_goes_to_everyone():
    state, fakes = _state()
    b = Broadcaster(state, fakes)
    await b.broadcast(GameEvent(type="system_announce", payload={"text": "x"}))
    for f in fakes:
        assert len(f.received) == 1


@pytest.mark.asyncio
async def test_broadcast_wolf_channel_only_to_wolves():
    state, fakes = _state()
    b = Broadcaster(state, fakes)
    await b.broadcast(GameEvent(
        type="chat_message", payload={"text": "x"},
        audience="role:werewolf", channel=Channel.WOLF,
    ))
    for p, f in zip(state.players, fakes):
        if p.role == Role.WEREWOLF:
            assert len(f.received) == 1
        else:
            assert len(f.received) == 0


@pytest.mark.asyncio
async def test_broadcast_player_scoped():
    state, fakes = _state()
    b = Broadcaster(state, fakes)
    seer_id = next(p.id for p in state.players if p.role == Role.SEER)
    await b.broadcast(GameEvent(
        type="seer_result", payload={"target_id": "p0", "is_wolf": True},
        audience=f"player:{seer_id}",
    ))
    for p, f in zip(state.players, fakes):
        expected = 1 if p.id == seer_id else 0
        assert len(f.received) == expected
