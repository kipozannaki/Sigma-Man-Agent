# -*- coding: utf-8 -*-
"""用户画像暂存：Redis + TTL，仅存特征值，严禁存姓名/手机号。

会话 ID 经加盐哈希脱敏后作为 Redis 键，防止原 ID 泄露用户身份。
"""

import hashlib
import json

import redis.asyncio as aioredis

from src.core.config import get_settings


def anonymize_session(session_id: str) -> str:
    """加盐哈希会话 ID，实现存储层脱敏。"""
    settings = get_settings()
    raw = f"{settings.encryption_salt}:{session_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


class ProfileCache:
    """会话画像缓存：状态机数据、已答追问、用户权重偏好。"""

    def __init__(self) -> None:
        settings = get_settings()
        self.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        self.ttl = settings.profile_ttl_seconds

    def _key(self, session_id: str) -> str:
        """构造脱敏后的 Redis 键。"""
        return f"profile:{anonymize_session(session_id)}"

    async def save_context(self, session_id: str, context: dict) -> None:
        """保存会话上下文并刷新 TTL。"""
        await self.redis.set(
            self._key(session_id),
            json.dumps(context, ensure_ascii=False),
            ex=self.ttl,
        )

    async def load_context(self, session_id: str) -> dict | None:
        """读取会话上下文；过期或不存在时返回 None。"""
        raw = await self.redis.get(self._key(session_id))
        return json.loads(raw) if raw else None

    async def clear(self, session_id: str) -> None:
        """会话结束或用户主动退出时清除画像。"""
        await self.redis.delete(self._key(session_id))
