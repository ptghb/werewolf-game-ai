from __future__ import annotations

from dataclasses import dataclass, field

from app.game.constants import Role, Phase


@dataclass
class WitchPotions:
    save_left: bool = True
    poison_left: bool = True


@dataclass
class PlayerState:
    id: str
    nickname: str
    role: Role
    is_ai: bool
    seat: int
    alive: bool = True
    used_last_words: bool = False
    connected: bool = True


@dataclass
class GameState:
    room_code: str
    players: list[PlayerState]
    phase: Phase
    host_id: str = ""
    day_number: int = 0
    tonight_killed_by_wolves: str | None = None
    tonight_poisoned_by_witch: str | None = None
    tonight_saved_by_witch: bool = False
    witch: WitchPotions = field(default_factory=WitchPotions)
    last_vote_tally: dict[str, str] = field(default_factory=dict)
    hunter_can_shoot: bool = True
    hunter_just_died: bool = False
    last_death_reason: str | None = None

    def get_player(self, pid: str) -> PlayerState | None:
        for p in self.players:
            if p.id == pid:
                return p
        return None

    def alive_players(self) -> list[PlayerState]:
        return [p for p in self.players if p.alive]

    def players_by_role(self, role: Role) -> list[PlayerState]:
        return [p for p in self.players if p.role == role]

    def alive_players_by_role(self, role: Role) -> list[PlayerState]:
        return [p for p in self.players if p.alive and p.role == role]
