import pytest
from unittest.mock import AsyncMock, MagicMock

from app.ai.personas import Persona
from app.game.constants import Role
from app.game.events import GameEvent
from app.players.ai import AIPlayer
from app.players.base import ActionPrompt


def _make_ai(stub_response, persona_style="calm"):
    stub_llm = MagicMock()
    stub_llm.bind_tools.return_value = stub_llm
    stub_llm.ainvoke = AsyncMock(return_value=stub_response)
    return AIPlayer(
        id="p0", nickname="AI-0", role=Role.WEREWOLF, seat=0,
        persona=Persona(name="X", style=persona_style),
        llm=stub_llm,
    ), stub_llm


@pytest.mark.asyncio
async def test_ai_parses_tool_call_to_response():
    from langchain_core.messages import AIMessage
    resp = AIMessage(content="", tool_calls=[{
        "id": "c1", "name": "wolf_vote", "args": {"target_id": "p5"},
    }])
    ai, _ = _make_ai(resp)
    out = await ai.request(ActionPrompt(action="wolf_vote", options=["p4", "p5"]))
    assert out.action == "wolf_vote"
    assert out.target == "p5"


@pytest.mark.asyncio
async def test_ai_speech_returns_text():
    from langchain_core.messages import AIMessage
    resp = AIMessage(content="", tool_calls=[{
        "id": "c1", "name": "speak", "args": {"text": "我觉得 p5 是狼"},
    }])
    ai, _ = _make_ai(resp)
    out = await ai.request(ActionPrompt(action="speech", options=[]))
    assert out.text == "我觉得 p5 是狼"


@pytest.mark.asyncio
async def test_ai_falls_back_to_default_on_invalid_target():
    from langchain_core.messages import AIMessage
    resp = AIMessage(content="", tool_calls=[{
        "id": "c1", "name": "wolf_vote", "args": {"target_id": "nonexistent"},
    }])
    ai, _ = _make_ai(resp)
    out = await ai.request(ActionPrompt(action="wolf_vote", options=["p4", "p5"]))
    assert out.target in {"p4", "p5"}


@pytest.mark.asyncio
async def test_ai_timeout_falls_back():
    import asyncio
    stub_llm = MagicMock()
    stub_llm.bind_tools.return_value = stub_llm

    async def hang(*_args, **_kwargs):
        await asyncio.sleep(10)

    stub_llm.ainvoke = hang
    ai = AIPlayer(id="p0", nickname="AI-0", role=Role.WEREWOLF, seat=0,
                  persona=Persona(name="X", style="calm"),
                  llm=stub_llm, llm_timeout=0.05)
    out = await ai.request(ActionPrompt(action="wolf_vote", options=["p4", "p5"]))
    assert out.target in {"p4", "p5"}


@pytest.mark.asyncio
async def test_ai_notify_appends_to_memory():
    from langchain_core.messages import AIMessage
    resp = AIMessage(content="", tool_calls=[])
    ai, _ = _make_ai(resp)
    await ai.notify(GameEvent(type="system_announce", payload={"text": "天黑"}))
    assert len(ai.memory) == 1
