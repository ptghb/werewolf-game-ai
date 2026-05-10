from app.players.base import ActionPrompt, ActionResponse, Player


def test_action_prompt_fields():
    p = ActionPrompt(
        action="day_vote",
        options=["p1", "p2"],
        deadline_ts=123.0,
        hint="vote someone out",
    )
    assert p.action == "day_vote"
    assert p.options == ["p1", "p2"]
    assert p.deadline_ts == 123.0
    assert p.hint == "vote someone out"


def test_action_response_fields():
    r = ActionResponse(action="day_vote", target="p1")
    assert r.action == "day_vote"
    assert r.target == "p1"
    assert r.text is None


def test_player_protocol_is_runtime_checkable():
    class Fake:
        id = "p1"
        nickname = "a"
        role = None
        alive = True
        is_ai = False
        async def request(self, prompt): ...
        async def notify(self, event): ...
    assert isinstance(Fake(), Player)
