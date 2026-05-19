from app.ai.tools import tools_for_action


def test_wolf_vote_tool_has_target_field():
    tools = tools_for_action("wolf_vote", options=["p0", "p1"])
    assert any(t.name == "wolf_vote" for t in tools)
    tool = next(t for t in tools if t.name == "wolf_vote")
    schema = tool.args_schema.model_json_schema()
    assert "target_id" in schema["properties"]


def test_seer_check_has_skip_option():
    tools = tools_for_action("seer_check", options=["p0", "p1"])
    names = {t.name for t in tools}
    assert "seer_check" in names
    assert "seer_skip" in names


def test_witch_save_has_save_and_skip():
    tools = tools_for_action("witch_save", options=["p0"])
    names = {t.name for t in tools}
    assert "witch_save" in names
    assert "witch_skip" in names


def test_witch_poison_has_poison_and_skip():
    tools = tools_for_action("witch_poison", options=["p0", "p1"])
    names = {t.name for t in tools}
    assert "witch_poison" in names
    assert "witch_skip" in names


def test_speech_tool_text_only():
    tools = tools_for_action("speech", options=[])
    assert any(t.name == "speak" for t in tools)
    tool = next(t for t in tools if t.name == "speak")
    schema = tool.args_schema.model_json_schema()
    assert "text" in schema["properties"]


def test_day_vote_tool_and_abstain():
    tools = tools_for_action("day_vote", options=["p0", "p1"])
    names = {t.name for t in tools}
    assert "day_vote" in names
    assert "day_abstain" in names
