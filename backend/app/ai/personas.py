from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Persona:
    name: str
    style: str


PERSONAS: list[Persona] = [
    Persona("理性派", "calm, analytical, cites timeline and vote logic"),
    Persona("活泼派", "energetic, uses humor and casual tone"),
    Persona("话少派", "terse, speaks in short declarative sentences"),
    Persona("冲锋派", "aggressive, pushes bold claims early"),
    Persona("和事佬", "diplomatic, avoids commitments, summarizes others"),
    Persona("玄学派", "intuitive, references feelings and impressions"),
    Persona("推理狂", "over-detailed, long chains of suspicion"),
    Persona("摸鱼党", "low-effort speeches, often agrees with last speaker"),
]


def random_persona(seed: Optional[int] = None) -> Persona:
    rng = random.Random(seed)
    return rng.choice(PERSONAS)


__all__ = ["Persona", "PERSONAS", "random_persona"]
