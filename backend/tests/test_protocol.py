import pytest
from pydantic import ValidationError

from app.protocol import (
    ClientMessage, ServerMessage,
    CreateRoomPayload, JoinRoomPayload, ActionPayload, ChatPayload, AckPayload,
    PhaseChangePayload, PromptActionPayload, ChatMessagePayload, RoleAssignedPayload,
)


def test_create_room_roundtrip():
    msg = ClientMessage(
        type="create_room",
        payload=CreateRoomPayload(nickname="alice", human_slots=1, ai_slots=5),
        room=None, seq=1,
    )
    data = msg.model_dump()
    assert data["type"] == "create_room"
    parsed = ClientMessage.model_validate(data)
    assert parsed.payload.nickname == "alice"


def test_join_room_requires_code():
    with pytest.raises(ValidationError):
        JoinRoomPayload(nickname="a")


def test_action_payload_allows_optional_fields():
    payload = ActionPayload(action="day_vote", target="p5")
    assert payload.target == "p5"
    assert payload.text is None


def test_server_phase_change_roundtrip():
    msg = ServerMessage(
        type="phase_change",
        payload=PhaseChangePayload(phase="day_vote", deadline_ts=123.0),
        seq=10,
    )
    raw = msg.model_dump_json()
    ServerMessage.model_validate_json(raw)


def test_role_assigned_wolf_includes_teammates():
    payload = RoleAssignedPayload(role="werewolf", wolf_teammates=["p1", "p2"])
    assert payload.wolf_teammates == ["p1", "p2"]


def test_prompt_action_requires_action():
    with pytest.raises(ValidationError):
        PromptActionPayload(options=[], deadline_ts=1.0)
