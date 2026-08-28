# -*- coding: utf-8 -*-
"""七大男性情感困局枚举。

所有模块（路由分发、追问树加载、埋点统计）均通过导入此枚举
进行场景标识，保证场景 ID 全局唯一且不可拼错。
"""

from enum import Enum


class ScenarioEnum(str, Enum):
    """七大困局：值同时用作追问树文件名与埋点场景字段。"""

    FINANCE = "FINANCE"                # 财务围猎：彩礼 / 经济吸血 / 上交工资
    CHEATING = "CHEATING"              # 出轨疑云：暧昧 / 实锤 / 信任崩塌
    COLD_VIOLENCE = "COLD_VIOLENCE"    # 冷暴力：长期冷战 / 精神内耗
    FAMILY_ORIGIN = "FAMILY_ORIGIN"    # 原生家庭介入：丈母娘 / 对方父母越界
    REPRODUCTION = "REPRODUCTION"      # 生育博弈：生育分歧 / 育儿主导权
    LOW_INTIMACY = "LOW_INTIMACY"      # 亲密感缺失：无性 / 生理排斥
    REPUTATION = "REPUTATION"          # 社死危机：公开处刑 / 职场干扰

    @classmethod
    def values(cls) -> list[str]:
        """返回全部场景值，供路由器校验 LLM 分类输出是否合法。"""
        return [item.value for item in cls]

    @property
    def question_tree_file(self) -> str:
        """该场景对应的苏格拉底追问树 JSON 文件名。"""
        return f"{self.value.lower()}_tree.json"
