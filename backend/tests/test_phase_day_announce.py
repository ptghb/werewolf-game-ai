from typing import Optional, Dict
import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.day_announce import run_day_announce
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


def _state(killed: Optional[str], poisoned: Optional[str], saved: bool):
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = [FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat, speech="bye")
             for p in players]
    s = GameState(room_code="R", players=players, phase=Phase.DAY_ANNOUNCE)
    s.tonight_killed_by_wolves = killed
    s.tonight_poisoned_by_witch = poisoned
    s.tonight_saved_by_witch = saved
    return s, fakes


@pytest.mark.asyncio
async def test_wolf_kill_unsaved_dies():
    s, fakes = _state("p5", None, False)
    b = Broadcaster(s, fakes)
    dead = await run_day_announce(s, fakes, broadcaster=b, deadline_ts=9999999999)
    assert dead == ["p5"]
    assert s.get_player("p5").alive is False


@pytest.mark.asyncio
async def test_wolf_kill_saved_nobody_dies():
    s, fakes = _state("p5", None, True)
    b = Broadcaster(s, fakes)
    dead = await run_day_announce(s, fakes, broadcaster=b, deadline_ts=9999999999)
    assert dead == []
    assert s.get_player("p5").alive is True


@pytest.mark.asyncio
async def test_wolf_and_poison_both_die():
    s, fakes = _state("p5", "p0", False)
    b = Broadcaster(s, fakes)
    dead = await run_day_announce(s, fakes, broadcaster=b, deadline_ts=9999999999)
    assert set(dead) == {"p5", "p0"}


@pytest.mark.asyncio
async def test_peaceful_night():
    s, fakes = _state(None, None, False)
    b = Broadcaster(s, fakes)
    dead = await run_day_announce(s, fakes, broadcaster=b, deadline_ts=9999999999)
    assert dead == []


@pytest.mark.asyncio
async def test_revealed_idiot_can_die_at_night():
    s, fakes = _state("p5", None, False)
    player = s.get_player("p5")
    player.role = Role.IDIOT
    player.idiot_revealed = True
    b = Broadcaster(s, fakes)

    dead = await run_day_announce(s, fakes, broadcaster=b, deadline_ts=9999999999)

    assert dead == ["p5"]
    assert s.get_player("p5").alive is False
    p0_fake = next(f for f in fakes if f.id == "p0")
    assert any(
        e.type == "death_announce"
        and e.payload == {"dead": ["p5"], "reason": "night"}
        for e in p0_fake.received
    )


@pytest.mark.asyncio
async def test_night_death_last_words_include_sender_nickname():
    s, fakes = _state("p5", None, False)
    p5_fake = next(f for f in fakes if f.id == "p5")
    p5_fake.speech = "night farewell"
    b = Broadcaster(s, fakes)

    await run_day_announce(s, fakes, broadcaster=b, deadline_ts=9999999999)

    p0_fake = next(f for f in fakes if f.id == "p0")
    chats = [e for e in p0_fake.received if e.type == "chat_message"
             and e.payload.get("from") == "p5"]
    assert any(c.payload.get("from_name") == "n5" for c in chats)


@pytest.mark.asyncio
async def test_night_counters_reset_after_announce():
    s, fakes = _state("p5", None, False)
    b = Broadcaster(s, fakes)
    await run_day_announce(s, fakes, broadcaster=b, deadline_ts=9999999999)
    assert s.tonight_killed_by_wolves is None
    assert s.tonight_poisoned_by_witch is None
    assert s.tonight_saved_by_witch is False
