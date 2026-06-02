import os

import pytest

from app.ai.llm import build_llm
from app.ai.personas import random_persona
from app.game.constants import Role
from app.game.engine import GameEngine
from app.players.ai import AIPlayer


pytestmark = pytest.mark.llm


@pytest.mark.asyncio
async def test_six_real_ai_finish_game():
    if not os.getenv("LLM_API_KEY"):
        pytest.skip("No LLM_API_KEY in env")
    llm = build_llm()
    specs = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        AIPlayer(id=f"ai_{i}", nickname=f"AI-{i}", role=r, seat=i,
                 persona=random_persona(seed=i), llm=llm)
        for i, r in enumerate(specs)
    ]
    engine = GameEngine(
        room_code="LLM", players=players, start_player_id="ai_0",
        phase_timeouts={k: 60 for k in [
            "wolf_kill","seer_check","witch_action",
            "day_announce","day_speech","day_vote","last_words"]},
    )
    await engine.run_until_game_over(max_rounds=8)
    assert engine.winner in {"good", "werewolf"}