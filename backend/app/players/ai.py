from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.personas import Persona, random_persona
from app.ai.prompts import build_system_prompt
from app.ai.tools import tools_for_action
from app.game.constants import LLM_CALL_TIMEOUT, Role
from app.game.events import GameEvent
from app.players.base import ActionPrompt, ActionResponse


logger = logging.getLogger("werewolf.player.ai")


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

    def _memory_text(self, nickname_map: dict[str, str]) -> str:
        def _replace_ids(val: object) -> object:
            if isinstance(val, str) and val in nickname_map:
                return f"{nickname_map[val]}({val})"
            if isinstance(val, list):
                return [_replace_ids(v) for v in val]
            if isinstance(val, dict):
                return {k: _replace_ids(v) for k, v in val.items()}
            return val

        lines = []
        for event in self.memory[-40:]:
            cleaned = _replace_ids(event.payload)
            lines.append(f"[{event.type}] {cleaned}")
        return "\n".join(lines) or "(no prior events)"

    async def _single_llm_call(self, prompt: ActionPrompt) -> ActionResponse | None:
        if self.llm is None:
            return None
        tools = tools_for_action(prompt.action, prompt.options, prompt.nickname_map)
        llm = self.llm.bind_tools(tools) if tools else self.llm
        sys_prompt = build_system_prompt(self.role, self.persona, self.wolf_teammates, prompt.nickname_map, self.id, self.nickname)
        options_display = [f"{prompt.nickname_map.get(oid, oid)}({oid})" for oid in prompt.options]
        user_msg = (
            f"当前阶段：{prompt.action}\n"
            f"可选目标：{options_display}\n"
            f"提示：{prompt.hint}\n\n"
            f"历史事件：\n{self._memory_text(prompt.nickname_map)}\n\n"
            f"请通过 function calling 作出决策。"
            f"target_id 参数请填入玩家的 id（括号内的部分）。"
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
        if prompt.action == "hunter_shot":
            if resp.action == "hunter_skip":
                return True
            return resp.target in prompt.options
        if prompt.options and resp.target not in prompt.options:
            return False
        return True

    async def _log_decision(self, prompt: ActionPrompt, resp: ActionResponse) -> None:
        player_info = f"AI[{self.nickname}({self.id})]"
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
        elif action == "day_vote":
            logger.info("白天投票 | %s | target=%s", player_info, resp.target or "弃票")
        elif action == "day_abstain":
            logger.info("白天投票 | %s | 弃权", player_info)
        elif action == "day_vote_pk":
            logger.info("PK投票 | %s | target=%s", player_info, resp.target or "弃票")
        elif action == "hunter_shot":
            logger.info("猎人开枪 | %s | target=%s", player_info, resp.target or "跳过")
        elif action == "hunter_skip":
            logger.info("猎人放弃开枪 | %s", player_info)
        else:
            logger.info("决策 | %s | action=%s | target=%s | text=\"%s\"",
                        player_info, action, resp.target or "", (resp.text or "")[:50])

    async def request(self, prompt: ActionPrompt) -> ActionResponse:
        player_info = f"AI[{self.nickname}({self.id})]"
        logger.info("收到决策请求 | %s | action=%s | options=%s | hint=%s",
                    player_info, prompt.action, prompt.options, prompt.hint)

        for attempt in range(MAX_LLM_RETRIES + 1):
            resp = await self._single_llm_call(prompt)
            valid = self._is_valid(prompt, resp)
            logger.debug("LLM调用 | %s | attempt=%d | valid=%s | resp=%s",
                         player_info, attempt + 1, valid, resp)
            if valid:
                await self._log_decision(prompt, resp)
                return resp

        logger.warning("LLM调用全部失败 | %s | action=%s | 使用默认回退", player_info, prompt.action)

        if prompt.action in ("speech", "speak", "last_words"):
            resp = ActionResponse(action=prompt.action, text="(沉默)")
            await self._log_decision(prompt, resp)
            return resp
        if prompt.action == "seer_check":
            resp = ActionResponse(action="seer_skip")
            await self._log_decision(prompt, resp)
            return resp
        if prompt.action == "witch_action":
            resp = ActionResponse(action="witch_skip")
            await self._log_decision(prompt, resp)
            return resp
        if prompt.action == "day_vote":
            resp = ActionResponse(action="day_abstain")
            await self._log_decision(prompt, resp)
            return resp
        if prompt.action == "hunter_shot":
            resp = ActionResponse(action="hunter_skip")
            await self._log_decision(prompt, resp)
            return resp
        resp = ActionResponse(action=prompt.action, target=self._default_target(prompt.options))
        await self._log_decision(prompt, resp)
        return resp


__all__ = ["AIPlayer"]
