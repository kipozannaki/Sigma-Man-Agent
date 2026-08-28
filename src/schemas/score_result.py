# -*- coding: utf-8 -*-
"""评分结果数据模式：LLM 五维评分输出的强校验模型。"""

from pydantic import BaseModel, Field, field_validator

from src.schemas.scenario_enum import ScenarioEnum


class ScoreResult(BaseModel):
    """五维评分输出：任何字段缺失或越界即校验失败。"""

    finance: float = Field(ge=0, le=100)
    emotion: float = Field(ge=0, le=100)
    reproduction: float = Field(ge=0, le=100)
    reputation: float = Field(ge=0, le=100)
    legal: float = Field(ge=0, le=100)
    total_score: float = Field(ge=0, le=100)
    reasoning: str = Field(min_length=1)

    @field_validator("finance", "emotion", "reproduction", "reputation", "legal", "total_score")
    @classmethod
    def round_score(cls, v: float) -> float:
        """分数统一保留一位小数，避免 LLM 输出超长小数。"""
        return round(float(v), 1)


class ClassifyResult(BaseModel):
    """场景分类输出：scenario 必须是七大困局枚举之一。"""

    scenario: ScenarioEnum
    confidence: float = Field(ge=0.0, le=1.0)


class ChatRequest(BaseModel):
    """流式对话请求体。"""

    session_id: str = Field(min_length=6, max_length=64)
    message: str = Field(min_length=1, max_length=2000)
    weights: dict[str, float] | None = None  # 用户自定义五维权重（可选）
