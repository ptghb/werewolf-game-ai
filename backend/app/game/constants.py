from enum import Enum


class Role(str, Enum):
    WEREWOLF = "werewolf"
    WITCH = "witch"
    SEER = "seer"
    VILLAGER = "villager"


class Phase(str, Enum):
    LOBBY = "lobby"
    ROLE_ASSIGN = "role_assign"
    NIGHT_START = "night_start"
    WOLF_KILL = "wolf_kill"
    SEER_CHECK = "seer_check"
    WITCH_ACTION = "witch_action"
    DAY_ANNOUNCE = "day_announce"
    DAY_SPEECH = "day_speech"
    DAY_VOTE = "day_vote"
    CHECK_WIN = "check_win"
    GAME_OVER = "game_over"


class Channel(str, Enum):
    DAY = "day"
    WOLF = "wolf"
    DEAD = "dead"


SIX_PLAYER_ROLES: list[Role] = [
    Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
    Role.WITCH, Role.SEER, Role.VILLAGER,
]

WOLF_KILL_TIMEOUT = 45
SEER_CHECK_TIMEOUT = 20
WITCH_ACTION_TIMEOUT = 25
SPEECH_PER_PLAYER_TIMEOUT = 60
DAY_VOTE_TIMEOUT = 30
LAST_WORDS_TIMEOUT = 30
RECONNECT_GRACE_SECONDS = 30
LLM_CALL_TIMEOUT = 30
