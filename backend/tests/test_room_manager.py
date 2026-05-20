import pytest

from app.rooms.room_manager import RoomManager


@pytest.mark.asyncio
async def test_create_room_returns_unique_code():
    mgr = RoomManager()
    r1 = await mgr.create_room(host_nickname="alice", mode="6")
    r2 = await mgr.create_room(host_nickname="bob", mode="6")
    assert r1.code != r2.code


@pytest.mark.asyncio
async def test_room_fills_ai_slots():
    mgr = RoomManager()
    room = await mgr.create_room(host_nickname="alice", mode="6")
    assert sum(1 for p in room.players if p.is_ai) == 5
    assert sum(1 for p in room.players if not p.is_ai) == 1


@pytest.mark.asyncio
async def test_create_room_12_mode_fills_eleven_ai_slots():
    mgr = RoomManager()
    room = await mgr.create_room(host_nickname="alice", mode="12")
    assert len(room.players) == 12
    assert sum(1 for p in room.players if p.is_ai) == 11
    assert sum(1 for p in room.players if not p.is_ai) == 1
    assert room.players[0].nickname == "alice"
    assert room.players[0].seat == 0
    assert [p.seat for p in room.players] == list(range(12))


@pytest.mark.asyncio
async def test_join_rejects_unknown_code():
    mgr = RoomManager()
    with pytest.raises(KeyError):
        await mgr.join_room("NOPE", nickname="bob")


@pytest.mark.asyncio
async def test_join_rejects_full_room():
    mgr = RoomManager()
    room = await mgr.create_room(host_nickname="alice", mode="6")
    with pytest.raises(ValueError):
        await mgr.join_room(room.code, nickname="bob")