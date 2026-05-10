import pytest

from app.game.constants import Role
from app.game.events import GameEvent
from app.players.base import ActionPrompt, Player
from tests.fakes import FakeAIPlayer


@pytest.mark.asyncio
async def test_fake_ai_returns_scripted_response():
    fake = FakeAIPlayer(
        id="p1", nickname="a", role=Role.VILLAGER, seat=0,
        scripted={"day_vote": "p2"},
    )
    assert isinstance(fake, Player)
    resp = await fake.request(ActionPrompt(action="day_vote", options=["p2", "p3"]))
    assert resp.target == "p2"


@pytest.mark.asyncio
async def test_fake_ai_defaults_to_first_option():
    fake = FakeAIPlayer(id="p1", nickname="a", role=Role.VILLAGER, seat=0)
    resp = await fake.request(ActionPrompt(action="day_vote", options=["p2", "p3"]))
    assert resp.target == "p2"


@pytest.mark.asyncio
async def test_fake_ai_records_notifications():
    fake = FakeAIPlayer(id="p1", nickname="a", role=Role.VILLAGER, seat=0)
    await fake.notify(GameEvent(type="system_announce", payload={"text": "x"}))
    assert len(fake.received) == 1
    assert fake.received[0].type == "system_announce"
