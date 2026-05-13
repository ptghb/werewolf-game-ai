import pytest

from app.game.constants import Phase, Role
from app.game.engine import GameEngine
from tests.fakes import FakeAIPlayer


def _make_players():
    specs = [
        ("p0", Role.WEREWOLF, {"wolf_vote": "p5"}),
        ("p1", Role.WEREWOLF, {"wolf_vote": "p5"}),
        ("p2", Role.WEREWOLF, {"wolf_vote": "p5"}),
        ("p3", Role.WITCH, {"witch_skip": None}),
        ("p4", Role.SEER, {"seer_skip": None}),
        ("p5", Role.VILLAGER, {}),
    ]
    return [
        FakeAIPlayer(id=i, nickname=i, role=r, seat=idx, scripted=sc, speech="...")
        for idx, (i, r, sc) in enumerate(specs)
    ]


@pytest.mark.asyncio
async def test_single_night_day_cycle_transitions_phases_in_order():
    players = _make_players()
    for f in players:
        f.scripted["day_vote"] = "p0"
    engine = GameEngine(room_code="R", players=players, start_player_id="p0",
                        phase_timeouts={"wolf_kill": 1, "seer_check": 1, "witch_action": 1,
                                        "day_announce": 1, "day_speech": 1, "day_vote": 1,
                                        "last_words": 1})
    await engine.run_one_round()
    assert engine.state.phase in (Phase.CHECK_WIN, Phase.GAME_OVER, Phase.DAY_VOTE)
    assert engine.state.get_player("p5").alive is False
    assert engine.state.get_player("p0").alive is False


@pytest.mark.asyncio
async def test_game_ends_when_all_wolves_dead():
    players = _make_players()
    engine = GameEngine(room_code="R", players=players, start_player_id="p0",
                        phase_timeouts={k: 1 for k in [
                            "wolf_kill", "seer_check", "witch_action",
                            "day_announce", "day_speech", "day_vote", "last_words"]})
    for pid in ("p0", "p1", "p2"):
        engine.state.get_player(pid).alive = False
    await engine.run_until_game_over()
    assert engine.state.phase == Phase.GAME_OVER
    assert engine.winner == "good"


@pytest.mark.asyncio
async def test_game_ends_when_all_good_dead():
    players = _make_players()
    engine = GameEngine(room_code="R", players=players, start_player_id="p0",
                        phase_timeouts={k: 1 for k in [
                            "wolf_kill", "seer_check", "witch_action",
                            "day_announce", "day_speech", "day_vote", "last_words"]})
    for pid in ("p3", "p4", "p5"):
        engine.state.get_player(pid).alive = False
    await engine.run_until_game_over()
    assert engine.state.phase == Phase.GAME_OVER
    assert engine.winner == "werewolf"
