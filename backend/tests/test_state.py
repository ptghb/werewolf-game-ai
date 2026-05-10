from app.game.constants import Role, Phase
from app.game.state import GameState, PlayerState, WitchPotions


def test_player_state_defaults():
    p = PlayerState(id="p1", nickname="Alice", role=Role.VILLAGER, is_ai=False, seat=0)
    assert p.alive is True
    assert p.used_last_words is False


def test_witch_potions_defaults():
    w = WitchPotions()
    assert w.save_left is True
    assert w.poison_left is True


def test_game_state_alive_and_by_role():
    ps = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=False, seat=i)
        for i, r in enumerate([Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
                               Role.WITCH, Role.SEER, Role.VILLAGER])
    ]
    gs = GameState(room_code="ABC123", players=ps, phase=Phase.LOBBY)
    assert len(gs.alive_players()) == 6
    assert [p.id for p in gs.players_by_role(Role.WEREWOLF)] == ["p0", "p1", "p2"]
    ps[0].alive = False
    assert len(gs.alive_players()) == 5
    assert len(gs.alive_players_by_role(Role.WEREWOLF)) == 2


def test_game_state_get_by_id():
    ps = [PlayerState(id="p1", nickname="a", role=Role.VILLAGER, is_ai=False, seat=0)]
    gs = GameState(room_code="R", players=ps, phase=Phase.LOBBY)
    assert gs.get_player("p1") is ps[0]
    assert gs.get_player("missing") is None
