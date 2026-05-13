from __future__ import annotations

from app.ai.personas import Persona
from app.game.constants import Role


ROLE_DESCRIPTIONS: dict[Role, str] = {
    Role.WEREWOLF: "你是狼人。夜间你和狼队友一起决定击杀目标；白天要伪装好人，避免被投出。",
    Role.SEER: "你是预言家（好人阵营）。夜间每晚查验一名玩家的身份；白天要利用信息引导好人投票。",
    Role.WITCH: "你是女巫（好人阵营）。你有救药和毒药各 1 瓶（全局计数），同一夜不能同时使用两瓶。",
    Role.VILLAGER: "你是平民（好人阵营）。你无特殊技能，依靠推理和发言引导投票。",
}


RULES_SUMMARY = """
游戏规则：6 人局（3 狼人 + 1 女巫 + 1 预言家 + 1 平民）。
夜间：狼人共刀 → 预言家查验 → 女巫决定救/毒/跳。
白天：公布死讯 → 轮流发言 → 全员投票（平票则 PK，再平无人出局）。
胜负：所有狼人死 → 好人胜；好人（女巫+预言家+平民）全死 → 狼人胜。
""".strip()


def build_system_prompt(
    role: Role,
    persona: Persona,
    wolf_teammates: list[str],
) -> str:
    teammate_line = ""
    if role == Role.WEREWOLF and wolf_teammates:
        teammate_line = f"\n你的狼队友 id：{', '.join(wolf_teammates)}。"
    return (
        f"{RULES_SUMMARY}\n\n"
        f"{ROLE_DESCRIPTIONS[role]}{teammate_line}\n\n"
        f"你的人设：{persona.name} — {persona.style}。\n"
        f"发言时严格控制在 80 汉字以内；保持人设一致。"
    )


__all__ = ["build_system_prompt", "ROLE_DESCRIPTIONS", "RULES_SUMMARY"]
