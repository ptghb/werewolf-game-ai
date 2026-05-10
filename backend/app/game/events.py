from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.game.constants import Channel


@dataclass
class GameEvent:
    """Internal canonical event. Broadcaster decides who sees it."""
    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    audience: str = "all"
    channel: Channel | None = None
