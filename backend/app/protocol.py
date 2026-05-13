from __future__ import annotations

from typing import Any, Literal, Union, Optional, List, Dict

from pydantic import BaseModel, Field


# Client → Server payloads

class CreateRoomPayload(BaseModel):
    nickname: str
    human_slots: int = 1
    ai_slots: int = 5


class JoinRoomPayload(BaseModel):
    room_code: str
    nickname: str


class StartGamePayload(BaseModel):
    pass


class ChatPayload(BaseModel):
    channel: Literal["day", "wolf", "dead"]
    text: str


class ActionPayload(BaseModel):
    action: str
    target: Optional[str] = None
    text: Optional[str] = None


class AckPayload(BaseModel):
    seq: int


PAYLOAD_MAP = {
    "create_room": CreateRoomPayload,
    "join_room": JoinRoomPayload,
    "start_game": StartGamePayload,
    "chat": ChatPayload,
    "action": ActionPayload,
    "ack": AckPayload,
}


class ClientMessage(BaseModel):
    type: Literal[
        "create_room", "join_room", "start_game", "chat", "action", "ack",
    ]
    payload: Union[Dict[str, Any], CreateRoomPayload, JoinRoomPayload, StartGamePayload, ChatPayload, ActionPayload, AckPayload] = Field(default_factory=dict)
    room: Optional[str] = None
    seq: int = 0

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if isinstance(obj, dict) and "payload" in obj and isinstance(obj["payload"], dict):
            msg_type = obj.get("type")
            payload_cls = PAYLOAD_MAP.get(msg_type)
            if payload_cls is not None:
                obj = {**obj, "payload": payload_cls(**obj["payload"])}
        return super().model_validate(obj, *args, **kwargs)


# Server → Client payloads

class PlayerInfo(BaseModel):
    id: str
    nickname: str
    seat: int
    is_ai: bool
    alive: bool = True
    connected: bool = True


class RoomStatePayload(BaseModel):
    room_code: str
    host_id: str
    players: list[PlayerInfo]


class RoleAssignedPayload(BaseModel):
    role: str
    wolf_teammates: Optional[List[str]] = None


class PhaseChangePayload(BaseModel):
    phase: str
    deadline_ts: Optional[float] = None
    day: Optional[int] = None
    order: Optional[List[str]] = None


class PromptActionPayload(BaseModel):
    action: str
    options: List[str] = Field(default_factory=list)
    deadline_ts: float = 0.0
    hint: Optional[str] = None


class ChatMessagePayload(BaseModel):
    channel: Literal["day", "wolf", "dead"]
    from_id: str = Field(..., alias="from")
    text: str
    last_words: bool = False

    model_config = {"populate_by_name": True}


class SystemAnnouncePayload(BaseModel):
    text: str


class DeathAnnouncePayload(BaseModel):
    dead: List[str]
    reason: str


class VoteTallyPayload(BaseModel):
    votes: Dict[str, Optional[str]]
    round: int = 1


class SeerResultPayload(BaseModel):
    target_id: str
    is_wolf: bool


class WitchInfoPayload(BaseModel):
    tonight_killed: Optional[str]
    save_left: bool
    poison_left: bool


class GameOverPayload(BaseModel):
    winner: str
    roles: Dict[str, str]


class ErrorPayload(BaseModel):
    code: str
    message: str


class ServerMessage(BaseModel):
    type: Literal[
        "room_state", "role_assigned", "phase_change", "prompt_action",
        "chat_message", "system_announce", "death_announce", "vote_tally",
        "seer_result", "witch_info", "game_over", "error",
    ]
    payload: Any
    room: Optional[str] = None
    seq: int = 0


__all__ = [
    "ClientMessage", "ServerMessage",
    "CreateRoomPayload", "JoinRoomPayload", "StartGamePayload",
    "ChatPayload", "ActionPayload", "AckPayload",
    "PlayerInfo", "RoomStatePayload", "RoleAssignedPayload",
    "PhaseChangePayload", "PromptActionPayload", "ChatMessagePayload",
    "SystemAnnouncePayload", "DeathAnnouncePayload", "VoteTallyPayload",
    "SeerResultPayload", "WitchInfoPayload", "GameOverPayload", "ErrorPayload",
]