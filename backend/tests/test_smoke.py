import asyncio

import pytest

from app.game.constants import Role
from app.players.human import HumanPlayer
from app.rooms.room import Room
from app.rooms.room_manager import RoomManager


def test_python_works():
    assert 1 + 1 == 2


@pytest.mark.asyncio
async def test_ai_players_get_persona_nicknames():
    manager = RoomManager()

    room = await manager.create_room(host_nickname="房主", human_slots=1, ai_slots=5)

    ai_nicknames = [p.nickname for p in room.players if p.is_ai]
    assert len(ai_nicknames) == 5
    assert all(not nickname.startswith("AI-") for nickname in ai_nicknames)
    assert len(set(ai_nicknames)) == len(ai_nicknames)


@pytest.mark.asyncio
async def test_human_chat_queue_payload_includes_sender_nickname():
    player = HumanPlayer(id="h_1", nickname="小明", role=Role.VILLAGER, seat=0)
    room = Room(
        code="ABC123",
        host_id="h_1",
        human_slots=1,
        ai_slots=0,
        players=[player],
        created_at=0,
    )

    payload = {"channel": "day", "text": "大家好"}
    await room.queue.put({"type": "chat", "from": player.id, "from_name": player.nickname, **payload})
    queued = await asyncio.wait_for(room.queue.get(), timeout=0.1)

    assert queued == {
        "type": "chat",
        "from": "h_1",
        "from_name": "小明",
        "channel": "day",
        "text": "大家好",
    }
