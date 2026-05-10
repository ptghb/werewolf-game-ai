from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class VoteResult:
    kind: Literal["winner", "tie", "no_vote"]
    winner: str | None = None
    tied_candidates: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)


def tally_votes(votes: dict[str, str | None]) -> VoteResult:
    counts = Counter(t for t in votes.values() if t is not None)
    if not counts:
        return VoteResult(kind="no_vote", counts={})
    top = counts.most_common()
    max_n = top[0][1]
    leaders = [c for c, n in top if n == max_n]
    if len(leaders) == 1:
        return VoteResult(kind="winner", winner=leaders[0], counts=dict(counts))
    return VoteResult(kind="tie", tied_candidates=leaders, counts=dict(counts))


__all__ = ["tally_votes", "VoteResult"]
