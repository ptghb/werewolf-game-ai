from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, Optional, List

from app.game.constants import Role
from app.game.events import GameEvent
from app.players.base import ActionPrompt, ActionResponse


logger = logging.getLogger("werewolf.player.human")


class _SocketLike(Protocol):
    async def send_json(self, data: dict) -> None: ...


DEFAULT_REQUEST_TIMEOUT = 120


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

    async def _log_human_decision(self, prompt: ActionPrompt, resp: ActionResponse) -> None:
        player_info = f"Human[{self.nickname}({self.id})]"
        action = resp.action or prompt.action
        if action in ("speech", "speak", "last_words"):
            logger.info("发言 | %s | text=\"%s\"", player_info, resp.text or "")
        elif action == "wolf_vote":
            logger.info("狼人投票 | %s | target=%s", player_info, resp.target or "无")
        elif action == "seer_check":
            if resp.target:
                logger.info("预言家查验 | %s | target=%s", player_info, resp.target)
            else:
                logger.info("预言家查验 | %s | 跳过", player_info)
        elif action == "witch_save":
            logger.info("女巫救药 | %s | target=%s", player_info, resp.target)
        elif action == "witch_poison":
            logger.info("女巫毒药 | %s | target=%s", player_info, resp.target)
        elif action == "witch_skip":
            logger.info("女巫跳过 | %s", player_info)
        elif action in ("day_vote", "day_vote_pk"):
            logger.info("白天投票 | %s | target=%s", player_info, resp.target or "弃票")
        elif action == "day_abstain":
            logger.info("白天投票 | %s | 弃权", player_info)
        else:
            logger.info("决策 | %s | action=%s | target=%s | text=\"%s\"",
                        player_info, action, resp.target or "", (resp.text or "")[:50])

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

        player_info = f"Human[{self.nickname}({self.id})]"
        logger.info("等待玩家决策 | %s | action=%s | options=%s",
                    player_info, prompt.action, prompt.options)

        try:
            action_dict = await asyncio.wait_for(fut, timeout=self.request_timeout)
        except asyncio.TimeoutError:
            logger.warning("玩家超时 | %s | action=%s | 使用默认回退",
                           player_info, prompt.action)
            resp = self._default_response(prompt)
            await self._log_human_decision(prompt, resp)
            return resp
        finally:
            self._pending = None
            self._pending_action = None

        resp = ActionResponse(
            action=action_dict.get("action", prompt.action),
            target=action_dict.get("target"),
            text=action_dict.get("text"),
        )
        await self._log_human_decision(prompt, resp)
        return resp

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