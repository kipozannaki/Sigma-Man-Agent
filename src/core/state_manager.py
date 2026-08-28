# -*- coding: utf-8 -*-
"""对话状态机：INIT → SCENARIO_MATCH → Q1..Q5 → CALCULATING → RESULT。

含回退机制：用户答非所问时回退到上一节点。
"""

from enum import Enum


class ChatState(str, Enum):
    """对话全生命周期状态。"""

    INIT = "INIT"                          # 等待用户首条输入
    SCENARIO_MATCH = "SCENARIO_MATCH"      # 场景分类中
    QUESTION_Q1 = "QUESTION_Q1"            # 追问第1层
    QUESTION_Q2 = "QUESTION_Q2"
    QUESTION_Q3 = "QUESTION_Q3"
    QUESTION_Q4 = "QUESTION_Q4"
    QUESTION_Q5 = "QUESTION_Q5"
    CALCULATING = "CALCULATING"            # 五维评分中
    RESULT = "RESULT"                      # 已输出红黄绿灯

    @property
    def depth(self) -> int:
        """追问层深度（非追问状态返回 0）。"""
        return int(self.value[-1]) if self.value.startswith("QUESTION_Q") else 0


#: 状态主线顺序（用于回退定位）
MAIN_LINE: list[ChatState] = [
    ChatState.INIT,
    ChatState.SCENARIO_MATCH,
    ChatState.QUESTION_Q1,
    ChatState.QUESTION_Q2,
    ChatState.QUESTION_Q3,
    ChatState.QUESTION_Q4,
    ChatState.QUESTION_Q5,
    ChatState.CALCULATING,
    ChatState.RESULT,
]


class StateManager:
    """单会话状态机：只允许沿主线前进一格，或回退一格。"""

    def __init__(self) -> None:
        self.state = ChatState.INIT
        self.answers: dict[int, str] = {}   # {追问深度: 用户回答}

    @property
    def depth(self) -> int:
        """当前追问层深度。"""
        return self.state.depth

    def advance(self) -> ChatState:
        """沿主线前进一格，返回新状态；到终点则原地不动。"""
        idx = MAIN_LINE.index(self.state)
        self.state = MAIN_LINE[min(idx + 1, len(MAIN_LINE) - 1)]
        return self.state

    def rollback(self) -> ChatState:
        """答非所问时回退到上一节点，返回回退后的状态。"""
        idx = MAIN_LINE.index(self.state)
        self.state = MAIN_LINE[max(idx - 1, 0)]
        return self.state

    def record_answer(self, depth: int, answer: str) -> None:
        """记录用户对某层追问的回答，供评分阶段汇总。"""
        self.answers[depth] = answer

    def is_finished(self) -> bool:
        """是否已到达终点状态。"""
        return self.state == ChatState.RESULT
