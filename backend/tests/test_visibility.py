from app.game.constants import Role, Phase, Channel
from app.game.events import GameEvent
from app.game.state import GameState, PlayerState
from app.game.visibility import is_visible_to


def _mk_state():
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=False, seat=i)
        for i, r in enumerate(roles)
    ]
    return GameState(room_code="R", players=players, phase=Phase.LOBBY), players


def test_all_audience_visible_to_everyone():
    state, ps = _mk_state()
    ev = GameEvent(type="system_announce", payload={"text": "天黑请闭眼"}, audience="all")
    for p in ps:
        assert is_visible_to(ev, p, state)


def test_wolf_channel_only_to_wolves():
    state, ps = _mk_state()
    ev = GameEvent(type="chat_message", payload={"text": "kill p4"},
                   audience="role:werewolf", channel=Channel.WOLF)
    for p in ps:
        if p.role == Role.WEREWOLF:
            assert is_visible_to(ev, p, state)
        else:
            assert not is_visible_to(ev, p, state)


def test_seer_result_only_to_seer():
    state, ps = _mk_state()
    seer = next(p for p in ps if p.role == Role.SEER)
    ev = GameEvent(type="seer_result", payload={"target_id": "p0", "is_wolf": True},
                   audience=f"player:{seer.id}")
    for p in ps:
        assert is_visible_to(ev, p, state) == (p.id == seer.id)


def test_dead_channel_only_to_dead():
    state, ps = _mk_state()
    ps[3].alive = False
    ps[4].alive = False
    ev = GameEvent(type="chat_message", payload={"text": "hi"},
                   audience="dead", channel=Channel.DEAD)
    for p in ps:
        assert is_visible_to(ev, p, state) == (not p.alive)
