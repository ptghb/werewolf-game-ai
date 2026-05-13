import pytest

from app.game.constants import Phase, Role
from app.game.engine import GameEngine
from tests.fakes import FakeAIPlayer


@pytest.mark.asyncio
async def test_all_fake_ai_game_runs_to_game_over():
    specs = [
        ("p0", Role.WEREWOLF,
         {"wolf_vote": "p5", "day_vote": "p4", "day_vote_pk": "p4"}),
        ("p1", Role.WEREWOLF,
         {"wolf_vote": "p5", "day_vote": "p4", "day_vote_pk": "p4"}),
        ("p2", Role.WEREWOLF,
         {"wolf_vote": "p5", "day_vote": "p4", "day_vote_pk": "p4"}),
        ("p3", Role.WITCH,
         {"witch_skip": None, "day_vote": "p0", "day_vote_pk": "p0"}),
        ("p4", Role.SEER,
         {"seer_check": "p0", "day_vote": "p0", "day_vote_pk": "p0"}),
        ("p5", Role.VILLAGER,
         {"day_vote": "p0", "day_vote_pk": "p0"}),
    ]
    players = [
        FakeAIPlayer(id=pid, nickname=pid, role=role, seat=idx, scripted=sc, speech="...")
        for idx, (pid, role, sc) in enumerate(specs)
    ]
    engine = GameEngine(
        room_code="IT",
        players=players,
        start_player_id="p0",
        phase_timeouts={k: 1 for k in [
            "wolf_kill", "seer_check", "witch_action",
            "day_announce", "day_speech", "day_vote", "last_words",
        ]},
    )
    await engine.run_until_game_over(max_rounds=10)
    assert engine.state.phase == Phase.GAME_OVER
    assert engine.winner in {"good", "werewolf"}
    for f in players:
        assert any(e.type == "game_over" for e in f.received)


@pytest.mark.asyncio
async def test_witch_save_prevents_night_death():
    specs = [
        ("p0", Role.WEREWOLF, {"wolf_vote": "p5", "day_vote": None}),
        ("p1", Role.WEREWOLF, {"wolf_vote": "p5", "day_vote": None}),
        ("p2", Role.WEREWOLF, {"wolf_vote": "p5", "day_vote": None}),
        ("p3", Role.WITCH, {"witch_save": "p5", "day_vote": None}),
        ("p4", Role.SEER, {"seer_skip": None, "day_vote": None}),
        ("p5", Role.VILLAGER, {"day_vote": None}),
    ]
    players = [
        FakeAIPlayer(id=pid, nickname=pid, role=role, seat=idx, scripted=sc, speech="...")
        for idx, (pid, role, sc) in enumerate(specs)
    ]
    engine = GameEngine(
        room_code="IT2", players=players, start_player_id="p0",
        phase_timeouts={k: 1 for k in [
            "wolf_kill", "seer_check", "witch_action",
            "day_announce", "day_speech", "day_vote", "last_words"]},
    )
    await engine.run_one_round()
    assert engine.state.get_player("p5").alive is True
