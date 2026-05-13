from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable, Optional

from app.game.constants import Role
from app.game.events import GameEvent


@dataclass
class ActionPrompt:
    action: str
    options: list[str] = field(default_factory=list)
    deadline_ts: float = 0.0
    hint: str = ""


@dataclass
class ActionResponse:
    action: str
    target: Optional[str] = None
    text: Optional[str] = None


@runtime_checkable
class Player(Protocol):
    id: str
    nickname: str
    role: Role
    alive: bool
    is_ai: bool

    async def request(self, prompt: ActionPrompt) -> ActionResponse: ...
    async def notify(self, event: GameEvent) -> None: ...


__all__ = ["ActionPrompt", "ActionResponse", "Player"]
