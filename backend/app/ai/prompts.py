from __future__ import annotations

from app.ai.personas import Persona
from app.game.constants import Role


ROLE_DESCRIPTIONS: dict[Role, str] = {
    Role.WEREWOLF: "你是狼人。夜间你和狼队友一起决定击杀目标；白天要伪装好人，避免被投出。",
    Role.SEER: "你是预言家（好人阵营）。夜间每晚查验一名玩家的身份；白天要利用信息引导好人投票。",
    Role.WITCH: "你是女巫（好人阵营）。你有救药和毒药各 1 瓶（全局计数），同一夜不能同时使用两瓶。",
    Role.VILLAGER: "你是平民（好人阵营）。你无特殊技能，依靠推理和发言引导投票。",
    Role.HUNTER: "你是猎人（好人阵营）。当你被狼人杀死或被投票放逐时，可以开枪带走任意一名玩家。被女巫毒死不能开枪。",
}


RULES_SUMMARY = """
游戏规则（6 人局）：2 狼人 + 1 女巫 + 1 预言家 + 2 平民。
游戏规则（9 人局）：3 狼人 + 1 女巫 + 1 预言家 + 3 平民 + 1 猎人。
夜间：狼人共刀 → 预言家查验 → 女巫决定救/毒/跳。
白天：公布死讯 → 轮流发言 → 全员投票（平票则 PK，再平无人出局）。
猎人：被狼刀或公投出局时可开枪带走一人；被毒不能开枪。
胜负：所有狼人死 → 好人胜；好人全死 → 狼人胜。
""".strip()


def build_system_prompt(
    role: Role,
    persona: Persona,
    wolf_teammates: list[str],
    nickname_map: dict[str, str] | None = None,
    self_id: str | None = None,
    self_nickname: str | None = None,
) -> str:
    self_line = ""
    if self_id and self_nickname:
        self_line = f"\n你的身份：{self_nickname}({self_id})。"
    teammate_line = ""
    if role == Role.WEREWOLF and wolf_teammates:
        names = [f"{nickname_map.get(tid, tid)}({tid})" if nickname_map else tid for tid in wolf_teammates]
        teammate_line = f"\n你的狼队友：{', '.join(names)}。"
    return (
        f"{RULES_SUMMARY}\n\n"
        f"{ROLE_DESCRIPTIONS[role]}{self_line}{teammate_line}\n\n"
        f"你的人设：{persona.name} — {persona.style}。\n"
        f"发言时严格控制在 80 汉字以内；保持人设一致。"
    )


__all__ = ["build_system_prompt", "ROLE_DESCRIPTIONS", "RULES_SUMMARY"]
