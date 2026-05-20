from enum import Enum


class Role(str, Enum):
    WEREWOLF = "werewolf"
    WITCH = "witch"
    SEER = "seer"
    VILLAGER = "villager"
    HUNTER = "hunter"
    IDIOT = "idiot"


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
    HUNTER_SHOT = "hunter_shot"
    CHECK_WIN = "check_win"
    GAME_OVER = "game_over"


class Channel(str, Enum):
    DAY = "day"
    WOLF = "wolf"
    DEAD = "dead"


SIX_PLAYER_ROLES: list[Role] = [
    Role.WEREWOLF, Role.WEREWOLF,
    Role.WITCH, Role.SEER,
    Role.VILLAGER, Role.VILLAGER,
]

NINE_PLAYER_ROLES: list[Role] = [
    Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
    Role.VILLAGER, Role.VILLAGER, Role.VILLAGER,
    Role.SEER, Role.WITCH, Role.HUNTER,
]

TWELVE_PLAYER_ROLES: list[Role] = [
    Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
    Role.SEER, Role.WITCH, Role.HUNTER, Role.IDIOT,
    Role.VILLAGER, Role.VILLAGER, Role.VILLAGER, Role.VILLAGER,
]

WOLF_KILL_TIMEOUT = 45
SEER_CHECK_TIMEOUT = 20
WITCH_ACTION_TIMEOUT = 25
SPEECH_PER_PLAYER_TIMEOUT = 60
DAY_VOTE_TIMEOUT = 30
LAST_WORDS_TIMEOUT = 30
RECONNECT_GRACE_SECONDS = 30
LLM_CALL_TIMEOUT = 30
HUNTER_SHOT_TIMEOUT = 30
