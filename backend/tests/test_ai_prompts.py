from app.ai.personas import Persona
from app.ai.prompts import ROLE_DESCRIPTIONS, RULES_SUMMARY, build_system_prompt
from app.game.constants import Role


def test_rules_summary_mentions_12_player_idiot_rules():
    assert "游戏规则（12 人局）" in RULES_SUMMARY
    assert "4 狼人" in RULES_SUMMARY
    assert "1 白痴" in RULES_SUMMARY
    assert "翻牌免死" in RULES_SUMMARY
    assert "不能投票" in RULES_SUMMARY
    assert "不能再被投票" in RULES_SUMMARY
    assert "仍可被杀" in RULES_SUMMARY


def test_idiot_role_prompt_exists():
    description = ROLE_DESCRIPTIONS[Role.IDIOT]
    assert "你是白痴" in description
    assert "好人阵营" in description
    assert "正常发言和投票" in description
    assert "被公投出局" in description
    assert "翻牌免死" in description
    assert "不能投票" in description
    assert "不能再被投票" in description
    assert "仍可被杀" in description

    prompt = build_system_prompt(
        Role.IDIOT,
        Persona("测试人设", "冷静发言"),
        [],
    )
    assert "你是白痴" in prompt
    assert "好人阵营" in prompt
