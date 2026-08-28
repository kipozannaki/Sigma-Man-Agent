# -*- coding: utf-8 -*-
"""全局配置加载：唯一的环境变量读取入口（SSOT 原则）。

其他模块一律通过 `get_settings()` 获取配置，禁止散落各处的 os.getenv。
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

#: 项目根目录（config/ 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """环境变量映射模型，自动读取 config/.env。"""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / "config" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---------- LLM ----------
    llm_api_key: str = "sk-placeholder"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # ---------- 存储 ----------
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sigma_man"

    # ---------- 向量库 ----------
    pinecone_api_key: str = ""
    pinecone_env: str = "gcp-starter"
    chroma_persist_dir: str = "./data/vector_db"

    # ---------- 安全 ----------
    encryption_salt: str = "CHANGE_ME_TO_RANDOM_32_BYTES"
    profile_ttl_seconds: int = 1800


@lru_cache
def get_settings() -> Settings:
    """带缓存的单例读取，避免重复解析 .env 文件。"""
    return Settings()
