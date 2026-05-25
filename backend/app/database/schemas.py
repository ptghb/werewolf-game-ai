from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=50)
    phone: str = Field(min_length=5, max_length=20)
    account: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    account: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    nickname: str
    phone: str
    account: str
    level: int
    vip: int = 0

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserResponse
    token: str


class LlmtokenCreate(BaseModel):
    base_url: str = Field(min_length=1, max_length=255)
    api_key: str = Field(min_length=1, max_length=512)
    model: str = Field(min_length=1, max_length=100)


class LlmtokenUpdate(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    enable: Optional[int] = None


class LlmtokenResponse(BaseModel):
    id: int
    base_url: str
    api_key: str
    model: str
    enable: int
    user_id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}