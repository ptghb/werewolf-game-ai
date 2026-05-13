from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, Optional, List

from app.game.constants import Role
from app.game.events import GameEvent
from app.players.base import ActionPrompt, ActionResponse


class _SocketLike(Protocol):
    async def send_json(self, data: dict) -> None: ...


DEFAULT_REQUEST_TIMEOUT = 60


@dataclass
class _Buffered:
    seq: int
    envelope: dict


@dataclass
class HumanPlayer:
    id: str
    nickname: str
    role: Role
    seat: int
    socket: Optional[_SocketLike] = None
    alive: bool = True
    is_ai: bool = False
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT
    _seq: int = 0
    _buffer: List[_Buffered] = field(default_factory=list)
    _pending: Optional[asyncio.Future] = None
    _pending_action: Optional[str] = None

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    async def _send(self, envelope: dict) -> None:
        self._buffer.append(_Buffered(seq=envelope["seq"], envelope=envelope))
        if self.socket is not None:
            try:
                await self.socket.send_json(envelope)
            except Exception:
                self.socket = None

    async def notify(self, event: GameEvent) -> None:
        envelope = {
            "type": event.type,
            "payload": event.payload,
            "seq": self._next_seq(),
        }
        await self._send(envelope)

    async def request(self, prompt: ActionPrompt) -> ActionResponse:
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending = fut
        self._pending_action = prompt.action
        envelope = {
            "type": "prompt_action",
            "payload": {
                "action": prompt.action,
                "options": prompt.options,
                "deadline_ts": prompt.deadline_ts or (time.time() + self.request_timeout),
                "hint": prompt.hint,
            },
            "seq": self._next_seq(),
        }
        await self._send(envelope)
        try:
            action_dict = await asyncio.wait_for(fut, timeout=self.request_timeout)
        except asyncio.TimeoutError:
            return self._default_response(prompt)
        finally:
            self._pending = None
            self._pending_action = None
        return ActionResponse(
            action=action_dict.get("action", prompt.action),
            target=action_dict.get("target"),
            text=action_dict.get("text"),
        )

    def _default_response(self, prompt: ActionPrompt) -> ActionResponse:
        if prompt.action in ("speech", "speak", "last_words"):
            return ActionResponse(action=prompt.action, text="")
        if prompt.action in ("seer_check",):
            return ActionResponse(action="seer_skip")
        if prompt.action in ("witch_action",):
            return ActionResponse(action="witch_skip")
        return ActionResponse(action=prompt.action, target=None)

    async def deliver_action(self, action: Dict[str, Any]) -> None:
        fut = self._pending
        if fut is not None and not fut.done():
            fut.set_result(action)

    async def detach(self) -> None:
        self.socket = None

    async def attach(self, socket: _SocketLike, last_ack_seq: int) -> None:
        self.socket = socket
        for item in self._buffer:
            if item.seq > last_ack_seq:
                try:
                    await socket.send_json(item.envelope)
                except Exception:
                    self.socket = None
                    return

    def prune_acked(self, ack_seq: int) -> None:
        self._buffer = [b for b in self._buffer if b.seq > ack_seq]