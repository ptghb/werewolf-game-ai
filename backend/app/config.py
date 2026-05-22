from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    api_key: str
    base_url: str
    model: str
    database_url: str
    jwt_secret: str


settings = Settings(
    api_key=os.getenv("SILICONFLOW_API_KEY", ""),
    base_url=os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"),
    model=os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
    database_url=os.getenv("DATABASE_URL", "mysql+aiomysql://root:password@localhost:3306/werewolf"),
    jwt_secret=os.getenv("JWT_SECRET", "change-me-in-production"),
)
