from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.auth import get_current_user
from app.database.models import Llmtoken, User
from app.database.schemas import LlmtokenCreate, LlmtokenResponse, LlmtokenUpdate
from app.database.session import get_session
from app.game.constants import LLM_CALL_TIMEOUT

logger = logging.getLogger("werewolf.llm_tokens")

router = APIRouter(prefix="/api/llm-tokens", tags=["llm-tokens"])


@router.get("")
async def list_tokens(
    user_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
) -> list[LlmtokenResponse]:
    result = await session.execute(
        select(Llmtoken)
        .where(Llmtoken.user_id == user_id, Llmtoken.del_flag == 0)
        .order_by(Llmtoken.id.desc())
    )
    tokens = result.scalars().all()
    return [
        LlmtokenResponse(
            id=t.id,
            base_url=t.base_url,
            api_key=t.api_key,
            model=t.model,
            enable=t.enable,
            user_id=t.user_id,
            created_at=t.created_at.isoformat() if t.created_at else None,
            updated_at=t.updated_at.isoformat() if t.updated_at else None,
        )
        for t in tokens
    ]


@router.post("", status_code=201)
async def create_token(
    body: LlmtokenCreate,
    user_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
) -> LlmtokenResponse:
    token = Llmtoken(
        base_url=body.base_url,
        api_key=body.api_key,
        model=body.model,
        enable=0,
        user_id=user_id,
    )
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return LlmtokenResponse(
        id=token.id,
        base_url=token.base_url,
        api_key=token.api_key,
        model=token.model,
        enable=token.enable,
        user_id=token.user_id,
        created_at=token.created_at.isoformat() if token.created_at else None,
        updated_at=token.updated_at.isoformat() if token.updated_at else None,
    )


@router.put("/{token_id}")
async def update_token(
    token_id: int,
    body: LlmtokenUpdate,
    session: AsyncSession = Depends(get_session),
) -> LlmtokenResponse:
    token = await session.get(Llmtoken, token_id)
    if token is None or token.del_flag == 1:
        raise HTTPException(status_code=404, detail="Token not found")
    if body.base_url is not None:
        token.base_url = body.base_url
    if body.api_key is not None:
        token.api_key = body.api_key
    if body.model is not None:
        token.model = body.model
    if body.enable is not None:
        token.enable = body.enable
    await session.commit()
    await session.refresh(token)
    return LlmtokenResponse(
        id=token.id,
        base_url=token.base_url,
        api_key=token.api_key,
        model=token.model,
        enable=token.enable,
        user_id=token.user_id,
        created_at=token.created_at.isoformat() if token.created_at else None,
        updated_at=token.updated_at.isoformat() if token.updated_at else None,
    )


@router.delete("/{token_id}")
async def delete_token(
    token_id: int,
    session: AsyncSession = Depends(get_session),
):
    token = await session.get(Llmtoken, token_id)
    if token is None or token.del_flag == 1:
        raise HTTPException(status_code=404, detail="Token not found")
    token.del_flag = 1
    await session.commit()
    return {"ok": True}


@router.post("/{token_id}/test")
async def test_token(
    token_id: int,
    session: AsyncSession = Depends(get_session),
):
    token = await session.get(Llmtoken, token_id)
    if token is None or token.del_flag == 1:
        raise HTTPException(status_code=404, detail="Token not found")
    try:
        llm = ChatOpenAI(
            model=token.model,
            api_key=token.api_key,
            base_url=token.base_url,
            timeout=LLM_CALL_TIMEOUT,
            max_retries=0,
        )
        import asyncio
        from langchain_core.messages import HumanMessage

        resp = await asyncio.wait_for(
            llm.ainvoke([HumanMessage(content="回复OK")]),
            timeout=LLM_CALL_TIMEOUT,
        )
        return {"ok": True, "reply": (getattr(resp, "content", "") or "")[:200]}
    except Exception as e:
        logger.warning("LLM Token 测试失败 | token_id=%d | error=%s", token_id, e)
        raise HTTPException(status_code=400, detail=f"连接失败: {str(e)}")