from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.config import settings
from app.game.constants import LLM_CALL_TIMEOUT


def build_llm(model: str | None = None, temperature: float = 0.8) -> ChatOpenAI:
    return ChatOpenAI(
        model=model or settings.model,
        temperature=temperature,
        api_key=settings.api_key or "dummy",
        base_url=settings.base_url,
        timeout=LLM_CALL_TIMEOUT,
        max_retries=2,
    )


__all__ = ["build_llm"]
