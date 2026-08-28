# -*- coding: utf-8 -*-
"""埋点日志器：匿名记录会话指标到 PostgreSQL analytics 表。

记录字段全部为特征值，不含任何用户身份信息。
"""

import logging
import time
from contextlib import asynccontextmanager

from sqlalchemy import BigInteger, Column, Float, Integer, String, Text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

logger = logging.getLogger("metrics")

Base = declarative_base()


class AnalyticsEvent(Base):
    """analytics 表结构：一次会话一条记录。"""

    __tablename__ = "analytics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scenario = Column(String(32), index=True)        # 场景类型（七困局枚举）
    verdict = Column(String(8), index=True)          # 最终评级 red/yellow/green
    total_score = Column(Float, nullable=True)       # 加权总分
    duration_seconds = Column(Integer, default=0)    # 会话停留时长
    drop_at_depth = Column(Integer, nullable=True)   # 中途流失节点（0-5）
    created_at = Column(BigInteger, default=lambda: int(time.time()), index=True)


class MetricsLogger:
    """异步埋点写入器：写入失败不影响主流程（只记日志）。"""

    def __init__(self, database_url: str) -> None:
        self.engine = create_async_engine(database_url, pool_pre_ping=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_table(self) -> None:
        """建表（幂等），应用启动时调用。"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def log_session(self, scenario: str, verdict: str, total_score: float | None,
                          duration_seconds: int, drop_at_depth: int | None) -> None:
        """写入一条会话埋点。"""
        event = AnalyticsEvent(
            scenario=scenario, verdict=verdict, total_score=total_score,
            duration_seconds=duration_seconds, drop_at_depth=drop_at_depth,
        )
        try:
            async with self.session_factory() as session:
                session.add(event)
                await session.commit()
        except Exception:
            # 埋点失败绝不影响咨询主链路
            logger.warning("metrics_write_failed scenario=%s", scenario)

    @asynccontextmanager
    async def lifespan(self):
        """FastAPI lifespan 钩子：启动建表，退出释放连接。"""
        await self.create_table()
        yield
        await self.engine.dispose()
