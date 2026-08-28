# -*- coding: utf-8 -*-
"""五维评分权重数据结构。

用户可为五个评估维度自定义关注权重（总和必须为 1.0），
评分引擎据此加权计算最终红/黄/绿灯结论。
"""

from pydantic import BaseModel, Field, field_validator, model_validator

#: 系统默认均衡权重（用户未配置时兜底）
DEFAULT_WEIGHTS: dict[str, float] = {
    "finance": 0.20,       # 财务维度
    "emotion": 0.25,       # 情感维度
    "reproduction": 0.15,  # 生育维度
    "reputation": 0.15,    # 名声维度
    "legal": 0.25,         # 法律维度
}


class DimensionWeights(BaseModel):
    """五维权重模型：任何一项非法或总和偏离 1.0 均直接拒绝。"""

    finance: float = Field(default=0.20, ge=0.0, le=1.0)
    emotion: float = Field(default=0.25, ge=0.0, le=1.0)
    reproduction: float = Field(default=0.15, ge=0.0, le=1.0)
    reputation: float = Field(default=0.15, ge=0.0, le=1.0)
    legal: float = Field(default=0.25, ge=0.0, le=1.0)

    #: 权重总和允许的浮点误差窗口
    TOLERANCE: float = 0.001

    @field_validator("finance", "emotion", "reproduction", "reputation", "legal")
    @classmethod
    def check_non_negative(cls, v: float) -> float:
        """单项权重必须非负且不超过 1（ge/le 已约束，这里防御 NaN）。"""
        if v != v:  # NaN 检测：NaN 不等于自身
            raise ValueError("权重不能为 NaN")
        return round(v, 4)

    @model_validator(mode="after")
    def check_sum_is_one(self) -> "DimensionWeights":
        """归一化校验：五项之和必须等于 1.0，否则抛出 ValidationError。"""
        total = self.finance + self.emotion + self.reproduction + self.reputation + self.legal
        if abs(total - 1.0) > self.TOLERANCE:
            raise ValueError(f"五维权重之和必须为 1.0，当前为 {total:.4f}")
        return self

    def to_dict(self) -> dict[str, float]:
        """导出为字典，供评分 CoT Prompt 注入用户权重因子。"""
        return self.model_dump()
