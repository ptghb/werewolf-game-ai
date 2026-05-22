from __future__ import annotations

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

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserResponse
    token: str