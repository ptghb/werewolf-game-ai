import asyncio
import pytest

from app.game.constants import Role
from app.game.events import GameEvent
from app.players.base import ActionPrompt
from app.players.human import HumanPlayer


class FakeSocket:
    def __init__(self):
        self.sent = []
    async def send_json(self, data):
        self.sent.append(data)


@pytest.mark.asyncio
async def test_human_notify_sends_via_socket():
    sock = FakeSocket()
    hp = HumanPlayer(id="p1", nickname="A", role=Role.VILLAGER, seat=0, socket=sock)
    await hp.notify(GameEvent(type="system_announce", payload={"text": "天黑"}))
    assert len(sock.sent) == 1
    assert sock.sent[0]["type"] == "system_announce"


@pytest.mark.asyncio
async def test_human_request_resolved_by_deliver_action():
    sock = FakeSocket()
    hp = HumanPlayer(id="p1", nickname="A", role=Role.VILLAGER, seat=0, socket=sock,
                     request_timeout=5)

    async def feed():
        await asyncio.sleep(0.01)
        await hp.deliver_action({"action": "day_vote", "target": "p3"})

    asyncio.create_task(feed())
    resp = await hp.request(ActionPrompt(action="day_vote", options=["p2", "p3"]))
    assert resp.target == "p3"
    # Socket should have received a prompt_action first
    assert any(m["type"] == "prompt_action" for m in sock.sent)


@pytest.mark.asyncio
async def test_human_request_timeout_returns_default():
    sock = FakeSocket()
    hp = HumanPlayer(id="p1", nickname="A", role=Role.VILLAGER, seat=0, socket=sock,
                     request_timeout=0.05)
    resp = await hp.request(ActionPrompt(action="day_vote", options=["p2", "p3"]))
    assert resp.target is None  # abstain on timeout
    assert resp.action == "day_vote"


@pytest.mark.asyncio
async def test_human_disconnect_buffers_events_and_replays_on_attach():
    sock = FakeSocket()
    hp = HumanPlayer(id="p1", nickname="A", role=Role.VILLAGER, seat=0, socket=sock)
    await hp.detach()
    await hp.notify(GameEvent(type="chat_message", payload={"from": "p2", "text": "hi"}))
    assert sock.sent == []  # buffered
    new_sock = FakeSocket()
    await hp.attach(new_sock, last_ack_seq=0)
    # All buffered events should have been replayed
    assert any(m["type"] == "chat_message" for m in new_sock.sent)