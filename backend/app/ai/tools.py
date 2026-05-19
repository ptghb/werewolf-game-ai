from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class TargetInput(BaseModel):
    target_id: str = Field(..., description="Player id to target")


class NoInput(BaseModel):
    pass


class SpeakInput(BaseModel):
    text: str = Field(..., description="Your message (<=80 Chinese chars)")


def _noop(**_kwargs):
    return ""


def _mk(name: str, description: str, schema: type[BaseModel]) -> StructuredTool:
    return StructuredTool.from_function(
        func=_noop,
        name=name,
        description=description,
        args_schema=schema,
    )


def tools_for_action(action: str, options: list[str], nickname_map: dict[str, str] | None = None) -> list[StructuredTool]:
    if nickname_map and options:
        display = [f"{nickname_map.get(oid, oid)}({oid})" for oid in options]
        opts_hint = f" Valid targets: {display}."
    else:
        opts_hint = f" Valid target_id: {options}." if options else ""
    if action == "wolf_vote":
        return [_mk("wolf_vote", "Cast your wolf-kill vote." + opts_hint, TargetInput)]
    if action == "seer_check":
        return [
            _mk("seer_check", "Check a player's identity tonight." + opts_hint, TargetInput),
            _mk("seer_skip", "Skip tonight's check.", NoInput),
        ]
    if action == "witch_save":
        return [
            _mk("witch_save", "Use save potion to save the killed player." + opts_hint, TargetInput),
            _mk("witch_skip", "Don't use save potion.", NoInput),
        ]
    if action == "witch_poison":
        return [
            _mk("witch_poison", "Use poison potion on a player." + opts_hint, TargetInput),
            _mk("witch_skip", "Don't use poison potion.", NoInput),
        ]
    if action in ("speech", "speak", "last_words"):
        return [_mk("speak", "Speak aloud during your turn.", SpeakInput)]
    if action in ("day_vote", "day_vote_pk"):
        return [
            _mk("day_vote", "Vote to eliminate a player." + opts_hint, TargetInput),
            _mk("day_abstain", "Abstain from voting.", NoInput),
        ]
    if action == "hunter_shot":
        return [
            _mk("hunter_shot", "Shoot a player and take them down with you." + opts_hint, TargetInput),
            _mk("hunter_skip", "Choose not to shoot.", NoInput),
        ]
    return []


__all__ = ["tools_for_action"]
