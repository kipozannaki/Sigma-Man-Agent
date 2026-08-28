# -*- coding: utf-8 -*-
"""伦理护栏：硬编码违规词拦截器。

命中即中断推理流程，返回固定话术，并输出匿名警告日志（不落任何原文）。
"""

import logging

logger = logging.getLogger("guardrails")

#: 违规词表：任何涉及伤害、伪造、窃听的意图一律拒绝（可按监管要求扩充）
BLOCKED_WORDS: tuple[str, ...] = (
    "陷害", "下药", "伪造", "偷拍", "偷录", "跟踪", "上门堵",
    "净身出户", "让她毁容", "打残", "买凶", "报复社会", "自杀教程",
    "查开房", "黑客查", "定位追踪", "监听", "非法获取",
)

#: 命中后的固定回复（不解释、不展开）
GUARD_MESSAGE = "该问题超出情感决策范围，建议咨询专业法律人士。"


def is_blocked(text: str) -> bool:
    """检查输入是否命中违规词表；命中时记录匿名警告日志。"""
    hit = any(word in text for word in BLOCKED_WORDS)
    if hit:
        # 只记录长度与命中数量，绝不记录原文
        logger.warning("guardrails_hit length=%d", len(text))
    return hit
