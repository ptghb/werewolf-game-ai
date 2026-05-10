from app.game.constants import Role
from app.game.events import GameEvent
from app.game.state import GameState, PlayerState


def is_visible_to(event: GameEvent, player: PlayerState, state: GameState) -> bool:
    aud = event.audience
    if aud == "all":
        return True
    if aud == "dead":
        return not player.alive
    if aud.startswith("role:"):
        role_name = aud.split(":", 1)[1]
        return player.role.value == role_name
    if aud.startswith("player:"):
        pid = aud.split(":", 1)[1]
        return player.id == pid
    return False


__all__ = ["is_visible_to"]
