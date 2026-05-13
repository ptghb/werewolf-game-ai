import pytest

from app.rooms.room_manager import RoomManager


@pytest.mark.asyncio
async def test_create_room_returns_unique_code():
    mgr = RoomManager()
    r1 = await mgr.create_room(host_nickname="alice", human_slots=2, ai_slots=4)
    r2 = await mgr.create_room(host_nickname="bob", human_slots=2, ai_slots=4)
    assert r1.code != r2.code


@pytest.mark.asyncio
async def test_join_room_adds_human_player():
    mgr = RoomManager()
    room = await mgr.create_room(host_nickname="alice", human_slots=2, ai_slots=4)
    pid = await mgr.join_room(room.code, nickname="bob")
    assert pid is not None
    assert any(p.nickname == "bob" for p in room.players)


@pytest.mark.asyncio
async def test_room_fills_ai_slots():
    mgr = RoomManager()
    room = await mgr.create_room(host_nickname="alice", human_slots=1, ai_slots=5)
    assert sum(1 for p in room.players if p.is_ai) == 5
    assert sum(1 for p in room.players if not p.is_ai) == 1


@pytest.mark.asyncio
async def test_join_rejects_unknown_code():
    mgr = RoomManager()
    with pytest.raises(KeyError):
        await mgr.join_room("NOPE", nickname="bob")


@pytest.mark.asyncio
async def test_join_rejects_full_room():
    mgr = RoomManager()
    room = await mgr.create_room(host_nickname="alice", human_slots=1, ai_slots=5)
    with pytest.raises(ValueError):
        await mgr.join_room(room.code, nickname="bob")