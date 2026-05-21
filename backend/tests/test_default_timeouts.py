from app.game.engine import DEFAULT_TIMEOUTS
from app.players.human import DEFAULT_REQUEST_TIMEOUT


def test_default_phase_timeouts_are_long_enough_for_manual_play():
    assert DEFAULT_TIMEOUTS == {
        "wolf_kill": 90,
        "seer_check": 60,
        "witch_action": 60,
        "day_announce": 45,
        "day_speech": 90,
        "day_vote": 60,
        "hunter_shot": 60,
        "last_words": 60,
    }
    assert DEFAULT_REQUEST_TIMEOUT == 120
