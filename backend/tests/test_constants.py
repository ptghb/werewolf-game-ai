from app.game.constants import Role, Phase, Channel, SIX_PLAYER_ROLES

def test_roles_exist():
    assert Role.WEREWOLF
    assert Role.WITCH
    assert Role.SEER
    assert Role.VILLAGER

def test_six_player_roles_has_three_wolves_one_witch_one_seer_one_villager():
    counts = {r: SIX_PLAYER_ROLES.count(r) for r in set(SIX_PLAYER_ROLES)}
    assert len(SIX_PLAYER_ROLES) == 6
    assert counts[Role.WEREWOLF] == 3
    assert counts[Role.WITCH] == 1
    assert counts[Role.SEER] == 1
    assert counts[Role.VILLAGER] == 1

def test_phase_enum_has_all_phases():
    for name in ["LOBBY", "ROLE_ASSIGN", "NIGHT_START", "WOLF_KILL",
                 "SEER_CHECK", "WITCH_ACTION", "DAY_ANNOUNCE",
                 "DAY_SPEECH", "DAY_VOTE", "CHECK_WIN", "GAME_OVER"]:
        assert hasattr(Phase, name)

def test_channels_exist():
    for c in ["DAY", "WOLF", "DEAD"]:
        assert hasattr(Channel, c)
