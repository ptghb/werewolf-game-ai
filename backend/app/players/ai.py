from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.personas import Persona, random_persona
from app.ai.prompts import build_system_prompt
from app.ai.tools import tools_for_action
from app.game.constants import LLM_CALL_TIMEOUT, Role
from app.game.events import GameEvent
from app.players.base import ActionPrompt, ActionResponse


MAX_LLM_RETRIES = 2


@dataclass
class AIPlayer:
    id: str
    nickname: str
    role: Role
    seat: int
    persona: Persona = field(default_factory=random_persona)
    wolf_teammates: list[str] = field(default_factory=list)
    llm: object | None = None
    memory: list[GameEvent] = field(default_factory=list)
    alive: bool = True
    is_ai: bool = True
    llm_timeout: float = LLM_CALL_TIMEOUT

    def _default_target(self, options: list[str]) -> str | None:
        return random.choice(options) if options else None

    async def notify(self, event: GameEvent) -> None:
        self.memory.append(event)

    def _memory_text(self) -> str:
        lines = [f"[{event.type}] {event.payload}" for event in self.memory[-40:]]
        return "\n".join(lines) or "(no prior events)"

    async def _single_llm_call(self, prompt: ActionPrompt) -> ActionResponse | None:
        if self.llm is None:
            return None
        tools = tools_for_action(prompt.action, prompt.options)
        llm = self.llm.bind_tools(tools) if tools else self.llm
        sys_prompt = build_system_prompt(self.role, self.persona, self.wolf_teammates)
        user_msg = (
            f"当前阶段：{prompt.action}\n"
            f"可选目标 id：{prompt.options}\n"
            f"提示：{prompt.hint}\n\n"
            f"历史事件：\n{self._memory_text()}\n\n"
            f"请通过 function calling 作出决策。"
        )
        messages = [SystemMessage(content=sys_prompt), HumanMessage(content=user_msg)]
        try:
            resp = await asyncio.wait_for(llm.ainvoke(messages), timeout=self.llm_timeout)
        except Exception:
            return None

        tool_calls = getattr(resp, "tool_calls", None) or []
        if not tool_calls:
            text = (getattr(resp, "content", "") or "").strip()
            return ActionResponse(action=prompt.action, text=text or None)

        call = tool_calls[0]
        name = call.get("name")
        args = call.get("args", {})
        if name in ("seer_skip", "witch_skip", "day_abstain"):
            return ActionResponse(action=name)
        if name == "speak":
            return ActionResponse(action=prompt.action, text=(args.get("text") or "").strip())
        target = args.get("target_id")
        if name in ("witch_save", "witch_poison"):
            return ActionResponse(action=name, target=target)
        return ActionResponse(action=name or prompt.action, target=target)

    def _is_valid(self, prompt: ActionPrompt, resp: ActionResponse | None) -> bool:
        if resp is None:
            return False
        if prompt.action in ("speech", "speak", "last_words"):
            return resp.text is not None
        if resp.action in ("seer_skip", "witch_skip", "day_abstain"):
            return True
        if prompt.action == "witch_action":
            if resp.action == "witch_save":
                return resp.target is not None
            if resp.action == "witch_poison":
                return resp.target in prompt.options
            return False
        if prompt.options and resp.target not in prompt.options:
            return False
        return True

    async def request(self, prompt: ActionPrompt) -> ActionResponse:
        for _ in range(MAX_LLM_RETRIES + 1):
            resp = await self._single_llm_call(prompt)
            if self._is_valid(prompt, resp):
                return resp

        if prompt.action in ("speech", "speak", "last_words"):
            return ActionResponse(action=prompt.action, text="(沉默)")
        if prompt.action == "seer_check":
            return ActionResponse(action="seer_skip")
        if prompt.action == "witch_action":
            return ActionResponse(action="witch_skip")
        if prompt.action == "day_vote":
            return ActionResponse(action="day_abstain")
        return ActionResponse(action=prompt.action, target=self._default_target(prompt.options))


__all__ = ["AIPlayer"]
