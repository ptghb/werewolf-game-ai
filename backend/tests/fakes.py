from __future__ import annotations

from dataclasses import dataclass, field

from app.game.constants import Role
from app.game.events import GameEvent
from app.players.base import ActionPrompt, ActionResponse


@dataclass
class FakeAIPlayer:
    id: str
    nickname: str
    role: Role
    seat: int
    alive: bool = True
    is_ai: bool = True
    scripted: dict[str, str | None] = field(default_factory=dict)
    speech: str = "(silence)"
    received: list[GameEvent] = field(default_factory=list)

    async def request(self, prompt: ActionPrompt) -> ActionResponse:
        if prompt.action in ("speak", "speech", "last_words"):
            return ActionResponse(action=prompt.action, text=self.speech)
        if prompt.action in self.scripted:
            return ActionResponse(action=prompt.action, target=self.scripted[prompt.action])
        if self.scripted:
            # Sub-action scripted (e.g. witch_save when prompt asks witch_action)
            action_name = next(iter(self.scripted))
            return ActionResponse(action=action_name, target=self.scripted[action_name])
        target = prompt.options[0] if prompt.options else None
        return ActionResponse(action=prompt.action, target=target)

    async def notify(self, event: GameEvent) -> None:
        self.received.append(event)
